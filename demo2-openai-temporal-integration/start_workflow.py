# ABOUTME: CLI starter for demo2 -- submits a single ToolsWorkflow execution and prints the result.

import asyncio
import sys
import uuid
from datetime import timedelta

from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
)
from temporalio.envconfig import ClientConfig

from tools_workflow import ToolsWorkflow

TASK_QUEUE = "openai-agents-python-task-queue"


async def main() -> None:
    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        )
    )

    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")
    client = await Client.connect(**config, plugins=[plugin])

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What is the weather in Tokyo?"
    )

    result = await client.execute_workflow(
        ToolsWorkflow.run,
        query,
        id=f"openai-agents-demo-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
