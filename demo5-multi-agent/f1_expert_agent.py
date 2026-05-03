# ABOUTME: F1 expert sub-agent — runs as a Nexus-invoked workflow, has the F1 MCP tools.
# Defines the Nexus service interface, the workflow, and the service handler that bridges them.

from __future__ import annotations

import uuid
from datetime import timedelta

import nexusrpc
from nexusrpc.handler import service_handler
from pydantic import BaseModel
from temporalio import nexus, workflow
from temporalio.contrib.openai_agents.workflow import stateless_mcp_server


# Nexus operation I/O — typed Pydantic models so nexus_operation_as_tool can
# derive a JSON schema for the LLM tool description.
class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


@nexusrpc.service
class F1ExpertService:
    # Operation attribute name doubles as the operation name. Naming this
    # ask_f1_expert (rather than bare "ask") makes the LLM-facing tool name
    # meaningful — the contrib helper derives the tool name from the operation
    # name verbatim.
    ask_f1_expert: nexusrpc.Operation[AskRequest, AskResponse]


with workflow.unsafe.imports_passed_through():
    import annotated_types  # noqa: F401
    import pydantic_core  # noqa: F401
    import pydantic_core.core_schema  # noqa: F401

    from agents import Agent, Runner


SYSTEM_PROMPT = """
You are a Formula 1 expert. Use the provided F1 data tools to answer questions
about race schedules, results, drivers, championships, telemetry, and circuits.

Answer concisely as plain text. Today's date is {date}.
"""


@workflow.defn
class F1ExpertAgentWorkflow:
    @workflow.run
    async def run(self, request: AskRequest) -> AskResponse:
        today = workflow.now().strftime("%Y-%m-%d")
        f1 = stateless_mcp_server(name="f1-data", cache_tools_list=True)
        agent = Agent(
            name="F1Expert",
            instructions=SYSTEM_PROMPT.format(date=today),
            model="gpt-4o",
            mcp_servers=[f1],
        )
        result = await Runner.run(agent, input=request.question)
        return AskResponse(answer=result.final_output)


@service_handler(service=F1ExpertService)
class F1ExpertServiceHandler:
    @nexus.workflow_run_operation
    async def ask_f1_expert(
        self,
        ctx: nexus.WorkflowRunOperationContext,
        request: AskRequest,
    ) -> nexus.WorkflowHandle[AskResponse]:
        # Plain uuid.uuid4 is fine here — the handler runs outside a workflow,
        # so workflow.uuid4() does not apply.
        return await ctx.start_workflow(
            F1ExpertAgentWorkflow.run,
            request,
            id=f"f1-expert-{uuid.uuid4()}",
        )
