# ABOUTME: Interactive starter for demo4 — polls for agent questions and signals user input back.
# Supports --workflow-id <id> to reconnect to an existing (waiting) workflow.

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

from tools_workflow import AgentWorkflow
from worker import MCP_SERVER_NAME, TASK_QUEUE, _f1_server_factory

POLL_INTERVAL_SECONDS = 2.0
DEFAULT_QUERY = "Should I bring rain gear to the F1 race?"


def _parse_args(argv: list[str]) -> tuple[str | None, str | None]:
    """Return (workflow_id, goal). Exactly one will be non-None."""
    if len(argv) >= 3 and argv[1] == "--workflow-id":
        return argv[2], None
    goal = argv[1] if len(argv) >= 2 else DEFAULT_QUERY
    return None, goal


async def _read_line_async(prompt: str) -> str:
    """Non-blocking stdin read so the result poller keeps running."""
    return await asyncio.to_thread(input, prompt)


async def _interact(handle) -> str:
    """Poll for pending questions, relay them to stdin, and signal responses back.

    Returns the workflow's final result string.
    """
    result_task = asyncio.create_task(handle.result())

    print("Agent is working...")
    while not result_task.done():
        try:
            if await handle.query(AgentWorkflow.is_input_needed):
                question = await handle.query(AgentWorkflow.get_pending_question)
                print()
                print(f"Agent asks: {question}")
                response = await _read_line_async("Your response: ")
                await handle.signal(AgentWorkflow.provide_user_input, response)
                print("Agent is working...")
        except Exception:
            # The workflow may not yet be ready for queries on its very first
            # task, or may have just completed between the done-check and the
            # query. Either way, wait for the next tick and try again —
            # result_task will fire if the workflow has actually finished.
            pass

        try:
            await asyncio.wait_for(asyncio.shield(result_task), timeout=POLL_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue

    return await result_task


async def main() -> None:
    workflow_id, goal = _parse_args(sys.argv)

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

    if workflow_id is not None:
        # Reconnect to an existing workflow (it may be waiting for input).
        print(f"Reconnecting to workflow: {workflow_id}")
        handle = client.get_workflow_handle_for(AgentWorkflow.run, workflow_id)
        result = await _interact(handle)
    else:
        # Start a new workflow. A trace context makes the Agents SDK
        # tracing pipeline happy and avoids "No active trace" noise.
        new_id = f"hitl-agent-{uuid.uuid4()}"
        print(f"Starting workflow {new_id} with goal: {goal}")
        with trace("AgentWorkflow"):
            handle = await client.start_workflow(
                AgentWorkflow.run,
                goal,
                id=new_id,
                task_queue=TASK_QUEUE,
            )
            result = await _interact(handle)

    print()
    print("=== Agent Result ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
