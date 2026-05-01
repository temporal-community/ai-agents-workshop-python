import asyncio

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker

from activities import openai_responses, tool_invoker
from workflows.agent import AgentWorkflow

TASK_QUEUE = "tool-invoking-agent-python-task-queue"


async def main():
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")
    client = await Client.connect(
        **config,
        data_converter=pydantic_data_converter,
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgentWorkflow],
        activities=[
            openai_responses.create,
            tool_invoker.dynamic_tool_activity,
        ],
    )

    print(f"Worker started. Listening on task queue: {TASK_QUEUE}")
    print("Ready — run the starter in the other terminal.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
