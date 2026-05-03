# ABOUTME: Strands-built travel planning agent. Self-contained, no Temporal awareness.
# Pretend this is a third-party library; the personal-assistant team just imports it.

from urllib.parse import quote

import httpx
from strands import Agent, tool
from strands.models.openai import OpenAIModel


@tool
async def wikipedia_summary(topic: str) -> str:
    """Get a Wikipedia summary for a topic — useful for cities, countries, regions, attractions.

    Args:
        topic: The article title to look up (e.g. "Monaco", "Spa-Francorchamps", "Suzuka Circuit").
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}",
            timeout=5.0,
        )
        response.raise_for_status()
        return response.text


@tool
async def country_info(country: str) -> str:
    """Get country background information — currency, languages, region, capital, timezones.

    Args:
        country: Country name (e.g. "Monaco", "Italy", "Singapore", "Japan").
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://restcountries.com/v3.1/name/{quote(country)}",
            timeout=5.0,
        )
        response.raise_for_status()
        return response.text


SYSTEM_PROMPT = """
You are a travel planning specialist. Help users understand destinations:
their context (Wikipedia summary), country background (language, currency,
region), and high-level practical information.

If users are not asking about a specific destination, do not guess, instead 
ask for more specific information.

Use the provided tools as needed. Answer concisely as plain text.
"""


def build_agent() -> Agent:
    return Agent(
        model=OpenAIModel(model_id="gpt-4o"),
        tools=[wikipedia_summary, country_info],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,  # silence Strands' default stdout printing
    )


async def run(question: str) -> str:
    """Build a fresh agent and answer one question. Returns plain text."""
    agent = build_agent()
    result = await agent.invoke_async(question)
    return str(result)
