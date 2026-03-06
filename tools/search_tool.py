from __future__ import annotations

from typing import Any

import httpx


class SearchTool:
    """
    Lightweight web search wrapper using DuckDuckGo instant answer API.
    Works without API keys.
    """

    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self._timeout = timeout_seconds

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            payload = response.json()

        results: list[dict[str, Any]] = []
        related = payload.get("RelatedTopics", []) or []
        for item in related:
            if "Text" in item and "FirstURL" in item:
                results.append({"title": item["Text"], "url": item["FirstURL"]})
            nested = item.get("Topics", [])
            for nested_item in nested:
                if "Text" in nested_item and "FirstURL" in nested_item:
                    results.append({"title": nested_item["Text"], "url": nested_item["FirstURL"]})
            if len(results) >= limit:
                break
        return results[:limit]
