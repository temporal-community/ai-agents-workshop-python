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
  title: Terminal
  type: terminal
  hostname: workshop-host
- id: mzxhkdd9ly6f
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: xxhzofvtcgdf
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1200
enhanced_loading: null
---

# Demo 2: OpenAI Agents SDK + Temporal Integration

## What changed

Open `/workspace/workshop/demo2-openai-temporal-integration` in the Editor. Compare it to demo1:

- `tools_workflow.py` — the entire agentic loop is now `result = await Runner.run(agent, input=question)`. One line.
- `tool_activities.py` — tools are `@activity.defn` functions. `activity_as_tool(...)` wraps each one for the SDK.
- `worker.py` — the `OpenAIAgentsPlugin` is registered on both the client and worker. It installs the model-execution activity and interceptors automatically.

## Run it

**Terminal 1 — worker:**
```bash
cd /workspace/workshop/demo2-openai-temporal-integration
uv run python -m worker
```

**Terminal 2 — workflow:**
```bash
cd /workspace/workshop/demo2-openai-temporal-integration
uv run python -m start_workflow "What is the weather in Tokyo?"
```

## Compare in the Temporal UI

Look at a completed workflow from this demo alongside one from demo1. The
activity sequence is the same: LLM call, tool call, LLM call, tool call...
But in demo2 the `InvokeModelActivity` appears as its own named entry —
the SDK's model calls are now first-class Temporal activities.

## OpenAI Traces

If you open [https://platform.openai.com/traces](https://platform.openai.com/traces)
in a browser, you'll see the agent's reasoning trace alongside the Temporal
event history — two complementary views of the same execution.

Click **Check** when you've run at least one workflow successfully.
