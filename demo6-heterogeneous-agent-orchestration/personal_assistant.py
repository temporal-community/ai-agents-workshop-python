# ABOUTME: Personal assistant orchestrator — delegates to three specialists.
# Weather: child workflow. F1 expert: Nexus. Travel planner: directly an activity (no sub-workflow).

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.openai_agents.workflow import (
    activity_as_tool,
    nexus_operation_as_tool,
)

with workflow.unsafe.imports_passed_through():
    import annotated_types  # noqa: F401
    import pydantic_core  # noqa: F401
    import pydantic_core.core_schema  # noqa: F401

    from agents import Agent, Runner

    from child_workflow_tool import child_workflow_as_tool
    from f1_expert_agent import F1ExpertService
    from travel_planner_activity import ask_travel_planner
    from weather_agent import WeatherAgentWorkflow


SYSTEM_PROMPT = """
You are a helpful personal assistant. You have three specialist sub-agents
available as tools:

- ask_weather_agent: a weather forecasting specialist with access to
  geocoding and current-weather tools. Use it for any weather question.
- ask_f1_expert: a Formula 1 expert with access to F1 race schedules,
  results, driver and constructor standings, and circuit telemetry. Use
  it for any F1 question.
- ask_travel_planner: a travel planning specialist that can summarize
  destinations and look up country background (currency, languages,
  region, capital). Use it for "tell me about <place>" or
  "what should I know about visiting X" style questions.

For questions that span multiple domains (e.g. "what's the weather at
the next F1 race and what should I know about the destination?"), call
the relevant specialists and combine their answers.

When you have enough information, give the user a concise final answer
in plain text. Today's date is {date}.
"""


@workflow.defn
class PersonalAssistantWorkflow:
    @workflow.run
    async def run(self, question: str) -> str:
        today = workflow.now().strftime("%Y-%m-%d")

        weather_tool = child_workflow_as_tool(
            WeatherAgentWorkflow.run,
            name="ask_weather_agent",
            description=(
                "Delegate a weather-related question to the weather forecasting "
                "specialist. Pass the full question as plain English."
            ),
            task_queue="weather-agent-tq",
            execution_timeout=timedelta(minutes=5),
        )

        f1_tool = nexus_operation_as_tool(
            F1ExpertService.ask_f1_expert,
            service=F1ExpertService,
            endpoint="f1-expert-d6",
            schedule_to_close_timeout=timedelta(minutes=5),
        )
        # The contrib helper has no description hook (the Operation dataclass
        # doesn't carry one and the stub function it inspects has no __doc__).
        # Set the description directly on the FunctionTool so the LLM has a
        # real signal for when to choose this tool.
        f1_tool.description = (
            "Delegate Formula 1 questions to the F1 expert specialist. "
            "It can look up race schedules, results, driver and constructor "
            "standings, and circuit telemetry. Pass the full question as plain English."
        )

        # Travel planner is an external Strands agent; we wrap it in an
        # activity rather than a child workflow. No per-step Temporal
        # visibility — see the README's "Two integration depths" section.
        travel_tool = activity_as_tool(
            ask_travel_planner,
            start_to_close_timeout=timedelta(minutes=5),
        )

        agent = Agent(
            name="PersonalAssistant",
            instructions=SYSTEM_PROMPT.format(date=today),
            model="gpt-4o",
            tools=[weather_tool, f1_tool, travel_tool],
        )
        result = await Runner.run(agent, input=question)
        return result.final_output
