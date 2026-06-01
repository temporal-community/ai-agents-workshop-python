# ABOUTME: Personal assistant orchestrator — delegates to three specialists.
# Weather: child workflow. F1 expert: Python Nexus. Travel planner: Java (Spring AI) via Nexus.

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.contrib.openai_agents.workflow import nexus_operation_as_tool

with workflow.unsafe.imports_passed_through():
    import annotated_types  # noqa: F401
    import pydantic_core  # noqa: F401
    import pydantic_core.core_schema  # noqa: F401

    from agents import Agent, Runner

    from child_workflow_tool import child_workflow_as_tool
    from f1_expert_agent import F1ExpertService
    from travel_planner_service import TravelPlannerService
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

        # Travel planner is a Java + Spring AI agent, reached over the same
        # Nexus mechanism as the F1 expert — the boundary is language-agnostic.
        # Its handler runs on a Java worker; from here it's just another tool.
        travel_tool = nexus_operation_as_tool(
            TravelPlannerService.ask_travel_planner,
            service=TravelPlannerService,
            endpoint="travel-planner",
            schedule_to_close_timeout=timedelta(minutes=5),
        )
        # Same description-hook gap as the F1 tool above — set it explicitly.
        travel_tool.description = (
            "Delegate travel-planning questions to the travel planner specialist. "
            "It can summarize destinations and look up country background "
            "(currency, languages, region, capital). Pass the full question as plain English."
        )

        agent = Agent(
            name="PersonalAssistant",
            instructions=SYSTEM_PROMPT.format(date=today),
            model="gpt-4o",
            tools=[weather_tool, f1_tool, travel_tool],
        )
        result = await Runner.run(agent, input=question)
        return result.final_output
