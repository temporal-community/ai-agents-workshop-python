---
slug: agentic-loop
id: xzmridxou6au
type: challenge
title: 'Demo 1: The Hand-Written Agentic Loop'
teaser: Build an agentic loop from scratch as a Temporal workflow, and watch it survive
  failure.
notes:
- type: text
  contents: |
    ## Demo 1: The Agentic Loop

    Most AI agent frameworks hide a loop from you: call the LLM, check if it
    wants to use a tool, call the tool, feed the result back, repeat.

    In Demo 1 we make that loop explicit — written by hand as a Temporal
    workflow. The LLM call is one activity. Each tool dispatch is another
    activity. Temporal's event history records every step.

    The payoff: if the worker crashes mid-loop, the workflow replays from
    history and picks up exactly where it left off — no duplicate LLM calls,
    no lost tool results.
tabs:
- id: dlcy32x3lwyw
  title: Terminal
  type: terminal
  hostname: workshop-host
- id: 4m0obiegxvsk
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: b76krwtx7tyk
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1200
enhanced_loading: null
---

# Demo 1: The Hand-Written Agentic Loop

## What you're looking at

Open the Editor tab and navigate to `/workspace/workshop/demo1-agentic-loop`. The key files are:

- `workflows/agent.py` — the `while True` loop: call LLM, dispatch tool if
  needed, repeat until the model returns a final answer
- `activities/openai_responses.py` — the LLM activity: sends the conversation
  history to OpenAI and returns the model's response
- `activities/tool_invoker.py` — a single *dynamic* activity that routes to
  whichever tool the LLM chose
- `tools/` — four weather tools: `get_ip_address`, `get_location_info`,
  `get_coordinates`, `get_weather`

## Run it

Open two terminals (use the `+` button to split).

**Terminal 1 — start the worker:**
```bash
cd /workspace/workshop/demo1-agentic-loop
uv run python -m worker
```

**Terminal 2 — start a workflow:**
```bash
cd /workspace/workshop/demo1-agentic-loop
uv run python -m start_workflow "What is the weather in Barcelona?"
```

## Watch it in the Temporal UI

Switch to the **Temporal UI** tab. Click into the running (or completed)
workflow. You'll see each LLM call and each tool invocation as a separate
activity in the event history — the full decision trail of the agent.

## Try a multi-step prompt

```bash
uv run python -m start_workflow "What is the weather where I am right now?"
```

This one chains three tools: `get_ip_address` → `get_location_info` →
`get_weather`. Watch the Temporal UI as each activity completes in sequence.

## The durability point

While a workflow is running, try stopping and restarting the worker:

```bash
# In Terminal 1, press Ctrl+C, then immediately:
uv run python -m worker
```

The workflow will resume from exactly where it left off — completed activities
are not re-run. The event history is the source of truth.

Click **Check** when you've run at least one workflow successfully.
