# AI Agents Python Workshop

A series of progressive demos that build an AI agent in Python using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) and [Temporal](https://temporal.io/) for durable execution. Each demo builds on the previous one, adding a single new capability so you can see what each Temporal primitive buys you.

Every demo is self-contained: its own `pyproject.toml`, its own task queue, its own worker. You can work through them in order, or jump into one that matches what you want to learn.

## Demos

| Demo | What's new | Read this first |
|---|---|---|
| [`demo1-agentic-loop`](demo1-agentic-loop/) | A hand-written agentic loop as a Temporal workflow. Calls OpenAI's Responses API from an activity, dispatches tools via a dynamic activity, loops until the model stops asking for tool calls. | [`demo1-agentic-loop/README.md`](demo1-agentic-loop/README.md) |
| [`demo2-openai-temporal-integration`](demo2-openai-temporal-integration/) | Same agent, reimplemented with the OpenAI Agents SDK and Temporal's `temporalio.contrib.openai_agents` plugin. The SDK's `Runner` drives the loop; Temporal makes every LLM call and tool call an activity automatically. Workflow becomes one-line. | [`demo2-openai-temporal-integration/README.md`](demo2-openai-temporal-integration/README.md) |
| [`demo3-mcp`](demo3-mcp/) | Adds an MCP (Model Context Protocol) tool server for Formula 1 race data. MCP operations are dispatched as Temporal activities via `StatelessMCPServerProvider`. The agent now chains F1 tools with weather tools. | [`demo3-mcp/README.md`](demo3-mcp/README.md) |
| [`demo4-hitl`](demo4-hitl/) | Human-in-the-loop. The agent can pause mid-execution to ask the user a question via an in-workflow `ask_user` tool, a Temporal signal for the response, and queries for the starter to poll. | [`demo4-hitl/README.md`](demo4-hitl/README.md) |
| [`demo5-multi-agent`](demo5-multi-agent/) | Multi-agent orchestration. A personal-assistant agent delegates to two specialist sub-agents (weather, F1 expert), invoking one via Temporal child workflow and the other via Nexus. | [`demo5-multi-agent/README.md`](demo5-multi-agent/README.md) |
| [`demo6-heterogeneous-agent-orchestration`](demo6-heterogeneous-agent-orchestration/) | Adds a third specialist (travel planner) built with the Strands Agents SDK alongside demo5's OpenAI Agents SDK specialists. Two frameworks behind one orchestrator — and a deliberate contrast between per-step durability (with Temporal's framework contrib) and coarse-grained, single-activity durability (without). | [`demo6-heterogeneous-agent-orchestration/README.md`](demo6-heterogeneous-agent-orchestration/README.md) |

## How to work through the workshop

Each demo's README is a self-contained walkthrough. The rough shape every time:

1. Start a Temporal dev server once (`temporal server start-dev`). All demos connect to `localhost:7233`.
2. Set `OPENAI_API_KEY` in your shell.
3. `cd demo<N>-…/ && uv sync`
4. Run the worker in one terminal: `uv run python -m worker`
5. Run a workflow in another: `uv run python -m start_workflow "<your prompt>"`

Every demo uses a distinct Temporal task queue, so workers can run side-by-side without interfering with each other.

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — `brew install uv` on macOS.
- **[Temporal CLI](https://docs.temporal.io/cli)** — `brew install temporal` on macOS.
- **OpenAI API key** — set as `OPENAI_API_KEY`.
- **F1 MCP server** (demo3 and demo4 only) — a Node.js + Python hybrid that wraps [FastF1](https://docs.fastf1.dev/). Expected at `~/Projects/Temporal/AI/MCP/f1-mcp-server/`; override with `F1_MCP_SERVER_HOME`. See each demo's README for details.

## Observing what Temporal gives you

All demos are Temporal workflows, so you can watch them in the Temporal Web UI at http://localhost:8233. The comparisons between demos are most interesting in that UI — demo2's tool calls appear as activities automatically, demo3 adds MCP listTools/callTool activities, demo4 shows a workflow that suspends durably on `wait_condition` and later receives a signal, and demo6 puts per-step (OpenAI Agents) and single-activity (Strands) durability side by side.

Demos 2–6 also send traces to OpenAI's trace dashboard at https://platform.openai.com/traces, so you can see the agent's reasoning alongside the Temporal-side history.

## Project layout

```
temporal-ai-agents/
├── README.md                                  # this file
├── docs/                                      # planning + research notes
│   ├── plans/                                 # work items (demo parity plans, open items)
│   └── research/                              # investigation notes (e.g. trace integration quirks)
├── demo1-agentic-loop/
├── demo2-openai-temporal-integration/
├── demo3-mcp/
├── demo4-hitl/
├── demo5-multi-agent/
└── demo6-heterogeneous-agent-orchestration/
```

## Related

This workshop has a [Java / Spring AI sibling](https://github.com/temporal-community/springio-agents-springai-temporal) that covers the same progression using Spring AI instead of the OpenAI Agents SDK. The two implementations diverge in interesting ways where the frameworks differ — see `docs/research/tool-execution-strategies-java-vs-python.md` for one such comparison.
