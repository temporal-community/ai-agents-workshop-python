---
slug: openai-agents-sdk
id: pg6xxx7txwrq
type: challenge
title: 'Demo 2: OpenAI Agents SDK + Temporal Integration'
teaser: The same agent, but the SDK drives the loop. Temporal durability becomes automatic.
notes:
- type: text
  contents: |
    ## Demo 2: OpenAI Agents SDK + Temporal

    Demo 1's workflow was ~50 lines of explicit loop logic. Demo 2 collapses
    that to a single `Runner.run(...)` call.

    The OpenAI Agents SDK drives the tool-calling loop. Temporal's
    `OpenAIAgentsPlugin` intercepts it transparently: every LLM call and every
    tool invocation becomes a Temporal activity automatically. The developer
    writes standard SDK code; Temporal durability is free.

    The trade-off: tools must now be `@activity.defn` functions rather than
    plain Python. They gain durability but they're no longer Temporal-agnostic.
tabs:
- id: paamfrjtl6jp
  title: Worker
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo2-openai-temporal-integration
- id: mzxhkdd9ly6f
  title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo2-openai-temporal-integration
- id: xxhzofvtcgdf
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: zwbzs5jwr8wu
  title: Network Control Panel
  type: service
  hostname: workshop-host
  port: 5000
- id: l7jrbvxuygss
  title: VS Code
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1200
enhanced_loading: null
---

# Demo 2: OpenAI Agents SDK + Temporal Integration

## What changed

Click the **VS Code** tab and open `demo2-openai-temporal-integration`. Compare it to demo1:

- `tools_workflow.py` - the entire agentic loop is now one line: `result = await Runner.run(agent, input=question)`
- `tool_activities.py` - tools are `@activity.defn` functions. `activity_as_tool(...)` wraps each one for the SDK.
- `worker.py` - the `OpenAIAgentsPlugin` is registered on both the client and worker. It installs the model-execution activity and interceptors automatically.

## Run it

**Worker tab:**
```
uv run python -m worker
```

**Starter tab:**
```
uv run python -m start_workflow "What is the weather in Tokyo?"
```

## Watch it in the Temporal UI

Look at a completed workflow. The `InvokeModelActivity` appears as its own
named entry - the SDK's model calls are now first-class Temporal activities,
alongside the tool calls.

## Try disabling a service

Start a new workflow, then use the **Network Control Panel** to disable Weather.
Watch the weather activities fail and retry in the Temporal UI. Re-enable and
watch the workflow succeed - no code changes required.

Click **Check** when you've run at least one workflow successfully.
