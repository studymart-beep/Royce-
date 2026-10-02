"""Weather tool using Open-Meteo (no API key required)."""

from __future__ import annotations

from typing import Any, Dict

import httpx

from tools.registry import ToolDefinition, registry


async def weather_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    location = str(args.get("location", "")).strip()
    if not location:
        return {"error": "location is required"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
        )
        if geo.status_code != 200:
            return {"error": "Geocoding failed"}
        data = geo.json()
        results = data.get("results") or []
        if not results:
            return {"error": f"Location not found: {location}"}
        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        name = place.get("name")
        country = place.get("country")
        w = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
            },
        )
        if w.status_code != 200:
            return {"error": "Weather API failed"}
        cur = (w.json().get("current_weather") or {})
        return {
            "location": f"{name}, {country}" if country else name,
            "temperature_c": cur.get("temperature"),
            "windspeed_kmh": cur.get("windspeed"),
            "weathercode": cur.get("weathercode"),
            "time": cur.get("time"),
        }


registry.register(
    ToolDefinition(
        name="weather",
        description="Get current weather for a city or location name.",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or place name"}
            },
            "required": ["location"],
        },
    ),
    weather_handler,
)
