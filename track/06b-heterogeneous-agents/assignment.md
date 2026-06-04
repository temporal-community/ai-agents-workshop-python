---
slug: heterogeneous-agents-different-languages
type: challenge
title: 'Demo 6b: Heterogeneous Agents — Different Languages'
teaser: Same orchestrator, Java specialist. The travel planner moves to Spring AI
  and gets per-step durability over Nexus.
notes:
- type: text
  contents: |
    ## Demo 6b: Heterogeneous Agents — Different Languages

    Demo 6a showed heterogeneity axis 1: different frameworks, same language
    (Python + Strands). Demo 6b shows axis 2: a different language entirely.

    The travel planner is reimplemented in **Java with Spring AI**. The Python
    orchestrator reaches it over **Nexus** — the same boundary it already uses
    for the F1 expert. The Java side doesn't share any code with Python; the
    two sides agree only on string names and JSON shapes.

    The payoff: the Java travel planner now gets **per-step durability**. Every
    LLM call and every tool call inside the Spring AI agent loop is its own
    Temporal activity — exactly like the OpenAI Agents SDK specialists. Compare
    its workflow history to demo 6a's single opaque `ask_travel_planner` event.

    Three workers, three languages of expertise, one Python orchestrator. The
    orchestration is language-agnostic.
tabs:
- title: Java Worker
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6b-different-languages/travel-planner-java
- title: Worker PA
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6b-different-languages
- title: Worker F1
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6b-different-languages
- title: Starter
  type: terminal
  hostname: workshop-host
  workdir: /workspace/workshop/demo6b-different-languages
- title: Temporal UI
  type: service
  hostname: workshop-host
  port: 8233
- title: Network Control Panel
  type: service
  hostname: workshop-host
  port: 5000
- title: Editor
  type: service
  hostname: workshop-host
  port: 8080
difficulty: basic
timelimit: 2400
enhanced_loading: null
---

# Demo 6b: Heterogeneous Agents — Different Languages

## What changed from 6a

The travel planner moved from Python (Strands, one activity) to **Java (Spring AI,
full workflow over Nexus)**. Everything else — the Python orchestrator, the weather
agent, the F1 expert — is unchanged.

| | demo6a | demo6b |
|---|---|---|
| Travel planner language | Python | Java |
| Travel planner framework | Strands Agents SDK | Spring AI |
| Invocation from orchestrator | direct activity | Nexus operation |
| Durability of travel agent | coarse (whole loop = one activity) | per-step (each LLM/tool call = one activity) |

## Run it

**Java Worker tab** — start the Spring AI travel planner:
```
./mvnw spring-boot:run
```
This starts a Temporal worker on `travel-planner-agent-tq` hosting the
`TravelPlannerAgentWorkflow` and the `TravelPlannerService` Nexus handler.

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
uv run python -m start_workflow "What should I know about visiting Monaco?"
```

## The key thing to watch in the Temporal UI

Open the **orchestrator workflow** history. The travel planner path now shows
`StartNexusOperation` / `NexusOperationCompleted` — the same boundary shape as
the F1 expert — instead of a single opaque activity event.

Then find the **`TravelPlannerAgentWorkflow`** on `travel-planner-agent-tq` and
open its history. You should see per-step activities: a `ChatModelActivity` for
each LLM call and individual activities for each tool call (`getWikipediaSummary`,
`getCountryInfo`). That's the Spring AI integration giving the Java agent the same
per-step durability the OpenAI Agents SDK gives the Python agents.

## Try more prompts

```
# Travel only — exercises the Java path
uv run python -m start_workflow "What should I know about visiting Monaco?"

# F1 only — Python Nexus path (unchanged from 6a)
uv run python -m start_workflow "When is the next F1 race?"

# All three specialists
uv run python -m start_workflow "What's the weather at the next F1 race and what should I know about visiting the destination?"
```

Click **Check** when you've run at least one workflow that invokes the Java travel planner.
