# ABOUTME: Personal-assistant team's worker — PersonalAssistantWorkflow + WeatherAgentWorkflow.
# Plugin: add_temporal_spans=True (default) so trace context propagates from starter into the
# orchestrator and on into the weather child workflow with full Temporal-layer visualization.

import asyncio
from datetime import timedelta

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
from weather_agent import WeatherAgentWorkflow

WEATHER_TASK_QUEUE = "weather-agent-tq"
ORCHESTRATOR_TASK_QUEUE = "orchestrator-tq"


async def main() -> None:
    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        ),
        # No mcp_server_providers — the F1 MCP server is owned by the F1 worker.
        # add_temporal_spans defaults to True; trace context flows in cleanly via
        # the starter's `with trace(...)` so the temporal:* spans render properly.
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
    )

    print(
        f"PA worker running:\n"
        f"  - {WEATHER_TASK_QUEUE} (WeatherAgentWorkflow)\n"
        f"  - {ORCHESTRATOR_TASK_QUEUE} (PersonalAssistantWorkflow)"
    )

    await asyncio.gather(
        weather_worker.run(),
        orchestrator_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
