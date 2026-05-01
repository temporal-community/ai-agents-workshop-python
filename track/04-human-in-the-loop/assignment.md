---
slug: human-in-the-loop
id: jj9quaamkjwi
type: challenge
title: 'Demo 4: Human-in-the-Loop'
teaser: The agent pauses mid-execution to ask you a question. A Temporal signal resumes
  it.
notes:
- type: text
  contents: |
    ## Demo 4: Human-in-the-Loop

    Sometimes an agent needs to ask a question before it can continue. Demo 4
    adds that capability using three Temporal primitives working together:

    - An **`ask_user` tool** defined inside the workflow that calls
      `workflow.wait_condition()` — suspending execution durably with no
      worker resources consumed while waiting.
    - A **signal** (`provide_user_input`) that delivers your answer and
      unblocks the workflow.
    - Two **queries** (`is_input_needed`, `get_pending_question`) that let
      the starter poll to detect when the agent is waiting and what it asked.

    While the workflow is suspended, you could restart the worker, redeploy
    your service, or wait days — the workflow will resume exactly where it
    left off the moment the signal arrives.
tabs:
- id: fxsv3lucmj5e
  title: Terminal
  type: terminal
  hostname: workshop-host
- id: nxm6q05axvqh
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: 0jpbuxjypy4y
  title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1800
enhanced_loading: null
---

# Demo 4: Human-in-the-Loop

## What changed

Open `/workspace/workshop/demo4-hitl` in the Editor:

- `tools_workflow.py` — an `ask_user` `@function_tool` is defined *inside*
  `run()` as a closure. It captures `self`, sets `self._input_needed = True`,
  and blocks on `await workflow.wait_condition(...)`. The signal handler flips
  the flag to unblock it.
- `start_workflow.py` — the starter polls queries every 2 seconds. When it
  detects `is_input_needed == True`, it reads your response from stdin and
  sends it as a signal.

## Run it

**Terminal 1 — worker:**
```bash
cd /workspace/workshop/demo4-hitl
uv run python -m worker
```

**Terminal 2 — workflow:**
```bash
cd /workspace/workshop/demo4-hitl
uv run python -m start_workflow "Should I bring rain gear to the F1 race?"
```

The prompt is intentionally ambiguous. The agent will ask you which race you
mean. Type your answer and press Enter.

## Watch the suspension in the Temporal UI

While the workflow is waiting for your input, switch to the **Temporal UI**.
The workflow shows as **Running** — but look at the event history. There are
no pending activity tasks; the workflow is simply suspended on a
`wait_condition`. No worker threads are consumed.

When you send your response, watch a new event appear: the signal arrives,
the `wait_condition` unblocks, and the agent continues.

## Reconnect to a waiting workflow

Close the starter terminal while the agent is waiting. The workflow keeps
running on the server. Reconnect:

```bash
# Get the workflow ID from the Temporal UI, then:
uv run python -m start_workflow --workflow-id hitl-agent-<uuid>
```

This demonstrates that the human interaction is decoupled from any particular
process — the workflow state lives in Temporal, not in your starter script.

Click **Check** when you've completed a full human-in-the-loop interaction.
