"""
Data models for LLM client responses and configuration.

Defines enums for provider selection and model configuration, plus dataclasses
for representing function calls and unified client responses.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel

# Type variable for Pydantic models used as structured output formats.
ResponseFormatT = TypeVar("ResponseFormatT", bound=BaseModel)


class ModelTier(StrEnum):
    """
    Model capability tiers for cost/performance tradeoffs.

    FAST: Nano/Haiku/Flash models for quick, low-cost responses.
    BALANCED: Mini/Sonnet models for optimal cost-performance ratio.
    POWERFUL: Full/Opus/Pro models for complex reasoning tasks.
    """

    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"


class ReasoningLevel(StrEnum):
    """
    Reasoning budget allocation for extended thinking.

    Controls the token budget for model reasoning:
        LOW=1024, MEDIUM=2048, HIGH=4096 tokens.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FunctionCall:
    """
    Represents a tool/function call from an LLM response.

    Attributes:
        id: Unique identifier for the function call.
        name: Name of the function to invoke.
        arguments: Parsed arguments dictionary for the function.
    """

    id: str
    name: str
    arguments: dict


@dataclass
class ClientResponse:
    """
    Unified response wrapper for all LLM providers.

    Attributes:
        text_outputs: List of text content blocks from the response.
        function_calls: List of tool calls requested by the model.
        client_response: Raw provider-specific response object.
    """

    text_outputs: list[str]
    function_calls: list[FunctionCall]
    client_response: object

    @property
    def output_text(self) -> str:
        """
        Returns all text outputs joined as a single string.
        """
        return " ".join(self.text_outputs)
