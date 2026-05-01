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

    An `ask_user` tool defined inside the workflow calls `workflow.wait_condition()`
    to suspend execution durably with no worker resources consumed while waiting.

    A signal (`provide_user_input`) delivers your answer and unblocks the workflow.

    Two queries (`is_input_needed`, `get_pending_question`) let the starter poll
    to detect when the agent is waiting and what it asked.

    While the workflow is suspended, you could restart the worker, redeploy
    your service, or wait days - the workflow resumes exactly where it left off
    the moment the signal arrives.
tabs:
- id: fxsv3lucmj5e
  title: Worker
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo4-hitl
- id: nxm6q05axvqh
  title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo4-hitl
- id: 0jpbuxjypy4y
  title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- id: 84uqxxylcabb
  title: VS Code
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 1800
enhanced_loading: null
---

# Demo 4: Human-in-the-Loop

## What changed

Click the **VS Code** tab and open `demo4-hitl`:

- `tools_workflow.py` - an `ask_user` `@function_tool` is defined inside `run()` as a closure. It sets `self._input_needed = True` and blocks on `await workflow.wait_condition(...)`. The signal handler flips the flag to unblock it.
- `start_workflow.py` - polls queries every 2 seconds. When `is_input_needed` is True, it prints the question, reads your response from the terminal, and sends it as a signal.

## Run it

**Worker tab:**
```
uv run python -m worker
```

**Starter tab:**
```
uv run python -m start_workflow "Should I bring rain gear to the F1 race?"
```

The agent will ask you which race you mean. Type your answer and press Enter.

## Watch the suspension in the Temporal UI

While the workflow is waiting, the **Temporal UI** shows it as **Running** but
there are no pending activity tasks. The workflow is suspended on `wait_condition`.
No worker threads are consumed.

When you respond, watch a new event appear: the signal arrives, the
`wait_condition` unblocks, and the agent continues.

## Reconnect to a waiting workflow

If you close the Starter terminal while the agent is waiting, the workflow
keeps running on the server. Find the workflow ID in the Temporal UI, then:

```
uv run python -m start_workflow --workflow-id hitl-agent-<uuid>
```

Click **Check** when you've completed a full interaction with the agent.
