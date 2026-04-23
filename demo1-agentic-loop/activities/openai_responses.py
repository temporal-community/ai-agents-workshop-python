# ABOUTME: Temporal activity that wraps the OpenAI Responses API for durable LLM calls.
# Client-side retries are disabled so Temporal owns the retry policy.

from dataclasses import dataclass
from typing import Any

import openai
from openai import AsyncOpenAI
from openai.types.responses import Response
from temporalio import activity
from temporalio.exceptions import ApplicationError


@dataclass
class OpenAIResponsesRequest:
    model: str
    instructions: str
    input: object
    tools: list[dict[str, Any]]


@activity.defn
async def create(request: OpenAIResponsesRequest) -> Response:
    # Retries are Temporal's job, not the client's.
    client = AsyncOpenAI(max_retries=0)

    try:
        return await client.responses.create(
            model=request.model,
            instructions=request.instructions,
            input=request.input,
            tools=request.tools,
            timeout=30,
        )
    except openai.AuthenticationError as e:
        # Bad API key → permanent; don't retry.
        raise ApplicationError(
            f"OpenAI authentication failed: {e}",
            type="AuthenticationError",
            non_retryable=True,
        )
    except openai.BadRequestError as e:
        # Malformed request (bad tool schema, bad model name, etc.) → permanent.
        raise ApplicationError(
            f"OpenAI rejected the request: {e}",
            type="BadRequestError",
            non_retryable=True,
        )
    finally:
        await client.close()
