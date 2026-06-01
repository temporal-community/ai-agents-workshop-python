# ABOUTME: CLI starter for demo6b — submits a single PersonalAssistantWorkflow execution.
# Targets the orchestrator task queue; the orchestrator fans out via child workflow (weather)
# + Nexus to a Python F1 expert + Nexus to a Java (Spring AI) travel planner.

import asyncio
import sys
import uuid
from datetime import timedelta

from agents import trace
from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
)
from temporalio.envconfig import ClientConfig

from personal_assistant import PersonalAssistantWorkflow
from worker_pa import ORCHESTRATOR_TASK_QUEUE


async def main() -> None:
    # Starter is client-only — no need for MCP providers (they're consumed only
    # when a Worker registers their activities; Workers live in the worker_*.py
    # processes). Keep the plugin minimal.
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
        else "What's the weather at the next F1 race?"
    )

    # Open a trace so the plugin's interceptor propagates trace context to the
    # orchestrator workflow, and from there into the weather child workflow.
    # The F1 expert lives behind a Nexus boundary that the contrib doesn't
    # currently propagate trace context across — see worker_f1.py and
    # docs/research/openai-agents-plugin-starter-trace-requirement.md.
    with trace("PersonalAssistant"):
        result = await client.execute_workflow(
            PersonalAssistantWorkflow.run,
            query,
            id=f"personal-assistant-{uuid.uuid4()}",
            task_queue=ORCHESTRATOR_TASK_QUEUE,
        )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
