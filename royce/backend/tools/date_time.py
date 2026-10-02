"""Date/time tool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from zoneinfo import ZoneInfo

from tools.registry import ToolDefinition, registry


async def date_time_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    tz_name = str(args.get("timezone") or "UTC")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
        tz_name = "UTC"
    now = datetime.now(tz)
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": tz_name,
        "unix": int(now.timestamp()),
    }


registry.register(
    ToolDefinition(
        name="date_time",
        description="Get the current date and time. Optionally pass an IANA timezone (e.g. Africa/Lagos).",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone name, default UTC",
                }
            },
        },
    ),
    date_time_handler,
)
