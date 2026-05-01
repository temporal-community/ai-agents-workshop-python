---
slug: mcp-tools
id: rdzxrsbfsuvs
type: challenge
title: 'Demo 3: MCP Tool Servers'
teaser: Add a Formula 1 data server via MCP. Each tool call becomes a durable Temporal
  activity.
notes:
- type: text
  contents: |
    ## Demo 3: MCP + Temporal

    Model Context Protocol (MCP) is a standard for connecting AI agents to
    external tool servers. Demo 3 adds an F1 race data server alongside the
    existing weather tools.

    The key: `StatelessMCPServerProvider` routes every MCP operation through
    Temporal. Each `listTools` and `callTool` becomes its own activity in the
    workflow history — durable, retryable, and observable — without any extra
    code from you.

    The agent can now answer questions that chain F1 data with weather:
    "When is the next race and what will the weather be there?"
tabs:
- id: khujr3sxpl3v
  title: Terminal
  type: terminal
  hostname: workshop-host
- id: lzzaloqoytcq
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: uaiuwohwqfea
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1500
enhanced_loading: null
---

# Demo 3: MCP Tool Servers

## What changed

Open `/workspace/workshop/demo3-mcp` in the Editor:

- `worker.py` — a `StatelessMCPServerProvider` is registered with the plugin.
  It launches the F1 MCP server process and wraps its operations as Temporal
  activities automatically.
- `tools_workflow.py` — `stateless_mcp_server("f1-data")` gives the agent a
  handle to the MCP server. Eight F1 tools appear alongside the four weather tools.
- The workflow code itself is nearly identical to demo2 — adding MCP required
  almost no changes to the workflow logic.

## Run it

**Terminal 1 — worker:**
```bash
cd /workspace/workshop/demo3-mcp
uv run python -m worker
```

**Terminal 2 — workflow:**
```bash
cd /workspace/workshop/demo3-mcp
uv run python -m start_workflow "When is the next F1 race and what will the weather be there?"
```

> Note: The first workflow may take 15-30 seconds on the F1 tool calls while
> FastF1 downloads session data. Subsequent runs are fast from the local cache.

## What to look for in the Temporal UI

Find your completed workflow. You'll see three kinds of activity entries:

- `InvokeModelActivity` — the LLM reasoning steps
- Weather activities (`get_coordinates`, `get_weather`, etc.)
- `f1-data-list-tools` and `f1-data-call-tool-v2` — MCP operations, each as
  its own durable activity

The F1 data calls look just like any other activity from Temporal's perspective.
That's the point.

## Try more prompts

```bash
uv run python -m start_workflow "What is the 2025 F1 race calendar?"
uv run python -m start_workflow "What were the results of the last Monaco Grand Prix?"
```

Click **Check** when you've run at least one workflow successfully.
