# ABOUTME: Location tools — machine IP lookup, IP-based geolocation, and city geocoding.
# Each returns raw upstream JSON so the LLM can pick out the fields it needs.

from typing import Any
from urllib.parse import quote
import httpx
from pydantic import BaseModel, Field
from helpers import tool_helpers


class GetLocationRequest(BaseModel):
    ipaddress: str = Field(description="An IP address")


class GetCoordinatesRequest(BaseModel):
    city: str = Field(description="The city name to look up")


GET_LOCATION_TOOL_OAI: dict[str, Any] = tool_helpers.oai_responses_tool_from_model(
    "get_location_info",
    "Get the location information for an IP address. This includes the city, state, country, latitude, and longitude.",
    GetLocationRequest,
)

GET_IP_ADDRESS_TOOL_OAI: dict[str, Any] = tool_helpers.oai_responses_tool_from_model(
    "get_ip_address",
    "Get the IP address of the current machine.",
    None,
)

GET_COORDINATES_TOOL_OAI: dict[str, Any] = tool_helpers.oai_responses_tool_from_model(
    "get_coordinates",
    "Get the latitude and longitude for a city name.",
    GetCoordinatesRequest,
)


async def get_ip_address() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://icanhazip.com", timeout=5.0)
        response.raise_for_status()
        return response.text.strip()


async def get_location_info(req: GetLocationRequest) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://ip-api.com/json/{req.ipaddress}", timeout=5.0
        )
        response.raise_for_status()
        return response.text


async def get_coordinates(req: GetCoordinatesRequest) -> str:
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote(req.city)}&count=1"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        return response.text
