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

    In Demo 1 we make that loop explicit, written by hand as a Temporal
    workflow. The LLM call is one activity. Each tool dispatch is another
    activity. Temporal's event history records every step.

    The payoff: if the worker crashes mid-loop, the workflow replays from
    history and picks up exactly where it left off - no duplicate LLM calls,
    no lost tool results.
tabs:
- id: dlcy32x3lwyw
  title: Worker
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo1-agentic-loop
- id: 4m0obiegxvsk
  title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo1-agentic-loop
- id: b76krwtx7tyk
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- title: Network Control Panel
  type: service
  hostname: workshop-host
  port: 5000
- id: pjlbsyohlkk4
  title: VS Code
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1200
enhanced_loading: null
---

# Demo 1: The Hand-Written Agentic Loop

## What you're looking at

Click the **VS Code** tab and open `demo1-agentic-loop`. The key files are:

- `workflows/agent.py` - the `while True` loop: call LLM, dispatch tool if needed, repeat until the model returns a final answer
- `activities/openai_responses.py` - the LLM activity: sends the conversation history to OpenAI and returns the model's response
- `activities/tool_invoker.py` - a single *dynamic* activity that routes to whichever tool the LLM chose
- `tools/` - four weather tools: `get_ip_address`, `get_location_info`, `get_coordinates`, `get_weather`

## Run it

**Worker tab - start the worker:**
```
uv run python -m worker
```

You should see `Worker started. Listening on task queue: tool-invoking-agent-python-task-queue`.

**Starter tab - start a workflow:**
```
uv run python -m start_workflow "What is the weather in Barcelona?"
```

## Watch it in the Temporal UI

Switch to the **Temporal UI** tab while the workflow runs. Click into it and
you'll see each LLM call and each tool invocation as a separate activity in
the event history - the full decision trail of the agent.

## Try a multi-step prompt

```
uv run python -m start_workflow "What is the weather where I am right now?"
```

This chains three tools: `get_ip_address` then `get_location_info` then `get_weather`.

## The durability point

While a workflow is running, try disabling the Weather service in the **Network Control Panel** tab. Watch the activity fail and retry in the Temporal UI. Re-enable it and watch the workflow resume - zero code changes.

Click **Check** when you've run at least one workflow successfully.
