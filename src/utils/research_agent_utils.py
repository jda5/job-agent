import asyncio
from abc import ABC, abstractmethod

from openai.types.responses import Response

from agents.research_agent import ResearchAgent
from dependencies.clients import get_openai_client
from models.agent_models import ClientResponse, ModelTier, ReasoningLevel

# -------------------------------------------------------------------------------- handler classes


class ProviderHandler(ABC):
    """
    Abstract base class for provider-specific tool handling.
    """

    @abstractmethod
    def format_assistant_message(self, response: ClientResponse) -> dict | list[dict]:
        """
        Format the assistant's response for the conversation history.
        """

    @abstractmethod
    def format_tool_results(self, agents: list[ResearchAgent]) -> dict | list[dict]:
        """
        Format tool results for the next request.
        """


class _OpenAIHandler(ProviderHandler):
    def format_assistant_message(self, response: ClientResponse) -> list[dict]:
        _response: Response = response.client_response
        return [output.model_dump(mode="json", exclude={"status"}) for output in _response.output]

    def format_tool_results(self, agents: list[ResearchAgent]) -> list[dict]:
        return [
            {
                "type": "function_call_output",
                "call_id": agent.call_id,
                "output": agent.output,
            }
            for agent in agents
        ]


# -------------------------------------------------------------------------------- public methods


async def run_research_agents(
    response: ClientResponse,
    model_tier: ModelTier = ModelTier.FAST,
    reasoning_level: ReasoningLevel = ReasoningLevel.LOW,
    run_id: str | None = None,
) -> tuple[bool, list[dict]]:
    """
    Execute research agents and format results for any provider.

    Args:
        caller_provider: The LLM provider that initiated the research agent run
        response: The client response containing function/tool calls
        model_tier: The model tier to use for the research agents
        reasoning_level: The reasoning level to use for the research agents

    Returns:
        Tuple of (has_tool_calls, intermediate_messages)
    """
    handler = _OpenAIHandler()

    # Create research agents from function calls
    research_agents = [
        ResearchAgent(
            client=get_openai_client(),
            research_topic=call.arguments["research_topic"],
            call_id=call.id,
            run_id=run_id,
        )
        for call in response.function_calls
    ]

    if not research_agents:
        return False, []

    # Build intermediate messages
    intermediate_messages: list[dict] = []

    # Add assistant message if needed (provider-specific)
    assistant_message = handler.format_assistant_message(response)
    if isinstance(assistant_message, list):
        intermediate_messages.extend(assistant_message)
    else:
        intermediate_messages.append(assistant_message)

    # Execute all research agents concurrently
    await asyncio.gather(
        *[agent.search(model_tier=model_tier, reasoning_level=reasoning_level) for agent in research_agents]
    )

    # Format and append tool results (provider-specific)
    tool_results = handler.format_tool_results(research_agents)

    if isinstance(tool_results, list):
        intermediate_messages.extend(tool_results)
    else:
        intermediate_messages.append(tool_results)

    return True, intermediate_messages
