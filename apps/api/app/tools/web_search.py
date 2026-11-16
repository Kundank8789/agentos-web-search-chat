
from typing import Any

from tavily import AsyncTavilyClient

from app.config import settings
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """
    Real web search tool powered by Tavily.
    """

    name = "web_search"
    description = (
        "Search the internet for current information "
        "and return relevant sources."
    )

    def __init__(self) -> None:
        if not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is not configured.")

        self.client = AsyncTavilyClient(
            api_key=settings.tavily_api_key
        )

    async def execute(self, **kwargs: Any) -> dict:
        query = (
            kwargs.get("query")
            or kwargs.get("search_query")
            or ""
        ).strip()

        if not query:
            return {
                "success": False,
                "error": "A search query is required.",
                "results": [],
            }

        try:
            response = await self.client.search(
                query=query,
                search_depth="basic",
                max_results=5,
                include_answer=False,
                include_raw_content=False,
            )

            results = []

            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score", 0),
                })

            return {
                "success": True,
                "source": "tavily",
                "query": query,
                "results": results,
                "result_count": len(results),
            }

        except Exception:
            return {
                "success": False,
                "source": "tavily",
                "query": query,
                "error": "Web search failed. Please try again.",
                "results": [],
            }

