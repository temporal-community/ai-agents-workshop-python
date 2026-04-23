# ABOUTME: Workflow that combines weather activity-tools with an F1 MCP server.
# The agentic loop is driven by the Agents SDK; Temporal makes both tool paths durable.

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.openai_agents.workflow import (
    activity_as_tool,
    stateless_mcp_server,
)

with workflow.unsafe.imports_passed_through():
    # Pre-import pydantic internals so the sandbox snapshots them before the
    # first workflow task. Without this, the Agents SDK's pydantic models get
    # loaded lazily on first Agent(...) construction, and the sandbox logs
    # "Module X was imported after initial workflow load" warnings.
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
You are a helpful assistant. Use the provided tools to help accomplish the user's goal.
Always use tools when they would help answer the question accurately.
You have access to weather tools (geocoding, current weather) and Formula 1 race data tools (schedules, results, standings).
When you have enough information to fully answer, provide your final response as plain text.
Today's date is {date}.
"""


@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, question: str) -> str:
        # workflow.now() is deterministic under replay, unlike datetime.now().
        today = workflow.now().strftime("%Y-%m-%d")

        # Reference to the MCP server registered on the worker under this name.
        # Each listTools/callTool becomes a Temporal activity (durable, retryable).
        f1 = stateless_mcp_server(name="f1-data", cache_tools_list=True)

        agent = Agent(
            name="Agent",
            instructions=SYSTEM_PROMPT.format(date=today),
            model="gpt-4o",
            mcp_servers=[f1],
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
