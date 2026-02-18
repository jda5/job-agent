from typing import Any

# -------------------------------------------------------------------------------- openai tool definitions

_OPENAI_PERFORM_RESEARCH_TOOL = {
    "type": "function",
    "name": "perform_research",
    "description": "Delegates a research task to a specialized web-browsing agent.",
    "parameters": {
        "type": "object",
        "properties": {
            "research_topic": {
                "type": "string",
                "description": "The specific question or topic to investigate.",
            },
        },
        "required": ["research_topic"],
    },
}

_OPENAI_WEB_SEARCH_TOOL = {
    "type": "web_search",
}

# -------------------------------------------------------------------------------- tool mapping

_tool_map: dict[str, dict[str, Any]] = {
    "perform_research": _OPENAI_PERFORM_RESEARCH_TOOL,
    "web_search": _OPENAI_WEB_SEARCH_TOOL,
}


def get_tools(tool_names: list[str]) -> list[dict[str, Any]]:
    """
    Retrieves tool definitions based on a list of tool names.
    """
    return [_tool_map[tool_name] for tool_name in tool_names]
