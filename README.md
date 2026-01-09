---
title: Career AI Assistant
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
python_version: 3.12
pinned: false
license: apache-2.0
---

# Career AI Assistant

An AI-powered job assistant that helps users prepare for job interviews, write resumes, and improve communication skills.

## Features

- AI-powered career guidance
- Interview preparation assistance
- Resume writing help
- Communication skills improvement
- Token-based usage system
- API rate limiting

## Deployment on Hugging Face Spaces

This application can be deployed on Hugging Face Spaces using Docker.

### Prerequisites

- A Hugging Face account
- Your Google Gemini API key

### Steps to Deploy

1. Fork this repository to your GitHub account
2. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and create a new Space
3. Select "Docker" as the SDK
4. Enter your repository URL
5. Add the following environment variables in the Space settings:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `DEFAULT_CREDIT_TOKENS`: (Optional) Set the default token amount per user (default: 50000)
6. The Space will automatically build and deploy using the provided Dockerfile

### Environment Variables

- `GEMINI_API_KEY` (required): Your Google Gemini API key for AI functionality
- `DEFAULT_CREDIT_TOKENS` (optional): Default token amount per user (default: 50000)

### API Endpoints

- `GET /` - Health check endpoint
- `POST /api/chat` - Main chat endpoint for career assistance

### Usage

The application uses a token-based system to manage usage. Each user starts with a default number of tokens that get deducted as they use the service.

## Local Development

If you want to run the application locally:

1. Clone the repository
2. Install dependencies: `uv sync`
3. Set up environment variables in a `.env` file
4. Run the application: `uvicorn main:app --reload`

## Architecture

The application is built with:
- FastAPI for the web framework
- Google Gemini for AI capabilities
- Uvicorn as the ASGI server
- Docker for containerization

## License

Add your license information here.