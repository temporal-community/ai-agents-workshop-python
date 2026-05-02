# ABOUTME: Worker process for demo2 -- registers the ToolsWorkflow and tool activities.
# Uses the OpenAIAgentsPlugin so the Agents SDK can run durably inside the workflow.

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

from tool_activities import (
    get_coordinates,
    get_ip_address,
    get_location_info,
    get_weather,
)
from tools_workflow import ToolsWorkflow

TASK_QUEUE = "openai-agents-python-task-queue"


async def main() -> None:
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        )
    )

    client = await Client.connect(**config, plugins=[plugin])

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ToolsWorkflow],
        activities=[
            get_ip_address,
            get_location_info,
            get_coordinates,
            get_weather,
        ],
    )

    print(f"Worker started. Listening on task queue: {TASK_QUEUE}")
    print("Ready -- run the starter in the other terminal.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
