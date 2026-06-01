# ABOUTME: Temporal activities that also serve as OpenAI Agents SDK tools.
# The Agents SDK auto-generates tool schemas from these signatures and docstrings.

import json
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
        # Open-Meteo's geocoder is fussy about query format. When it can't
        # match the query it omits the `results` field entirely, returning
        # something like {"generationtime_ms": 1.2}. The LLM doesn't reliably
        # recognize that as a "no match" signal — it sees a successful-looking
        # JSON response and retries the same call, eating turns. Detect the
        # empty case explicitly and return an unambiguous error payload with
        # a hint to retry with a simpler query (e.g. just the city name
        # without state/country qualifiers).
        data = response.json()
        if not data.get("results"):
            return json.dumps({
                "error": "no_match",
                "query": city,
                "hint": (
                    f"No location matched '{city}'. Try a simpler form "
                    "(e.g. just the city name) or check the spelling."
                ),
            })
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
