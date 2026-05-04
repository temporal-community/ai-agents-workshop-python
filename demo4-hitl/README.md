# Demo 4 - Human in the Loop

Extends demo3 by adding the ability for the agent to ask the user questions mid-execution. The LLM decides when it needs clarification and uses an `ask_user` tool to pause the workflow, get input from the user, and continue.

## What's different from demo3

Demo3's agent runs to completion without any user interaction after the initial goal. Demo4 adds a human-in-the-loop pattern: the agent can pause, ask the user a question, wait for their response, and continue with that information.

### How it works

The HITL mechanism uses three Temporal primitives — an in-workflow tool, a signal, and two queries:

**1. The `ask_user` tool** is defined *inside* the workflow's `run()` method as an `@function_tool`-decorated async closure. It's **not** a Temporal activity. The OpenAI Agents SDK awaits `@function_tool`-decorated async functions in the caller's context, so this tool runs directly in the workflow's event loop. When the LLM decides it needs more information, it calls this tool with a question. The tool:
- Sets `self._question = "..."` and `self._input_needed = True`
- Blocks on `await workflow.wait_condition(lambda: not self._input_needed)` — durably suspending the workflow

**2. The signal** `provide_user_input` delivers the user's response. The handler sets `self._user_input` and flips `self._input_needed = False`, unblocking the `wait_condition` so the tool returns the answer and the agent loop continues.

**3. The queries** `is_input_needed` and `get_pending_question` let the starter poll the workflow to detect when input is required and what question to surface.

### What happens while waiting for the user

When `workflow.wait_condition()` suspends the workflow, **no worker resources are consumed**. The workflow task completes, the worker is free to handle other work, and the workflow state is held durably by the Temporal server. The worker could even restart — when the signal arrives, the server schedules a new workflow task, the workflow replays, and execution resumes exactly where it left off.

### The starter

The starter starts the workflow asynchronously, then enters a polling loop:

- Every 2 seconds, it queries the workflow to check if input is needed.
- If yes, it prints the agent's question, reads the user's response from stdin, and sends it as a signal.
- A background `asyncio` task awaits the workflow result; when it completes, the loop exits and prints the result.

It also supports reconnecting to a workflow that's already waiting:

```bash
uv run python -m start_workflow --workflow-id hitl-agent-<uuid>
```

### Tools

Same tools as demo3 (4 weather activities + 8 F1 MCP tools), **plus** one new in-workflow tool:

| Tool | Kind | Purpose |
|------|------|---------|
| `ask_user` | in-workflow `@function_tool` | Pause and ask the user a question |

## Prerequisites

- **Python 3.10+**
- **uv** — `brew install uv` (macOS) or see [uv docs](https://docs.astral.sh/uv/)
- **Temporal CLI** — `brew install temporal` (macOS) or see [Temporal CLI docs](https://docs.temporal.io/cli)
- **OpenAI API key** — set as `OPENAI_API_KEY` environment variable
- **F1 MCP server** — installed locally and reachable via `F1_MCP_SERVER_HOME`. See [demo 3's install instructions](../demo3-mcp/README.md#install-the-f1-mcp-server) for the one-time setup; the same install is reused here.

## Running

### 1. Start the Temporal dev server

```bash
temporal server start-dev
```

### 2. Set your OpenAI API key (both terminals)

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Install dependencies

From `demo4-hitl/`:

```bash
uv sync
```

### 4. Start the worker

```bash
uv run python -m worker
```

Polls the `hitl-agent-python-task-queue` task queue. Leave this running.

### 5. Start a workflow

In a second terminal (also from `demo4-hitl/`):

```bash
uv run python -m start_workflow "Should I bring rain gear to the F1 race?"
```

The agent will ask which race you mean, wait for your response, then look up the weather.

### Example prompts

```bash
# Ambiguous — agent will ask which race
uv run python -m start_workflow "Should I bring rain gear to the F1 race?"

# Ambiguous location
uv run python -m start_workflow "What's the weather in Portland?"

# Clear enough — agent may not need to ask
uv run python -m start_workflow "What is the weather at the Monaco Grand Prix this year?"

# Multi-step with clarification
uv run python -m start_workflow "Help me plan what to pack for the race"
```

### Reconnecting to a waiting workflow

If you close the starter terminal while the agent is waiting for input, the workflow keeps running on the server. Reconnect with:

```bash
uv run python -m start_workflow --workflow-id hitl-agent-<uuid>
```

Find the workflow ID in the Temporal UI at [http://localhost:8233](http://localhost:8233).

### Observing the workflow

In the Temporal UI, running workflows show:

- `InvokeModelActivity` — LLM calls.
- Weather activities (`get_coordinates`, `get_weather`, etc.) — the `@activity.defn` tools.
- `f1-data-list-tools` / `f1-data-call-tool-v2` — F1 MCP operations.
- Signal events (`provide_user_input`) when the user responds.
- While the workflow is paused on `wait_condition`, it shows as "Running" but consumes no worker resources.
