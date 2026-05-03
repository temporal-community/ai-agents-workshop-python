# ABOUTME: Single-process worker that runs three Temporal Workers (one per task queue).
# Weather + F1-expert + orchestrator agents all live in this process; each polls its own queue.

import asyncio
import os
from datetime import timedelta

from agents.mcp import MCPServerStdio
from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
    StatelessMCPServerProvider,
)
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker

from f1_expert_agent import F1ExpertAgentWorkflow, F1ExpertServiceHandler
from personal_assistant import PersonalAssistantWorkflow
from tool_activities import (
    get_coordinates,
    get_ip_address,
    get_location_info,
    get_weather,
)
from weather_agent import WeatherAgentWorkflow

WEATHER_TASK_QUEUE = "weather-agent-tq"
F1_EXPERT_TASK_QUEUE = "f1-expert-agent-tq"
ORCHESTRATOR_TASK_QUEUE = "orchestrator-tq"

MCP_SERVER_NAME = "f1-data"
NEXUS_ENDPOINT_NAME = "f1-expert"

F1_MCP_SERVER_HOME = os.environ.get(
    "F1_MCP_SERVER_HOME",
    os.path.expanduser("~/Projects/Temporal/AI/MCP/f1-mcp-server"),
)


def _f1_server_factory() -> MCPServerStdio:
    launch = (
        f"source {F1_MCP_SERVER_HOME}/.venv/bin/activate"
        f" && node {F1_MCP_SERVER_HOME}/build/index.js"
    )
    return MCPServerStdio(
        name=MCP_SERVER_NAME,
        params={
            "command": "bash",
            "args": ["-c", launch],
        },
        cache_tools_list=True,
    )


async def main() -> None:
    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        ),
        mcp_server_providers=[
            StatelessMCPServerProvider(
                name=MCP_SERVER_NAME,
                server_factory=_f1_server_factory,
            ),
        ],
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

    f1_expert_worker = Worker(
        client,
        task_queue=F1_EXPERT_TASK_QUEUE,
        workflows=[F1ExpertAgentWorkflow],
        nexus_service_handlers=[F1ExpertServiceHandler()],
    )

    orchestrator_worker = Worker(
        client,
        task_queue=ORCHESTRATOR_TASK_QUEUE,
        workflows=[PersonalAssistantWorkflow],
    )

    print(
        f"Workers running:\n"
        f"  - {WEATHER_TASK_QUEUE} (WeatherAgentWorkflow)\n"
        f"  - {F1_EXPERT_TASK_QUEUE} (F1ExpertAgentWorkflow + Nexus handler)\n"
        f"  - {ORCHESTRATOR_TASK_QUEUE} (PersonalAssistantWorkflow)"
    )

    await asyncio.gather(
        weather_worker.run(),
        f1_expert_worker.run(),
        orchestrator_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
