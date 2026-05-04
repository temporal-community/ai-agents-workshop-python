# ABOUTME: Personal-assistant team's worker -- orchestrator + weather agent + travel planner activity.

import asyncio
import os
from datetime import timedelta

# Disable OpenAI Agents SDK trace export. No trace server is configured in
# the workshop environment and the warnings are confusing for participants.
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
)
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker

from personal_assistant import PersonalAssistantWorkflow
from tool_activities import (
    get_coordinates,
    get_ip_address,
    get_location_info,
    get_weather,
)
from travel_planner_activity import ask_travel_planner
from weather_agent import WeatherAgentWorkflow

WEATHER_TASK_QUEUE = "weather-agent-tq"
ORCHESTRATOR_TASK_QUEUE = "orchestrator-tq"


async def main() -> None:
    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        ),
    )

    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")
    client = await Client.connect(**config, plugins=[plugin])

    weather_worker = Worker(
        client,
        task_queue=WEATHER_TASK_QUEUE,
        workflows=[WeatherAgentWorkflow],
        activities=[
            get_ip_address,
            get_location_info,
            get_coordinates,
            get_weather,
        ],
    )

    orchestrator_worker = Worker(
        client,
        task_queue=ORCHESTRATOR_TASK_QUEUE,
        workflows=[PersonalAssistantWorkflow],
        activities=[ask_travel_planner],
    )

    print(
        f"PA worker started.\n"
        f"  - {WEATHER_TASK_QUEUE} (WeatherAgentWorkflow)\n"
        f"  - {ORCHESTRATOR_TASK_QUEUE} (PersonalAssistantWorkflow + ask_travel_planner [Strands])\n"
        f"Ready -- start the F1 worker, then run the starter."
    )

    await asyncio.gather(
        weather_worker.run(),
        orchestrator_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
