# ABOUTME: Registry mapping LLM-visible tool names to their async handlers and OpenAI tool schemas.
# Agent code imports get_tools() / get_handler() and stays decoupled from specific tool implementations.

from typing import Any, Awaitable, Callable

from temporalio.exceptions import ApplicationError

from .get_location import (
    GET_COORDINATES_TOOL_OAI,
    GET_IP_ADDRESS_TOOL_OAI,
    GET_LOCATION_TOOL_OAI,
    get_coordinates,
    get_ip_address,
    get_location_info,
)
from .get_weather import GET_WEATHER_TOOL_OAI, get_weather

ToolHandler = Callable[..., Awaitable[Any]]


def get_handler(tool_name: str) -> ToolHandler:
    if tool_name == "get_ip_address":
        return get_ip_address
    if tool_name == "get_location_info":
        return get_location_info
    if tool_name == "get_coordinates":
        return get_coordinates
    if tool_name == "get_weather":
        return get_weather
    raise ApplicationError(
        f"Unknown tool name: {tool_name}",
        type="UnknownTool",
        non_retryable=True,
    )


def get_tools() -> list[dict[str, Any]]:
    return [
        GET_IP_ADDRESS_TOOL_OAI,
        GET_LOCATION_TOOL_OAI,
        GET_COORDINATES_TOOL_OAI,
        GET_WEATHER_TOOL_OAI,
    ]
