# ABOUTME: Worker for demo3 — registers weather activities plus the F1 MCP server provider.
# The plugin auto-registers MCP listTools/callTool activities from the provider.

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

from tool_activities import (
    get_coordinates,
    get_ip_address,
    get_location_info,
    get_weather,
)
from tools_workflow import AgentWorkflow

TASK_QUEUE = "f1-agent-python-task-queue"
MCP_SERVER_NAME = "f1-data"

F1_MCP_SERVER_HOME = os.environ.get(
    "F1_MCP_SERVER_HOME",
    os.path.expanduser("~/Projects/Temporal/AI/MCP/f1-mcp-server"),
)


def _f1_server_factory() -> MCPServerStdio:
    # The F1 server is Node.js but shells out to python3 for FastF1. Activating
    # its venv ensures the child python3 finds fastf1, pandas, numpy on PATH.
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
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
