# ABOUTME: F1 expert team's worker -- F1ExpertAgentWorkflow + Nexus handler.

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

from f1_expert_agent import F1ExpertAgentWorkflow, F1ExpertServiceHandler

F1_EXPERT_TASK_QUEUE = "f1-expert-agent-tq"
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

    f1_expert_worker = Worker(
        client,
        task_queue=F1_EXPERT_TASK_QUEUE,
        workflows=[F1ExpertAgentWorkflow],
        nexus_service_handlers=[F1ExpertServiceHandler()],
    )

    print(
        f"F1 worker started.\n"
        f"  - {F1_EXPERT_TASK_QUEUE} (F1ExpertAgentWorkflow + Nexus handler)\n"
        f"  F1 MCP server: {F1_MCP_SERVER_HOME}"
    )

    await f1_expert_worker.run()


if __name__ == "__main__":
    asyncio.run(main())
