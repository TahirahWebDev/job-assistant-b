import os
import re
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    AsyncOpenAI,
    RunConfig,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered
)


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career-ai")

app = FastAPI(title="Career AI Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        external_client = AsyncOpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        model = OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=external_client
        )

        logger.info("Gemini model initialized successfully.")
    except Exception as e:
        logger.error(f" Error initializing Gemini model: {e}")
        model = None
else:
    logger.warning(" GEMINI_API_KEY not found. Running in mock mode.")
    model = None

config = RunConfig(model=model, tracing_disabled=True)


CREDITS = {}
USER_NAMES = {}
DEFAULT_CREDIT_TOKENS = int(os.getenv("DEFAULT_CREDIT_TOKENS", "50000"))


def get_user_id(header_user_id: Optional[str]) -> str:
    return header_user_id or "anonymous"


def get_user_name(user_id: str, header_user_name: Optional[str]) -> str:
    if header_user_name:
        USER_NAMES[user_id] = header_user_name
    return USER_NAMES.get(user_id, "there")


def ensure_user_in_credits(user_id: str):
    if user_id not in CREDITS:
        CREDITS[user_id] = {
            "tokens_left": DEFAULT_CREDIT_TOKENS,
            "last_reset": datetime.utcnow()
        }


def deduct_tokens(user_id: str, tokens: int) -> bool:
    ensure_user_in_credits(user_id)
    if CREDITS[user_id]["tokens_left"] >= tokens:
        CREDITS[user_id]["tokens_left"] -= tokens
        return True
    return False


def format_response(text: str) -> str:
    """Format response text with newlines and markdown clarity."""
    text = re.sub(r'(?<=\d\.)\s+', ' ', text)
    text = re.sub(r'(\d+\.\s+)', r'\n\1', text)
    text = text.replace("\\n", "\n")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class ChatRequest(BaseModel):
    message: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 0.9


class ChatResponse(BaseModel):
    response: str
    tokens_used_estimate: Optional[int] = None
    tokens_remaining: Optional[int] = None


@input_guardrail
async def career_guardrail(ctx, agent: Agent, user_input: str | list) -> GuardrailFunctionOutput:
    text = user_input if isinstance(user_input, str) else " ".join(
        item["content"] for item in user_input
    )
    keywords = [
        "career", "job", "interview", "resume", "cv",
        "skills", "experience", "portfolio", "guidance",
        "advice", "apply", "interviewer", "recruiter", "position",
        "prepare", "mock interview", "question", "answer"
    ]
    if not any(kw in text.lower() for kw in keywords):
        return GuardrailFunctionOutput(output_info=None, tripwire_triggered=True)
    return GuardrailFunctionOutput(output_info=None, tripwire_triggered=False)


def create_career_agent():
    return Agent(
        name="Career Mentor Agent",
        instructions="""
You are an AI Career Mentor.

Your job:
- Help users prepare for job interviews, write resumes, and improve communication skills.
- Respond like a human mentor: friendly, structured, and supportive.
- Format responses in **Markdown**.
- Use **bold headings**, **lists**, and **steps** for clarity.
- Keep answers concise, clear, and professional.

Avoid unrelated, harmful, or non-career topics.
""",
        input_guardrails=[career_guardrail]
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request,
               x_user_id: Optional[str] = Header(None),
               x_user_name: Optional[str] = Header(None)):

    user_id = get_user_id(x_user_id)
    user_name = get_user_name(user_id, x_user_name)
    ensure_user_in_credits(user_id)

    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    greetings = ["hi", "hello", "hey", "salam", "assalam"]
    if any(text.lower().startswith(g) for g in greetings):
        return ChatResponse(
            response=f"👋 Hello {user_name}! I’m your AI Job Assistant. How can I help today?",
            tokens_used_estimate=0,
            tokens_remaining=CREDITS[user_id]["tokens_left"]
        )

    max_tokens = min(1024, req.max_tokens or 512)
    estimated_tokens = max(1, int(len(text) / 4)) + max_tokens

    if not deduct_tokens(user_id, estimated_tokens):
        raise HTTPException(status_code=402, detail="Insufficient tokens")

    if model is None:
        logger.warning(" Model not initialized, returning mock response.")
        return ChatResponse(
            response="Gemini API key missing — using mock response. Example: 'You can improve your resume by highlighting measurable achievements.'",
            tokens_used_estimate=0,
            tokens_remaining=CREDITS[user_id]["tokens_left"]
        )

    agent = create_career_agent()
    user_prompt = f"User question: {text}"

    try:
        result = await Runner.run(agent, user_prompt, run_config=config)
        reply_text = getattr(result, "final_output", str(result))
        formatted = format_response(reply_text)

    except InputGuardrailTripwireTriggered:
        return ChatResponse(
            response="Please keep your question related to careers, resumes, or interviews.",
            tokens_used_estimate=0,
            tokens_remaining=CREDITS[user_id]["tokens_left"]
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")

        CREDITS[user_id]["tokens_left"] += estimated_tokens
        return ChatResponse(
            response=f"Agent error: {str(e)}",
            tokens_used_estimate=0,
            tokens_remaining=CREDITS[user_id]["tokens_left"]
        )

    logger.info(f"Reply generated for {user_name}")
    return ChatResponse(
        response=formatted,
        tokens_used_estimate=estimated_tokens,
        tokens_remaining=CREDITS[user_id]["tokens_left"]
    )

@app.get("/")
def root():
    return {"message": "✅ AI Job Assistant Backend is running!"}
