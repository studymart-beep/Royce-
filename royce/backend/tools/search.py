"""Web search tool abstraction."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from config import get_settings
from tools.registry import ToolDefinition, registry

logger = logging.getLogger("royce.tools.search")


async def _tavily_search(query: str, api_key: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": 5},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Tavily error {resp.status_code}")
        data = resp.json()
        results = []
        for r in data.get("results") or []:
            results.append(
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("content") or r.get("snippet"),
                }
            )
        return results


async def web_search_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    query = str(args.get("query", "")).strip()
    if not query:
        return {"error": "query is required"}
    settings = get_settings()
    if not settings.web_search_api_key:
        return {
            "error": "Web search is not configured. Set WEB_SEARCH_API_KEY on the server.",
            "query": query,
            "results": [],
        }
    try:
        if settings.web_search_provider == "tavily":
            results = await _tavily_search(query, settings.web_search_api_key)
        else:
            return {"error": f"Unknown search provider: {settings.web_search_provider}"}
        return {"query": query, "results": results}
    except Exception as e:
        logger.exception("web_search failed")
        return {"error": str(e), "query": query, "results": []}


registry.register(
    ToolDefinition(
        name="web_search",
        description="Search the web for current information. Use when the user asks about recent events, facts you may not know, or needs sources.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    ),
    web_search_handler,
)
