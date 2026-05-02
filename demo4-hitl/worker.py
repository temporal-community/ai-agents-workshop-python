# ABOUTME: Worker for demo4 -- same structure as demo3 (weather + F1 MCP), new task queue.
# HITL state lives inside the workflow; no additional worker wiring needed.

import asyncio
import os
from datetime import timedelta

# Disable OpenAI Agents SDK trace export. No trace server is configured in
# the workshop environment and the warnings are confusing for participants.
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from agents.mcp import MCPServerStdio
from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
    StatelessMCPServerProvider,
)
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker

from tool_activities import (
    get_coordinates,
    get_ip_address,
    get_location_info,
    get_weather,
)
from tools_workflow import AgentWorkflow

TASK_QUEUE = "hitl-agent-python-task-queue"
MCP_SERVER_NAME = "f1-data"

F1_MCP_SERVER_HOME = os.environ.get(
    "F1_MCP_SERVER_HOME",
    "/root/f1-mcp-server",
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
        # FastF1 downloads session data on first call, which can take 30+ seconds.
        # The default 5s timeout is too short; use 120s to be safe.
        client_session_timeout_seconds=120,
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

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgentWorkflow],
        activities=[
            get_ip_address,
            get_location_info,
            get_coordinates,
            get_weather,
        ],
    )

    print(f"Worker started. Listening on task queue: {TASK_QUEUE}")
    print(f"F1 MCP server: {F1_MCP_SERVER_HOME}")
    print("Ready -- run the starter in the other terminal.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
