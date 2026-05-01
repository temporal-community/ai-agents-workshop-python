---
slug: environment-setup
id: environment-setup
type: challenge
title: "Environment Setup"
teaser: "Verify your environment and get oriented before the first demo."
notes:
  - type: text
    contents: |
      # Building Durable AI Agents with Python and Temporal

      In this workshop you'll work through four progressive demos that show what
      Temporal buys you at each stage of building a production AI agent.

      Each demo adds exactly one new capability — so you can see the before and
      after clearly in the Temporal Web UI.

      **What you'll build:**
      - Demo 1: A hand-written agentic loop as a Temporal workflow
      - Demo 2: The same agent, powered by the OpenAI Agents SDK + Temporal integration
      - Demo 3: MCP tool servers — F1 race data alongside weather tools
      - Demo 4: Human-in-the-loop signals and queries

tabs:
  - title: Terminal
    type: terminal
    hostname: workshop-host
    workdir: /workspace/workshop
  - title: Temporal UI
    type: service
    hostname: workshop-host
    port: 8233
  - title: Editor
    type: service
    hostname: workshop-host
    port: 8080
difficulty: basic
timelimit: 600
---

# Environment Setup

Let's make sure everything is running before we dive in.

## 1. Check the Temporal dev server

The Temporal dev server starts automatically. Confirm it's healthy:

```
temporal operator cluster health
```

You should see `SERVING`. You can also click the **Temporal UI** tab — you should see the Temporal Web UI with no workflows yet.

## 2. Verify your tools

```
python --version
uv --version
temporal --version
node --version
```

## 3. Verify your API key is set

```
echo $OPENAI_API_KEY
```

You should see a key starting with `sk-`. If it's empty, let your facilitator know.

## 4. Explore the workshop repo

```
ls /workspace/workshop
```

You'll see four demo directories. Each is self-contained with its own dependencies and task queue. Click **Check** when you're ready to continue.
