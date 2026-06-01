# ABOUTME: Weather specialist sub-agent — runs as a child workflow when invoked by the orchestrator.
# Has the four weather activities (IP, location, coordinates, weather) wrapped via activity_as_tool.

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.openai_agents.workflow import activity_as_tool

with workflow.unsafe.imports_passed_through():
    import annotated_types  # noqa: F401
    import pydantic_core  # noqa: F401
    import pydantic_core.core_schema  # noqa: F401

    from agents import Agent, Runner

    from tool_activities import (
        get_coordinates,
        get_ip_address,
        get_location_info,
        get_weather,
    )


SYSTEM_PROMPT = """
You are a weather forecasting specialist. Use the provided tools to look up
weather information for any location. Available tools cover the caller's IP
address, IP-based geolocation, city geocoding, and current weather forecasts.

Answer the question concisely as plain text. Today's date is {date}.
"""


@workflow.defn
class WeatherAgentWorkflow:
    @workflow.run
    async def run(self, question: str) -> str:
        today = workflow.now().strftime("%Y-%m-%d")
        agent = Agent(
            name="WeatherAgent",
            instructions=SYSTEM_PROMPT.format(date=today),
            model="gpt-4o",
            tools=[
                activity_as_tool(
                    get_ip_address, start_to_close_timeout=timedelta(seconds=30)
                ),
                activity_as_tool(
                    get_location_info, start_to_close_timeout=timedelta(seconds=30)
                ),
                activity_as_tool(
                    get_coordinates, start_to_close_timeout=timedelta(seconds=30)
                ),
                activity_as_tool(
                    get_weather, start_to_close_timeout=timedelta(seconds=30)
                ),
            ],
        )
        result = await Runner.run(agent, input=question)
        return result.final_output
