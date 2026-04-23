# Demo 2 - OpenAI Agents SDK + Temporal Integration

The same agentic loop as demo1, reimplemented using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) and Temporal's `temporalio.contrib.openai_agents` integration. The integration makes the Agents SDK's built-in tool calling loop durable by routing LLM calls and tool executions through Temporal activities transparently.

## What's different from demo1

In demo1, we manually built the agentic loop: an explicit `while True` loop in the workflow that calls an LLM activity, checks for tool calls, dispatches them via a dynamic activity, and repeats. We also hand-wrote tool schemas using Pydantic models and OpenAI's internal `to_strict_json_schema` helper.

In demo2, the OpenAI Agents SDK handles all of that. The workflow's `run` method is one `Runner.run(...)` call:

```python
result = await Runner.run(agent, input=question)
return result.final_output
```

The SDK's `Runner` drives the tool calling loop. Under the hood, the `OpenAIAgentsPlugin` configures Temporal so that each LLM call runs as an activity and each tool execution runs as a separate Temporal activity. The developer writes standard Agents-SDK code; Temporal durability is automatic.

## Architecture

- **`OpenAIAgentsPlugin`** — A Temporal client/worker plugin that installs the Agents SDK runtime inside workflows. It registers a model-execution activity, sets interceptors, and installs the Pydantic data converter for type-safe serialization.
- **`activity_as_tool(...)`** — Wraps a `@activity.defn` function as an Agents SDK tool. The tool schema (name, description, JSON-schema parameters) is derived from the function's signature and docstring; calls made by the agent are dispatched through `workflow.execute_activity` with the timeouts you specify.
- **`tool_activities.py`** — A single module with all four tool activities. Each is decorated with `@activity.defn` and has a docstring whose first line becomes the tool description the LLM sees.
- **`OpenAIAgentsPlugin` on the client** — Both the worker and the starter pass the plugin when connecting, because the plugin also configures the client's data converter and task-queue expectations.

### Trade-off: tool coupling

In demo1, the `tools/` directory contains plain Python functions plus lightweight Pydantic request models — no Temporal imports. The `dynamic_tool_activity` bridges them to Temporal, keeping tool logic decoupled from infrastructure.

In demo2, the integration requires tools to be Temporal activities (`@activity.defn`). The `activity_as_tool` helper only accepts activity functions. This means the tools module now contains Temporal-specific code. You get a simpler workflow, but tools are no longer portable outside of Temporal.

### Tools

Same tools as demo1:

| Tool | API | Purpose |
|------|-----|---------|
| `get_ip_address` | icanhazip.com | Get the caller's public IP address |
| `get_location_info` | ip-api.com | Get city, country, lat/lon for an IP address |
| `get_coordinates` | Open-Meteo Geocoding | Get lat/lon for a city name |
| `get_weather` | Open-Meteo Forecast | Get current temperature, weather code, and wind speed |

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

From `demo2-openai-temporal-integration/`:

```bash
uv sync
```

### 4. Start the worker

```bash
uv run python -m worker
```

The worker connects with the `OpenAIAgentsPlugin`, registers `ToolsWorkflow` and the four tool activities, and polls the `openai-agents-python-task-queue` task queue. Leave this running.

### 5. Start a workflow

In a second terminal (also from `demo2-openai-temporal-integration/`):

```bash
uv run python -m start_workflow "What is the weather in Barcelona?"
```

### Example prompts

```bash
# Weather by city name (uses get_coordinates -> get_weather)
uv run python -m start_workflow "What is the weather in Tokyo?"

# Weather at current location (uses get_ip_address -> get_location_info -> get_weather)
uv run python -m start_workflow "What is the weather where I am?"

# Multi-city comparison
uv run python -m start_workflow "Compare the weather in London and Sydney right now"
```

### Observing the workflow

View running workflows in the Temporal Web UI at [http://localhost:8233](http://localhost:8233). Each LLM call and tool execution appears as a separate activity in the workflow history, just like demo1.
