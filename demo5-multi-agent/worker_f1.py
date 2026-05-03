# ABOUTME: F1 expert team's worker — F1ExpertAgentWorkflow + Nexus handler.
# Plugin: add_temporal_spans=False because the orchestrator's Nexus call doesn't propagate
# trace context (current contrib gap). Skipping temporal:* spans here avoids creating spans
# with parent_id="no-op" that the OpenAI tracing backend rejects (HTTP 400, dropped batches).

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

F1_EXPERT_TASK_QUEUE = "f1-expert-agent-tq"
MCP_SERVER_NAME = "f1-data"

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
        # Trace context doesn't propagate through Nexus to this worker, so the
        # workflow-inbound interceptor would create temporal:* spans with no
        # active trace, leaking parent_id="no-op" into export batches. Disable.
        # The F1 expert will appear as its own top-level trace in the OpenAI
        # dashboard until the contrib gains Nexus trace propagation.
        add_temporal_spans=False,
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
        f"F1 worker running:\n"
        f"  - {F1_EXPERT_TASK_QUEUE} (F1ExpertAgentWorkflow + Nexus handler)\n"
        f"  - plugin: add_temporal_spans=False (Nexus trace gap workaround)"
    )

    await f1_expert_worker.run()


if __name__ == "__main__":
    asyncio.run(main())
