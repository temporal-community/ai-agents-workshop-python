The files in this directory should not be considered a part of the agent implmementation, rather 
are metaphorically a set of tools that are made available to the agent at "runtime". This is 
reminiscent of registering MCP tools with something like Claude Desktop or Cursor. In this sample
we have not implemented that tool registry and have instead isolated the tool registry into this
separate set of files. We also are reloading tools at runtime, rather, whichever tools are defined
at the time we start the agent are loaded.

The tools, however, are completely abstracted away from the agent.

Note that the agentic loop calls an activity by the name of the tool selected by the LLM and this
activity invocation is handled by the tool_invoker dynamic activity.

To add or swap tools, edit `tools/__init__.py` to register handlers and OpenAI tool schemas.