# ABOUTME: CLI starter for demo5 — submits a single PersonalAssistantWorkflow execution.
# Targets the orchestrator task queue; the orchestrator fans out via child workflow + Nexus.

import asyncio
import sys
import uuid
from datetime import timedelta

from agents import trace
from temporalio.client import Client
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
    StatelessMCPServerProvider,
)
from temporalio.envconfig import ClientConfig

from personal_assistant import PersonalAssistantWorkflow
from worker import (
    MCP_SERVER_NAME,
    ORCHESTRATOR_TASK_QUEUE,
    _f1_server_factory,
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

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What's the weather at the next F1 race?"
    )

    # Open a trace so the plugin's interceptor propagates trace context to
    # the orchestrator workflow, the weather child workflow, and (separately)
    # any spans the F1 expert produces. See demo3/4 README for details.
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
