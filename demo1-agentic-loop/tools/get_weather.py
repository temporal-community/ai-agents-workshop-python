# ABOUTME: Weather tool that looks up current conditions by latitude/longitude.
# Uses Open-Meteo's forecast API; returns raw JSON for the LLM to summarize.

from typing import Any
from pydantic import BaseModel, Field
from helpers import tool_helpers
import httpx


class GetWeatherRequest(BaseModel):
    latitude: float = Field(description="Latitude of the location")
    longitude: float = Field(description="Longitude of the location")


GET_WEATHER_TOOL_OAI: dict[str, Any] = tool_helpers.oai_responses_tool_from_model(
    "get_weather",
    "Get current weather for a location using latitude and longitude. Returns temperature in Fahrenheit, weather code, and wind speed.",
    GetWeatherRequest,
)


async def get_weather(req: GetWeatherRequest) -> str:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={req.latitude}&longitude={req.longitude}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
        "&temperature_unit=fahrenheit"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        return response.text
