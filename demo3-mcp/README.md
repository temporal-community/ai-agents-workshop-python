# Demo 3 - MCP Integration

Extends demo2 by adding a Model Context Protocol (MCP) tool server for Formula 1 race data. The agent can now look up F1 race schedules, results, and standings, then chain those with the existing weather tools to answer questions like "When is the next F1 race and what will the weather be like there?"

## What's different from demo2

Demo2 exposed four weather tools as Temporal activities, wrapped via `activity_as_tool(...)` so the OpenAI Agents SDK's `Runner` could call them.

Demo3 adds an external MCP server — `f1-mcp-server`, a Node.js + Python hybrid — and wires it in through Temporal's `StatelessMCPServerProvider`. Each MCP operation (`listTools`, a `callTool` invocation) is dispatched as its own Temporal activity, so MCP tool calls are durable, retryable, and visible in workflow history alongside the weather activities.

## Architecture

The F1 MCP server is **a local subprocess**, not a remote service. The worker spawns it on demand and communicates with it over **stdio** (line-delimited JSON-RPC on the child process's stdin/stdout). No HTTP, no port, no separate "server" to keep running. When a workflow tick needs to invoke an F1 tool, the contrib's stateless provider connects, calls, and cleans up — the subprocess lives only for the duration of one MCP operation.

- **`StatelessMCPServerProvider`** (from `temporalio.contrib.openai_agents`) — registered on the worker under the name `"f1-data"`. Each `list_tools()` / `call_tool()` becomes a Temporal activity that connects, calls, and cleans up. No persistent connection between workflow ticks.
- **`stateless_mcp_server("f1-data")`** (workflow-side) — returns a handle that the agent passes to `Agent(mcp_servers=[...])`. Calls go through the activities the provider registered.
- **`MCPServerStdio`** — the Agents SDK's stdio transport. Configured here to launch `bash -c "source $F1_MCP_SERVER_HOME/.venv/bin/activate && node $F1_MCP_SERVER_HOME/build/index.js"` so the F1 server's Node entrypoint can shell out to Python (FastF1).
- **`OpenAIAgentsPlugin(mcp_server_providers=[...])`** — wires the provider's activities into the worker automatically. No manual activity registration for MCP.

### Trade-off: tool coupling

Same as demo2 — activity-backed tools and MCP-backed tools are both coupled to Temporal (they run as activities). The win vs. calling the MCP server directly from the workflow is that each MCP call is a durable, observable unit in the workflow history, with retry policy support.

### Tools

**Weather tools (reused from demo2 — Temporal activities):**

| Tool | API | Purpose |
|------|-----|---------|
| `get_ip_address` | icanhazip.com | Get the caller's public IP address |
| `get_location_info` | ip-api.com | Get city, country, lat/lon for an IP address |
| `get_coordinates` | Open-Meteo Geocoding | Get lat/lon for a city name |
| `get_weather` | Open-Meteo Forecast | Get current temperature, weather code, and wind speed |

**F1 tools (new — provided by the MCP server):**

| Tool | Purpose |
|------|---------|
| `get_event_schedule` | F1 race calendar for a season |
| `get_event_info` | Details about a specific Grand Prix |
| `get_session_results` | Race / qualifying / practice session results |
| `get_driver_info` | Driver information for a session |
| `analyze_driver_performance` | Lap times and performance metrics |
| `compare_drivers` | Compare multiple drivers in a session |
| `get_telemetry` | Vehicle telemetry for a lap |
| `get_championship_standings` | Driver and constructor standings |

## Prerequisites

- **Python 3.10+**
- **uv** — `brew install uv` (macOS) or see [uv docs](https://docs.astral.sh/uv/)
- **Node.js 18+** — needed to run the F1 MCP server's TypeScript entrypoint
- **Temporal CLI** — `brew install temporal` (macOS) or see [Temporal CLI docs](https://docs.temporal.io/cli)
- **OpenAI API key** — set as `OPENAI_API_KEY` environment variable
- **F1 MCP server** — installed locally, see [Install the F1 MCP server](#install-the-f1-mcp-server) below

## Install the F1 MCP server

This is a one-time setup. The worker will launch the server as a local subprocess each time it needs to call an F1 tool, but the server itself is a Node.js + Python hybrid that you have to clone, build, and provision a Python venv for ahead of time.

### 1. Clone the repository

Pick a directory you'd like to keep the server in. Anywhere is fine; the worker locates it via the `F1_MCP_SERVER_HOME` environment variable below.

```bash
git clone https://github.com/rakeshgangwar/f1-mcp-server.git
cd f1-mcp-server
```

### 2. Build the Node.js side

```bash
npm install
npm run build
```

This produces the `build/index.js` entrypoint that the worker spawns.

### 3. Provision the Python side

The Node.js entrypoint shells out to `python3` (within the activated venv) to run [FastF1](https://github.com/theOehrly/Fast-F1) for the actual data lookups. Create a venv inside the project and install the Python deps:

```bash
uv venv
source .venv/bin/activate
uv pip install fastf1 pandas numpy
deactivate
```

The worker will activate this venv on each invocation via the launch command shown in the Architecture section above.

### 4. Point the workshop worker at the install location

```bash
export F1_MCP_SERVER_HOME=/absolute/path/to/f1-mcp-server
```

Add this to your shell profile if you want it persisted across sessions. The workshop worker reads this variable at startup and bakes it into the `MCPServerStdio` launch command.

## Running

### 1. Start the Temporal dev server

```bash
temporal server start-dev
```

### 2. Set your OpenAI API key (both terminals)

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Install dependencies

From `demo3-mcp/`:

```bash
uv sync
```

### 4. Start the worker

```bash
uv run python -m worker
```

The worker connects with the `OpenAIAgentsPlugin` (configured with the F1 MCP provider), registers `AgentWorkflow`, the four weather activities, and the auto-generated MCP activities, then polls the `f1-agent-python-task-queue` task queue. Leave this running.

### 5. Start a workflow

In a second terminal (also from `demo3-mcp/`):

```bash
uv run python -m start_workflow "When is the next F1 race and what will the weather be there?"
```

### Example prompts

```bash
# F1 + weather — chains get_event_schedule -> get_coordinates -> get_weather
uv run python -m start_workflow "When is the next F1 race and what will the weather be there?"

# F1 schedule only
uv run python -m start_workflow "What is the 2025 F1 race calendar?"

# Weather only (existing tools still work)
uv run python -m start_workflow "What is the weather in Barcelona?"

# Combined analysis
uv run python -m start_workflow "What were the results of the last Monaco Grand Prix and what is the weather there right now?"
```

### Observing the workflow

View running workflows in the Temporal Web UI at [http://localhost:8233](http://localhost:8233). You'll see three kinds of activity entries in the history:

- `InvokeModelActivity` — the LLM calls.
- Weather activities (`get_coordinates`, `get_weather`, etc.) — the `@activity.defn` tools from demo2.
- `f1-data-list-tools` and `f1-data-call-tool-v2` — the MCP operations, each dispatched as its own Temporal activity.

Traces (if `OPENAI_API_KEY` is set in the starter terminal) appear at [https://platform.openai.com/traces](https://platform.openai.com/traces) under the trace name `AgentWorkflow`, with nested generation, function (weather), and MCP spans.
