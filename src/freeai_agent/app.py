from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import FreeAIAgent

app = FastAPI(title="FreeAI Agent", version="0.1.0")
agent = FreeAIAgent()


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation/session identifier")
    question: str


class ReviseRequest(BaseModel):
    session_id: str
    feedback: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    result = agent.answer(req.session_id, req.question)
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "sources": [s.__dict__ for s in result.sources],
        "context_used": [c.__dict__ for c in result.context_used],
        "transparency_notes": result.transparency_notes,
    }


@app.post("/revise")
def revise(req: ReviseRequest) -> dict[str, str]:
    revised = agent.revise_last_answer(req.session_id, req.feedback)
    return {"revised_answer": revised}
