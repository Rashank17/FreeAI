from __future__ import annotations

from .models import Source


class SearchClient:
    def __init__(self, max_results: int = 6) -> None:
        self.max_results = max_results

    def search(self, question: str) -> list[Source]:
        """Search via duckduckgo_search if installed, else return empty list."""
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except Exception:
            return []

        sources: list[Source] = []
        with DDGS() as ddgs:
            results = ddgs.text(question, max_results=self.max_results)
            for item in results:
                title = item.get("title") or "Untitled"
                url = item.get("href") or ""
                snippet = item.get("body") or ""
                if not url:
                    continue
                sources.append(Source(title=title, url=url, snippet=snippet))
        return sources
