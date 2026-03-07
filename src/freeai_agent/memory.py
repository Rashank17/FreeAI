from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import MemoryItem


class MemoryStore:
    def __init__(self, db_path: str = "memory.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS preferences (
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY(session_id, key)
                )
                """
            )

    def save_interaction(self, item: MemoryItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO interactions (session_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
                (item.session_id, item.question, item.answer, item.created_at),
            )

    def recent(self, session_id: str, limit: int = 8) -> list[MemoryItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, question, answer, created_at
                FROM interactions
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [MemoryItem(*row) for row in rows]

    def relevant(self, session_id: str, query: str, limit: int = 3) -> list[MemoryItem]:
        query_terms = set(query.lower().split())
        ranked: list[tuple[int, MemoryItem]] = []
        for item in self.recent(session_id, limit=20):
            text_terms = set((item.question + " " + item.answer).lower().split())
            score = len(query_terms & text_terms)
            ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for score, item in ranked if score > 0][:limit]

    def save_preference(self, session_id: str, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO preferences (session_id, key, value) VALUES (?, ?, ?)",
                (session_id, key, value),
            )

    def load_preferences(self, session_id: str) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM preferences WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        return {key: value for key, value in rows}
