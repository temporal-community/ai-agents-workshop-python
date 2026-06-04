---
slug: heterogeneous-agents-different-sdks
id: v9xxp83onfps
type: challenge
title: 'Demo 6a: Heterogeneous Agents — Different SDKs'
teaser: Two frameworks, one orchestrator. A Strands agent joins the OpenAI agents
  behind the same Temporal primitives.
notes:
- type: text
  contents: |
    ## Demo 6a: Heterogeneous Agents — Different SDKs

    Demo 5 had two specialists, both built with the OpenAI Agents SDK.
    Demo 6a adds a third specialist built with a completely different framework:
    **Strands Agents SDK**.

    The key lesson: Temporal's orchestration is framework-agnostic. The
    personal assistant orchestrator doesn't care what framework its specialists
    use — it just calls tools.

    The **travel planner** (Strands) is wired in as a plain activity rather
    than a child workflow. That's the integration trade-off:

    - **OpenAI agents** (weather, F1): per-step durability — every LLM call
      and every tool call is its own Temporal activity. If a worker dies
      mid-loop, only the failing step retries.

    - **Strands agent** (travel planner): coarse-grained durability — the
      entire agent loop is one activity. If the worker dies, the whole loop
      restarts. But the Strands agent itself has zero Temporal imports.

    The orchestrator's event history makes this asymmetry visible: the weather
    and F1 paths show detailed per-step activities; the travel planner path
    shows a single opaque `ask_travel_planner` activity event.
tabs:
- id: p2zrois2si7k
  title: Worker PA
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6a-different-sdks
- id: lid9wwwzzpiv
  title: Worker F1
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6a-different-sdks
- id: s96vbrx0nz2t
  title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6a-different-sdks
- id: j78qnmqyifdj
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: 9onpnlwggtkx
  title: Network Control Panel
  type: service
  hostname: workshop-host
  port: 5000
- id: v5qxuwujv3fq
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1800
enhanced_loading: null
---

# Demo 6a: Heterogeneous Agents — Different SDKs

## What changed

Click the **Editor** tab and open `demo6a-different-sdks`.

New files compared to demo5:

- `travel_planner.py` — the Strands travel agent. **Zero Temporal imports.**
  It could be a library vendored from another team's codebase.
- `travel_planner_activity.py` — a single `@activity.defn` wrapper owned by
  the personal-assistant team. It lazy-imports `travel_planner` and calls
  `run()`. One file, ~10 lines.
- `personal_assistant.py` — now wires three tools: `ask_weather_agent`
  (child workflow), `ask_f1_expert` (Nexus), and `ask_travel_planner`
  (direct activity — no sub-workflow).

## Run it

**Worker PA tab:**
```
uv run python -m worker_pa
```

**Worker F1 tab:**
```
uv run python -m worker_f1
```

**Starter tab:**
```
uv run python -m start_workflow "I'm going to the next F1 race -- what's the weather, and what should I know about the destination?"
```

## The key thing to watch in the Temporal UI

Open the orchestrator workflow and look at its event history side by side with
demo5. You should see:

- `StartChildWorkflowExecution` for the weather agent (same as demo5)
- `NexusOperationScheduled` / `NexusOperationCompleted` for the F1 expert (same as demo5)
- **A single `ScheduleActivityTask: ask_travel_planner`** — the entire Strands
  agent loop, all its LLM calls and tool calls, is opaque inside this one event

That contrast is the point. The weather and F1 specialists show per-step history.
The travel planner shows one event. Same orchestrator, same Temporal primitives,
fundamentally different visibility depending on how deep the framework integration goes.

## Try more prompts

```
uv run python -m start_workflow "Tell me about Monaco as a travel destination."
uv run python -m start_workflow "What's the weather at the next F1 race?"
uv run python -m start_workflow "Compare the weather at Monaco and Singapore on their Grand Prix dates."
```

Click **Check** when you've run at least one workflow that invokes the travel planner.
