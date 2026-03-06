from __future__ import annotations

from tools.search_tool import SearchTool


class ResearchAgent:
    def __init__(self) -> None:
        self.search_tool = SearchTool()

    async def run(self, query: str) -> dict[str, object]:
        results = await self.search_tool.search(query=query, limit=5)
        summary = "No results found."
        if results:
            top = results[0]
            summary = f"Top result: {top['title']} ({top['url']})"
        return {"query": query, "summary": summary, "results": results}
