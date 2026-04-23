# ABOUTME: Temporal activities that also serve as OpenAI Agents SDK tools.
# The Agents SDK auto-generates tool schemas from these signatures and docstrings.

from urllib.parse import quote

import httpx
from temporalio import activity


@activity.defn
async def get_ip_address() -> str:
    """Get the IP address of the current machine."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://icanhazip.com", timeout=5.0)
        response.raise_for_status()
        return response.text.strip()


@activity.defn
async def get_location_info(ipaddress: str) -> str:
    """Get the location information for an IP address. This includes the city, state, country, latitude, and longitude.

    Args:
        ipaddress: An IP address
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://ip-api.com/json/{ipaddress}", timeout=5.0
        )
        response.raise_for_status()
        return response.text


@activity.defn
async def get_coordinates(city: str) -> str:
    """Get the latitude and longitude for a city name.

    Args:
        city: The city name to look up
    """
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote(city)}&count=1"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        return response.text


@activity.defn
async def get_weather(latitude: float, longitude: float) -> str:
    """Get current weather for a location using latitude and longitude. Returns temperature in Fahrenheit, weather code, and wind speed.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
        "&temperature_unit=fahrenheit"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        return response.text
