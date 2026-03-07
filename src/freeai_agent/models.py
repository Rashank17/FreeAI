from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Source:
    title: str
    url: str
    snippet: str


@dataclass
class MemoryItem:
    session_id: str
    question: str
    answer: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentResponse:
    answer: str
    sources: list[Source]
    context_used: list[MemoryItem]
    transparency_notes: list[str]
    confidence: str
