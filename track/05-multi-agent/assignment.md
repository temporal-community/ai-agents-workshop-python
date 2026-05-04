---
slug: multi-agent
id: xcecicb6wthw
type: challenge
title: 'Demo 5: Multi-Agent Orchestration'
teaser: Three agents, three workflows. A personal assistant delegates to specialists
  via child workflow and Nexus.
notes:
- type: text
  contents: |
    ## Demo 5: Multi-Agent Orchestration

    Demo 4 was one workflow, one agent. Demo 5 introduces agent-as-workflow:
    each specialist is a real Temporal workflow execution, not an inline function.

    A personal assistant orchestrator delegates to two specialists:

    - **Weather agent** - invoked as a Temporal child workflow. Parent-child
      semantics, trace context propagates, shows as StartChildWorkflowExecution
      in the parent's history.

    - **F1 expert** - invoked via Nexus. Designed for cross-namespace boundaries,
      gives a clean typed operation interface. Shows as NexusOperationScheduled
      in the parent's history.

    Two different worker processes, two different plugin configurations,
    three separate task queues - you can see all three workflow executions
    independently in the Temporal UI.
tabs:
- id: uiv2s44gv4qr
  title: Worker PA
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo5-multi-agent
- id: xzsrty2svsny
  title: Worker F1
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo5-multi-agent
- id: q7xfa7anuklv
  title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo5-multi-agent
- id: ywyr433caxyb
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: ibtbtwufve7r
  title: Network Control Panel
  type: service
  hostname: workshop-host
  port: 5000
- id: etyyohta43gd
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1800
enhanced_loading: null
---

# Demo 5: Multi-Agent Orchestration

## What changed

Click the **Editor** tab and open `demo5-multi-agent`. The key new files are:

- `personal_assistant.py` - the orchestrator workflow. Uses `child_workflow_as_tool`
  for the weather agent and `nexus_operation_as_tool` for the F1 expert.
- `weather_agent.py` - the weather specialist, runs as its own workflow on `weather-agent-tq`.
- `f1_expert_agent.py` - the F1 specialist, runs as its own workflow on `f1-expert-agent-tq`.
  Also defines the Nexus service interface (`F1ExpertService`) and handler.
- `worker_pa.py` - runs the orchestrator and weather agent (two task queues, one process).
- `worker_f1.py` - runs the F1 expert and its Nexus handler (separate process, separate plugin config).

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
uv run python -m start_workflow "What's the weather at the next F1 race?"
```

## Watch it in the Temporal UI

This is the key moment. You should see **three separate workflow executions**:

- The **orchestrator workflow** on `orchestrator-tq`. Its history shows
  `StartChildWorkflowExecution` for the weather path, and
  `NexusOperationScheduled` / `NexusOperationCompleted` for the F1 path.
- A separate **WeatherAgentWorkflow** on `weather-agent-tq`, with its own
  activity history.
- A separate **F1ExpertAgentWorkflow** on `f1-expert-agent-tq`, with its own
  F1 MCP activity history.

Each specialist is independently observable, independently retryable, and
could independently be deployed on a different team's infrastructure.

## Try more prompts

```
uv run python -m start_workflow "What is the weather in Monaco?"
uv run python -m start_workflow "When is the next F1 race?"
uv run python -m start_workflow "Compare the weather at Monaco and Singapore on their Grand Prix dates"
```

Click **Check** when you've run at least one workflow successfully.
