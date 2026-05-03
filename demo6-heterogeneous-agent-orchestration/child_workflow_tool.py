# ABOUTME: Helper that wraps a Temporal child workflow's run method as an OpenAI Agents SDK tool.
# Mirrors the shape of activity_as_tool / nexus_operation_as_tool — every invocation is a child workflow.

from datetime import timedelta
from typing import Callable

from agents import FunctionTool, function_tool
from temporalio import workflow


def child_workflow_as_tool(
    workflow_run_method: Callable,
    *,
    name: str,
    description: str,
    task_queue: str,
    execution_timeout: timedelta | None = None,
) -> FunctionTool:
    """Wrap a Temporal child workflow's run method as an OpenAI Agents SDK tool.

    The tool takes a single string `question` and returns the workflow's
    final string output. Each invocation becomes a durable Temporal child
    workflow execution, visible in the parent's history as
    StartChildWorkflowExecution / ChildWorkflowExecutionCompleted.

    Args:
        workflow_run_method: Reference to the child workflow's @workflow.run
            method, e.g. ``WeatherAgentWorkflow.run``.
        name: Tool name surfaced to the LLM.
        description: Tool description surfaced to the LLM.
        task_queue: Task queue the child workflow polls.
        execution_timeout: Optional execution timeout for the child workflow.
    """

    @function_tool(name_override=name, description_override=description)
    async def _tool(question: str) -> str:
        return await workflow.execute_child_workflow(
            workflow_run_method,
            question,
            id=f"{name}-{workflow.uuid4()}",
            task_queue=task_queue,
            execution_timeout=execution_timeout,
        )

    return _tool
