# Demo 1 - Agentic Loop

An agentic loop implemented as a Temporal workflow, using the OpenAI Responses API directly. The agent calls an LLM with a set of tools and loops until it has enough information to answer the user's goal.

## Architecture

The agent runs as a Temporal workflow that orchestrates two types of activities:

- **LLM Activity** (`activities/openai_responses.py`) - Calls OpenAI via the `AsyncOpenAI` client's `responses.create()` method. Receives the conversation history, sends it to the model along with tool schemas, and returns the model's response (either a text answer or a tool call).
- **Tool Activities** (`activities/tool_invoker.py`) - A single *dynamic* activity that executes whatever tool the LLM chose, by looking up the handler in a registry. Each tool makes an external HTTP call:

| Tool | API | Purpose |
|------|-----|---------|
| `get_ip_address` | icanhazip.com | Get the caller's public IP address |
| `get_location_info` | ip-api.com | Get city, country, lat/lon for an IP address |
| `get_coordinates` | Open-Meteo Geocoding | Get lat/lon for a city name |
| `get_weather` | Open-Meteo Forecast | Get current temperature, weather code, and wind speed |

Tools are dispatched via Temporal's dynamic activity mechanism — the workflow itself knows nothing about specific tools. It simply forwards the tool name and arguments chosen by the LLM to the generic `dynamic_tool_activity`, which looks up the handler in the registry in `tools/__init__.py`.

The workflow loop:
1. Sends the conversation (system prompt + user goal + any prior tool results) to the LLM activity
2. If the LLM returns a tool call, dispatches it to the dynamic tool activity and adds the result to the conversation
3. If the LLM returns a text response, the agent is done

Temporal provides durable execution — if the worker crashes mid-loop, the workflow replays from history and resumes where it left off without re-executing completed activities.

## Prerequisites

- **Python 3.10+**
- **uv** — `brew install uv` (macOS) or see [uv docs](https://docs.astral.sh/uv/)
- **Temporal CLI** — `brew install temporal` (macOS) or see [Temporal CLI docs](https://docs.temporal.io/cli)
- **OpenAI API key** — set as `OPENAI_API_KEY` environment variable

## Running

### 1. Start the Temporal dev server

```bash
temporal server start-dev
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Install dependencies

From `demo1-agentic-loop/`:

```bash
uv sync
```

### 4. Start the worker

```bash
uv run python -m worker
```

The worker registers the workflow and activities with Temporal and begins polling the `tool-invoking-agent-python-task-queue` task queue. Leave this running.

### 5. Start a workflow

In a second terminal (also from `demo1-agentic-loop/`):

```bash
uv run python -m start_workflow "What is the weather in Barcelona?"
```

The starter creates a Temporal workflow, waits for the result, prints it, and exits.

### Example prompts

```bash
# Weather by city name (uses get_coordinates -> get_weather)
uv run python -m start_workflow "What is the weather in Tokyo?"

# Weather at current location (uses get_ip_address -> get_location_info -> get_weather)
uv run python -m start_workflow "What is the weather where I am?"

# Multi-city comparison
uv run python -m start_workflow "Compare the weather in London and Sydney right now"
```

## Adding or swapping tools

Tools are fully decoupled from the agent workflow and activity infrastructure. Each tool lives in `tools/` and is exposed through two pieces:

- an **OpenAI tool schema** — JSON describing the function name, description, and parameters (generated from a Pydantic model via the `oai_responses_tool_from_model` helper)
- an **async handler** — the Python function that actually runs

Both are wired up in `tools/__init__.py`.

**To add a new tool**, create a module in `tools/`:

```python
# tools/my_tool.py
from typing import Any
from pydantic import BaseModel, Field
from helpers import tool_helpers


class MyToolRequest(BaseModel):
    input: str = Field(description="The input")


MY_TOOL_OAI: dict[str, Any] = tool_helpers.oai_responses_tool_from_model(
    "my_tool",
    "Do something useful.",
    MyToolRequest,
)


async def my_tool(req: MyToolRequest) -> str:
    ...  # implementation
```

Then register it in `tools/__init__.py` by adding imports, a branch in `get_handler`, and an entry in `get_tools`:

```python
from .my_tool import MY_TOOL_OAI, my_tool

def get_handler(tool_name: str) -> ToolHandler:
    ...
    if tool_name == "my_tool":
        return my_tool
    ...

def get_tools() -> list[dict[str, Any]]:
    return [..., MY_TOOL_OAI]
```

Nothing else changes — the workflow, dynamic activity, and LLM activity are all tool-agnostic.

> [!NOTE]
> The helper that generates the tool schema uses `openai.lib._pydantic.to_strict_json_schema`, an internal OpenAI API that may change. There is currently no public equivalent for producing strict Responses-API tool schemas from a Pydantic model.

### Observing the workflow

While a workflow is running, you can view it in the Temporal Web UI at [http://localhost:8233](http://localhost:8233). You'll see each LLM call and tool execution as separate activity entries in the workflow history.
