# Demo 5 - Multi-agent orchestration

Three OpenAI Agents SDK agents wired together through Temporal: a **personal-assistant** orchestrator delegates to two specialists — a **weather forecaster** and an **F1 expert**. Each specialist runs in its own Temporal workflow execution. The orchestrator invokes one via a **child workflow** and the other via **Nexus**, so the demo shows both cross-workflow primitives side by side.

## Architecture

```
                               ┌──────────────────────────────────┐
                               │  PersonalAssistantWorkflow        │
                               │  (task queue: orchestrator-tq)    │
                               └─────────┬───────────────┬─────────┘
                                         │               │
                       child workflow    │               │   Nexus operation
                                         ▼               ▼
            ┌──────────────────────────────┐   ┌──────────────────────────────────┐
            │  WeatherAgentWorkflow         │   │  F1ExpertAgentWorkflow            │
            │  (task queue: weather-agent-  │   │  (task queue: f1-expert-agent-tq) │
            │   tq)                         │   │  via F1ExpertService.ask          │
            └────────────┬─────────────────┘   └────────────┬─────────────────────┘
                         │                                  │
              activity_as_tool                       stateless_mcp_server
                         │                                  │
            ┌────────────▼─────────────┐         ┌──────────▼──────────────┐
            │  4 weather activities    │         │  F1 MCP server (stdio)  │
            │  (httpx → public APIs)   │         │  → 8 F1 tools           │
            └──────────────────────────┘         └─────────────────────────┘
```

All three Workers run in a single Python process via `asyncio.gather(...)`. They poll three distinct task queues, so the routing in the Temporal UI is explicit. Splitting them across processes (or even hosts) would be a one-line change — nothing else cares.

## What's different from demo4

Demo4 was one workflow with one agent. Demo5 introduces **agent-as-workflow-as-tool**: each specialist is a real Temporal workflow execution, not an inline function. That gets you durability, retries, and independent visibility per sub-agent.

The orchestrator uses two different patterns to call its specialists:

- **Child workflow** for the weather agent — same namespace, same Temporal cluster, parent-child semantics. Trace context propagates from orchestrator into child via Temporal headers.
- **Nexus** for the F1 expert — designed for cross-namespace / cross-cluster calls. Even within a single namespace it gives you a clean operation-shaped boundary with typed I/O. Trace context does **not** propagate (current limitation in `temporalio.contrib.openai_agents`; see the README's "Known limitations" section).

## Tools

The orchestrator agent sees just two tools:

| Tool | Mechanism | Description |
|---|---|---|
| `ask_weather_agent` | child workflow | Delegate weather questions to the weather forecasting specialist |
| `ask_f1_expert` | Nexus operation | Delegate F1 questions to the F1 expert specialist |

Each specialist has its own internal toolkit (weather APIs / F1 MCP). The orchestrator only sees the high-level "ask the specialist" tool.

### Planned next additions to the F1 expert

These are user-approved, deferred from the initial implementation. Both are free, no signup, F1-relevant:

- **Wikipedia REST** (`https://en.wikipedia.org/api/rest_v1/page/summary/{title}`) — circuit history, driver bios, championship summaries.
- **REST Countries** (`https://restcountries.com/v3.1/name/{name}`) — country background for race-host locations.

Both would be added as `@activity.defn` activities and wired via `activity_as_tool(...)` on the F1 expert agent.

## Prerequisites

- **Python 3.10+**
- **uv** — `brew install uv` on macOS
- **Temporal CLI** — `brew install temporal` on macOS
- **OpenAI API key** — `export OPENAI_API_KEY=sk-...`
- **F1 MCP server** — at `~/Projects/Temporal/AI/MCP/f1-mcp-server/` (override with `F1_MCP_SERVER_HOME`). Same server demo3 and demo4 use.

## Running

### 1. Start the Temporal dev server

```bash
temporal server start-dev
```

### 2. Register the Nexus endpoint (one-time)

```bash
temporal operator nexus endpoint create \
    --name f1-expert \
    --target-namespace default \
    --target-task-queue f1-expert-agent-tq
```

The endpoint name (`f1-expert`) must match the `endpoint=` argument used in `personal_assistant.py`. Re-running the command after the endpoint already exists will fail harmlessly — feel free to ignore the error.

### 3. Set your OpenAI API key (both terminals)

```bash
export OPENAI_API_KEY=sk-...
```

### 4. Install dependencies

From `demo5-multi-agent/`:

```bash
uv sync
```

### 5. Start the worker

```bash
uv run python -m worker
```

Three Workers run concurrently in this one process, polling `weather-agent-tq`, `f1-expert-agent-tq`, and `orchestrator-tq`. Leave it running.

### 6. Start a workflow

In a second terminal (also from `demo5-multi-agent/`):

```bash
uv run python -m start_workflow "What's the weather at the next F1 race?"
```

### Example prompts

```bash
# Weather only — orchestrator → weather agent (child workflow)
uv run python -m start_workflow "What is the weather in Monaco?"

# F1 only — orchestrator → F1 expert (Nexus)
uv run python -m start_workflow "When is the next F1 race?"

# Both — orchestrator → F1 expert (Nexus) → weather agent (child workflow)
uv run python -m start_workflow "What's the weather at the next F1 race?"

# Compare F1 venues
uv run python -m start_workflow "Compare the typical weather at Monaco and Singapore Grand Prix dates"
```

### Observing the workflow

In the Temporal Web UI at [http://localhost:8233](http://localhost:8233) you'll see:

- The **orchestrator workflow** on `orchestrator-tq`. Its history shows `StartChildWorkflowExecution` → `ChildWorkflowExecutionCompleted` for the weather path, and `NexusOperationScheduled` → `NexusOperationStarted` → `NexusOperationCompleted` for the F1 path.
- A separate **weather child workflow** on `weather-agent-tq`, with the four weather activities visible in its own history.
- A separate **F1 expert workflow** on `f1-expert-agent-tq`, started by the Nexus operation handler. Its history shows the F1 MCP `f1-data-list-tools` and `f1-data-call-tool-v2` activities.

In the OpenAI trace dashboard at [https://platform.openai.com/traces](https://platform.openai.com/traces):

- The trace `PersonalAssistant` contains the orchestrator's reasoning plus the **weather agent's** spans nested under it (child workflow trace propagation works).
- The **F1 expert** appears as a *separate* trace, not nested under `PersonalAssistant` (see "Known limitations" below).

## Known limitations

- **Trace context across Nexus is not propagated** by the current `temporalio.contrib.openai_agents` interceptor (verified — `OpenAIAgentsContextPropagationInterceptor` has a `start_child_workflow` method but no Nexus equivalent). Effect: the F1 expert produces its own top-level trace in OpenAI's dashboard rather than nesting under the orchestrator's trace. Workflow history in Temporal still links them via the `NexusOperationScheduled` event, so it's just an OpenAI-trace-dashboard cosmetic gap. Captured as a planning open item.

## Production split

In a real deployment you'd run the three Workers as three separate processes (often on three separate hosts, owned by three teams). The single-process layout here is a workshop convenience — change nothing about the workflow code, change `worker.py` from one process running three Workers to three processes each running one Worker.
