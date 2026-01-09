"""
Agents module for the Career AI Assistant
"""
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from openai import AsyncOpenAI as OriginalAsyncOpenAI


class OpenAIChatCompletionsModel:
    def __init__(self, model: str, openai_client: "AsyncOpenAI"):
        self.model = model
        self.openai_client = openai_client


class AsyncOpenAI:
    def __init__(self, api_key: str, base_url: str):
        self.client = OriginalAsyncOpenAI(api_key=api_key, base_url=base_url)


@dataclass
class RunConfig:
    model: Optional[Any] = None
    tracing_disabled: bool = True


class InputGuardrailTripwireTriggered(Exception):
    pass


@dataclass
class GuardrailFunctionOutput:
    output_info: Optional[Any]
    tripwire_triggered: bool


def input_guardrail(func):
    """Decorator for input guardrails"""
    async def wrapper(ctx, agent, user_input):
        return await func(ctx, agent, user_input)
    return wrapper


class Agent:
    def __init__(self, name: str, instructions: str, input_guardrails: Optional[List] = None):
        self.name = name
        self.instructions = instructions
        self.input_guardrails = input_guardrails or []


@dataclass
class RunnerResult:
    final_output: str


class Runner:
    @staticmethod
    async def run(agent: Agent, user_prompt: str, run_config: RunConfig) -> RunnerResult:
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # If model is available, try to use it
        if run_config.model:
            try:
                # Attempt to generate response using the model
                messages = [
                    {"role": "system", "content": agent.instructions},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = await run_config.model.openai_client.client.chat.completions.create(
                    model=run_config.model.model,
                    messages=messages,
                    max_tokens=512,
                    temperature=0.7
                )
                
                return RunnerResult(final_output=response.choices[0].message.content)
            except Exception as e:
                # If API call fails, return a default response
                return RunnerResult(final_output=f"Response generated based on instructions: {user_prompt[:100]}...")
        else:
            # Mock response when no model is available
            mock_responses = [
                "Based on your question, I recommend focusing on highlighting your key achievements in your resume.",
                "For interview preparation, practice common questions and research the company thoroughly.",
                "Consider structuring your resume with clear sections: experience, skills, education, and achievements.",
                "Behavioral questions are common in interviews. Prepare using the STAR method (Situation, Task, Action, Result).",
                "Your portfolio should showcase your best work with clear explanations of your contributions."
            ]
            
            # Simple mock response generation based on keywords
            user_lower = user_prompt.lower()
            if "resume" in user_lower or "cv" in user_lower:
                return RunnerResult(final_output=mock_responses[0])
            elif "interview" in user_lower:
                return RunnerResult(final_output=mock_responses[1])
            elif "portfolio" in user_lower:
                return RunnerResult(final_output=mock_responses[4])
            else:
                return RunnerResult(final_output=mock_responses[2])