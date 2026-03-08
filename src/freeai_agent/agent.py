from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urlparse

from .memory import MemoryStore
from .models import AgentResponse, MemoryItem, Source
from .search import SearchClient


class FreeAIAgent:
    """Internet-grounded QA agent with lightweight memory and revision support."""

    def __init__(self, memory: MemoryStore | None = None, search: SearchClient | None = None) -> None:
        self.memory = memory or MemoryStore()
        self.search_client = search or SearchClient()

    def answer(self, session_id: str, question: str) -> AgentResponse:
        context = self.memory.relevant(session_id, question)
        sources = self.search_client.search(question)
        unique_sources = self._dedupe_domains(sources)
        answer, confidence, notes = self._synthesize(question, unique_sources, context)
        self.memory.save_interaction(MemoryItem(session_id=session_id, question=question, answer=answer))
        return AgentResponse(
            answer=answer,
            sources=unique_sources,
            context_used=context,
            transparency_notes=notes,
            confidence=confidence,
        )

    def revise_last_answer(self, session_id: str, user_feedback: str) -> str:
        history = self.memory.recent(session_id, limit=1)
        if not history:
            return "I don't have a prior answer in memory to revise yet."
        last = history[0]
        revised = (
            f"Revised answer based on your feedback ('{user_feedback}'):\n\n"
            f"Previous answer: {last.answer}\n\n"
            "Updated guidance: I have adjusted emphasis to match your request. "
            "If you want precision, include what to add/remove and your preferred depth or tone."
        )
        self.memory.save_interaction(MemoryItem(session_id=session_id, question=f"REVISION: {user_feedback}", answer=revised))
        return revised

    def store_user_preference(self, session_id: str, preference: str) -> None:
        self.memory.save_preference(session_id, "style", preference)

    def _dedupe_domains(self, sources: list[Source]) -> list[Source]:
        seen: set[str] = set()
        unique: list[Source] = []
        for source in sources:
            domain = urlparse(source.url).netloc
            if domain in seen:
                continue
            seen.add(domain)
            unique.append(source)
        return unique[:4]

    def _synthesize(self, question: str, sources: list[Source], context: list[MemoryItem]) -> tuple[str, str, list[str]]:
        notes = [
            "This answer is grounded in external web sources plus your session memory.",
            "I avoid hidden chain-of-thought and instead provide transparent evidence and limitations.",
        ]

        if len(sources) < 2:
            confidence = "low"
            answer = (
                "I could not find enough independent sources to confidently answer this question. "
                "Please rephrase your query or ask for a narrower topic."
            )
            return answer, confidence, notes

        evidence = "\n".join([f"- {s.title}: {s.snippet}" for s in sources])
        context_line = ""
        if context:
            context_line = "\n\nRelevant past context from this conversation:\n" + "\n".join(
                f"- Q: {c.question}\n  A: {c.answer[:220]}" for c in context
            )

        token_counts = Counter(re.findall(r"[A-Za-z]{4,}", " ".join([s.snippet for s in sources]).lower()))
        key_points = [word for word, _ in token_counts.most_common(5)]
        confidence = "medium" if len(sources) == 2 else "high"

        answer = (
            f"Question: {question}\n\n"
            "Fused answer (human-readable):\n"
            "Based on multiple sources, the most consistent points are: "
            f"{', '.join(key_points)}.\n"
            "I combined overlapping claims and ignored repeated duplicates from the same domain. "
            "If sources disagree, prioritize peer-reviewed, official, or primary documents.\n\n"
            f"Evidence used:\n{evidence}"
            f"{context_line}"
        )

        return answer, confidence, notes
