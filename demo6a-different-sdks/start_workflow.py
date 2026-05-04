# ABOUTME: CLI starter for demo6 -- submits a single PersonalAssistantWorkflow execution.

import asyncio
import os
import sys
import uuid
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

from personal_assistant import PersonalAssistantWorkflow
from worker_pa import ORCHESTRATOR_TASK_QUEUE


async def main() -> None:
    plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=60),
        ),
    )

    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")
    client = await Client.connect(**config, plugins=[plugin])

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "I'm going to the next F1 race -- what's the weather, and what should I know about the destination?"
    )

    result = await client.execute_workflow(
        PersonalAssistantWorkflow.run,
        query,
        id=f"personal-assistant-{uuid.uuid4()}",
        task_queue=ORCHESTRATOR_TASK_QUEUE,
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
