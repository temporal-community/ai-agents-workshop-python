# ABOUTME: CLI starter for demo3 -- submits a single AgentWorkflow execution and prints the result.

import asyncio
import sys
import uuid
from datetime import timedelta

from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
    StatelessMCPServerProvider,
)
from temporalio.envconfig import ClientConfig

from tools_workflow import AgentWorkflow
from worker import MCP_SERVER_NAME, TASK_QUEUE, _f1_server_factory


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

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "When is the next F1 race and what will the weather be there?"
    )

    result = await client.execute_workflow(
        AgentWorkflow.run,
        query,
        id=f"f1-agent-demo-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
