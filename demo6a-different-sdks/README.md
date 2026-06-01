# Demo 6a - Heterogeneous agent orchestration: different SDKs

Heterogeneity has more than one axis. This is **axis 1 — different agent frameworks**, same language. (See [demo 6b](../demo6b-different-languages/) for **axis 2 — a different language**, where the travel planner is reimplemented in Java with Spring AI.)

Extends [demo 5](../demo5-multi-agent/) by adding a third specialist — a **travel planner** built with the [Strands Agents SDK](https://strandsagents.com/) — alongside demo5's OpenAI Agents SDK weather forecaster and F1 expert. The orchestrator now drives **two different agent frameworks** (both Python) through the same Temporal primitives, demonstrating that the orchestration is framework-agnostic.

The pedagogical contrast: the OpenAI agents in demos 2–5 use `temporalio.contrib.openai_agents` and get **per-step durability** — every LLM call and every tool call is its own Temporal activity. The Strands agent has no Temporal contrib, so we wrap the entire agent loop in a single activity. That gives **coarse-grained durability** (the activity retries on worker failure) without per-step history. Demo 6 puts both styles in the same workflow so you can see the trade-off.

## Architecture

```
                            ┌─────────────────────────────────────┐
                            │  PersonalAssistantWorkflow           │
                            │  (task queue: orchestrator-tq)       │
                            └────┬─────────────┬──────────────┬────┘
                                 │             │              │
                  child workflow │     Nexus   │   activity (no sub-workflow)
                                 ▼             ▼              ▼
       ┌────────────────────────────┐ ┌──────────────────┐ ┌─────────────────────────────┐
       │  WeatherAgentWorkflow       │ │ F1ExpertAgent-   │ │  ask_travel_planner          │
       │  weather-agent-tq           │ │ Workflow         │ │  (single activity on         │
       │  [OpenAI Agents SDK]        │ │ f1-expert-       │ │   orchestrator-tq)           │
       │                             │ │   agent-tq       │ │  [Strands]                   │
       │                             │ │ via F1ExpertSer- │ │                              │
       │                             │ │ vice.ask         │ │  Lazy-imports the third-     │
       │                             │ │ [OpenAI Agents]  │ │  party Strands agent.        │
       └─────────────┬───────────────┘ └─────────┬────────┘ └──────────────┬──────────────┘
                     │                           │                          │
            activity_as_tool             stateless_mcp_server     travel_planner.run(question)
                     │                           │                       (Strands loop)
       ┌─────────────▼────────────┐  ┌───────────▼──────────┐    ┌────────▼─────────────┐
       │  4 weather activities    │  │  F1 MCP server       │    │  Strands agent loop   │
       │  (httpx → public APIs)   │  │  (stdio) → 8 tools   │    │  (Wikipedia REST +    │
       └──────────────────────────┘  └──────────────────────┘    │   REST Countries)     │
                                                                 └───────────────────────┘
```

The travel planner doesn't get its own workflow execution — it's invoked directly as an activity from the orchestrator. That asymmetry is part of the point: a third-party agent that isn't Temporal-aware doesn't need a workflow wrapper to be useful, just an activity wrapper.

Three Workers run in a single Python process via `asyncio.gather(...)`. They poll three distinct task queues, so the routing in the Temporal UI is explicit. The travel-planner activity is registered on the orchestrator's worker — that's the personal-assistant team's infrastructure, the team that owns the wrapper.

## What's different from demo5

Demo5 had two specialists, both built with the OpenAI Agents SDK and both running as their own Temporal workflows. Demo6 adds a third specialist using a different framework (Strands), and **wraps it differently** to highlight the integration trade-off:

- The Strands travel planner is written in `travel_planner.py` with no Temporal imports — it could be vendored from another team's codebase as-is.
- The personal-assistant team owns `travel_planner_activity.py`, a small `@activity.defn` wrapper that lazy-imports the Strands agent and invokes it.
- The orchestrator wires this activity in via `activity_as_tool(...)` — the same helper that the weather agent uses for its individual tools, but here it wraps the entire third-party agent loop.

The orchestrator uses three different invocation patterns:

- **Child workflow** for the weather agent — same namespace, same Temporal cluster, parent-child semantics. Trace context propagates from orchestrator into child via Temporal headers.
- **Nexus** for the F1 expert — designed for cross-namespace / cross-cluster calls. Even within a single namespace it gives you a clean operation-shaped boundary with typed I/O. Trace context does **not** propagate (current limitation in `temporalio.contrib.openai_agents`).
- **Direct activity** for the travel planner — no sub-workflow. The whole Strands agent runs inside one activity invocation.

## Tools

The orchestrator agent sees three tools:

| Tool | Mechanism | Framework | Description |
|---|---|---|---|
| `ask_weather_agent` | child workflow | OpenAI Agents SDK | Delegate weather questions to the weather forecasting specialist |
| `ask_f1_expert` | Nexus operation | OpenAI Agents SDK | Delegate F1 questions to the F1 expert specialist |
| `ask_travel_planner` | activity (no sub-workflow) | Strands Agents SDK | Delegate destination/country questions to the travel planning specialist |

Each specialist has its own internal toolkit. The orchestrator only sees the high-level "ask the specialist" tool.

## Two integration depths

The two frameworks are integrated with Temporal at very different depths, and that's intentional — it lets the demo show both ends of the spectrum.

**OpenAI Agents SDK** (weather agent, F1 expert) — uses `temporalio.contrib.openai_agents`. The plugin and its `activity_as_tool` / `nexus_operation_as_tool` / `stateless_mcp_server` helpers turn every LLM call and every tool call into its own Temporal activity, and the agent loop runs inside a Temporal workflow. Per-step durability: if the worker dies after the third tool call in a five-step loop, only the failing step retries, not the whole loop. Per-step history: the workflow's event log shows each LLM activity and each tool activity individually. Per-step traces: the OpenAI trace dashboard shows nested generation/function spans.

**Strands Agents SDK** (travel planner) — has no Temporal contrib. The Strands agent itself (`travel_planner.py`) is plain Strands code — zero Temporal imports. The personal-assistant team's wrapper (`travel_planner_activity.py`) is a single `@activity.defn` that lazy-imports the agent and calls its `run()` function. The activity is durable — Temporal will retry it on worker death — but everything inside the Strands agent loop is opaque to Temporal. If the activity fails halfway, it restarts from scratch and every internal LLM/tool call re-executes (and re-charges). The orchestrator's workflow history shows exactly **one** activity event for the travel planner, not a per-step breakdown.

The framing for the workshop: "this is an agent another team built without thinking about Temporal — we just wrapped it in an activity to give it coarse-grained durability." That's a real adoption pattern: you don't need a deep framework integration to get *some* benefit from Temporal.

| | OpenAI agents (weather, F1 expert) | Strands agent (travel planner) |
|---|---|---|
| Owns its own workflow? | Yes (sub-workflow per call) | No (just an activity) |
| Activities per agent run | one per LLM call + one per tool call | one (the whole agent loop) |
| Failure mode | per-step retry, prior steps preserved | whole loop restarts |
| History visibility | every LLM/tool call as its own event | opaque single activity |
| Trace dashboard | nested generation + function spans | only what Strands' own tracing emits |
| Code coupling | uses `activity_as_tool` + `OpenAIAgentsPlugin` | zero coupling in the agent file; one tiny activity wrapper |

### Planned next additions to the F1 expert

User-approved, deferred:

- **Wikipedia REST** (`https://en.wikipedia.org/api/rest_v1/page/summary/{title}`) — for F1-specific lookups: driver bios, race history, championship summaries. (The travel planner uses the same API for destination context — different scope, both legitimate.)

Would be added as a `@activity.defn` activity wired via `activity_as_tool(...)` on the F1 expert agent.

## Prerequisites

- **Python 3.10+**
- **uv** — `brew install uv` on macOS
- **Temporal CLI** — `brew install temporal` on macOS
- **OpenAI API key** — `export OPENAI_API_KEY=sk-...`
- **F1 MCP server** — installed locally and reachable via `F1_MCP_SERVER_HOME`. See [demo 3's install instructions](../demo3-mcp/README.md#install-the-f1-mcp-server) for the one-time setup; the same install is reused here.

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

From `demo6-heterogeneous-agent-orchestration/`:

```bash
uv sync
```

### 5. Start the workers (two processes)

The personal-assistant team and the F1 expert team run their own workers with their own plugin configurations. From `demo6-heterogeneous-agent-orchestration/`, in two separate terminals:

```bash
# terminal A — PA + weather + travel-planner activity
uv run python -m worker_pa

# terminal B — F1 expert (separate process, separate plugin config)
uv run python -m worker_f1
```

`worker_pa.py` runs the orchestrator, the weather agent, and the `ask_travel_planner` activity on `orchestrator-tq` and `weather-agent-tq`. `worker_f1.py` runs the F1 expert workflow + Nexus handler on `f1-expert-agent-tq`. The two have different `OpenAIAgentsPlugin` configurations — see "Per-worker plugin configuration" below.

### 6. Start a workflow

In a third terminal (also from `demo6-heterogeneous-agent-orchestration/`):

```bash
uv run python -m start_workflow "What's the weather at the next F1 race?"
```

### Example prompts

```bash
# Weather only — orchestrator → weather agent (child workflow)
uv run python -m start_workflow "What is the weather in Monaco?"

# F1 only — orchestrator → F1 expert (Nexus)
uv run python -m start_workflow "When is the next F1 race?"

# Travel only — orchestrator → ask_travel_planner activity → Strands agent loop
uv run python -m start_workflow "Tell me about Monaco as a travel destination."

# All three specialists in one turn
uv run python -m start_workflow "I'm going to the next F1 race — what's the weather, and what should I know about the destination?"

# Weather + F1 — orchestrator → F1 expert (Nexus) → weather agent (child workflow)
uv run python -m start_workflow "What's the weather at the next F1 race?"

# Compare F1 venues
uv run python -m start_workflow "Compare the typical weather at Monaco and Singapore Grand Prix dates"
```

### Observing the workflow

In the Temporal Web UI at [http://localhost:8233](http://localhost:8233) you'll see:

- The **orchestrator workflow** on `orchestrator-tq`. Its history shows:
  - `StartChildWorkflowExecution` → `ChildWorkflowExecutionCompleted` for the weather path.
  - `NexusOperationScheduled` → `NexusOperationStarted` → `NexusOperationCompleted` for the F1 path.
  - `ScheduleActivityTask: ask_travel_planner` → `ActivityTaskCompleted` for the travel-planner path. **Just one activity event** — the entire Strands agent loop is opaque inside it. This is the visible contrast with the per-step histories of the OpenAI-Agents-backed specialists.
- A separate **weather child workflow** on `weather-agent-tq`, with the four weather activities visible in its own history.
- A separate **F1 expert workflow** on `f1-expert-agent-tq`, started by the Nexus operation handler. Its history shows the F1 MCP `f1-data-list-tools` and `f1-data-call-tool-v2` activities.
- **No separate workflow for the travel planner** — it lives only as that one activity in the orchestrator's history.

In the OpenAI trace dashboard at [https://platform.openai.com/traces](https://platform.openai.com/traces):

- The trace `PersonalAssistant` contains the orchestrator's reasoning plus the **weather agent's** spans nested under it (child workflow trace propagation works).
- The **F1 expert** appears as a *separate* trace, not nested under `PersonalAssistant` (see "Known limitations" below).
- The **travel planner**'s LLM calls go through Strands' own tracing pipeline, not the OpenAI Agents SDK's. They will not appear under `PersonalAssistant`. This is consistent with the fact that the Strands agent isn't aware of any Temporal/OpenAI-Agents trace context.

## Per-worker plugin configuration

`worker_pa.py` and `worker_f1.py` each construct their own `OpenAIAgentsPlugin` with deliberately different settings:

| Worker | `add_temporal_spans` | `mcp_server_providers` | Why |
|---|---|---|---|
| `worker_pa.py` (PA + weather + travel planner activity) | `True` (default) | none | Trace context flows in cleanly via the starter's `with trace(...)` and onward through child workflows. The `temporal:executeWorkflow` / `temporal:startChildWorkflow` / `temporal:startActivity` custom spans render properly in the OpenAI trace dashboard. |
| `worker_f1.py` (F1 expert) | **`False`** | F1 stateless MCP provider | The orchestrator's Nexus call doesn't propagate trace context to this worker (current contrib gap), so the workflow-inbound interceptor would otherwise create `temporal:*` custom spans against no active trace, leaking `parent_id="no-op"` into export batches and producing `[non-fatal] Tracing client error 400` log spam. Disabling `temporal:*` spans on this worker silences the leak. The F1 expert appears as its own top-level trace in the OpenAI dashboard instead of nesting under `PersonalAssistant`. |

This per-worker tuning is a real benefit of running the F1 expert as a separate worker process: each team can choose plugin settings appropriate to its boundary.

## Known limitations

- **Trace context across Nexus is not propagated** by the current `temporalio.contrib.openai_agents` interceptor (verified — `OpenAIAgentsContextPropagationInterceptor` has a `start_child_workflow` method but no Nexus equivalent). Effect: the F1 expert produces its own top-level trace in OpenAI's dashboard rather than nesting under the orchestrator's trace. Workflow history in Temporal still links them via the `NexusOperationScheduled` event. Captured as Issue 1 (and the related Issue 2 on `nexus_operation_as_tool` schema) in `docs/research/openai-agents-plugin-starter-trace-requirement.md`.

## Production split

The two-process layout here matches what a real deployment would look like — different teams running their own workers on their own hosts, each configuring their plugin independently. If you wanted the travel-planner activity isolated on its own infrastructure (so the heavy Strands deps don't share the PA team's environment), give it its own task queue and add a third Worker that registers just that activity.
