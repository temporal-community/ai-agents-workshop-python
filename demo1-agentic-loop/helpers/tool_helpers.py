from openai.lib._pydantic import to_strict_json_schema  # private API; may change
# there currently is no public API to generate the tool definition from a Pydantic model
# or a function signature.
from pydantic import BaseModel

def oai_responses_tool_from_model(name: str, description: str, model: type[BaseModel]):
    return {
        "type": "function",
        "name": name,
        "description": description,
        # OpenAI Responses strict tools require a JSON Schema object where
        # additionalProperties is explicitly false. For tools without
        # parameters, supply an empty object schema.
        "parameters": (
            to_strict_json_schema(model)
            if model
            else {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        ),
        "strict": True,
    }

HELPFUL_AGENT_SYSTEM_INSTRUCTIONS = """
You are a helpful assistant. Use the provided tools to help accomplish the user's goal.
Always use tools when they would help answer the question accurately.
When you have enough information to fully answer, provide your final response as plain text.
"""