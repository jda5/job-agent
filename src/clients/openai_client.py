import json
from asyncio import sleep
from typing import Type

import openai
from openai import APIConnectionError, APIError, Omit, RateLimitError, omit
from openai.types.responses import Response
from openai.types.shared_params.reasoning import Reasoning

from config import OPENAI_API_KEY
from controllers.usage_tracker import UsageTracker
from models.agent_models import (
    ClientResponse,
    FunctionCall,
    ModelTier,
    ReasoningLevel,
    ResponseFormatT,
)
from tools import get_tools
from utils import calculate_delay, create_logger

ONE_MILLION = 1_000_000


class OpenAIClient:
    """
    Client for interacting with OpenAI's API.
    """

    _logger = create_logger("🤖 OpenAI Client")

    MAX_RETRIES = 3

    MODEL_MAP = {
        ModelTier.FAST: "gpt-5-nano-2025-08-07",
        ModelTier.BALANCED: "gpt-5-mini-2025-08-07",
        ModelTier.POWERFUL: "gpt-5.2-2025-12-11",
    }

    MODEL_PRICING = {
        "gpt-5.2-2025-12-11": {
            "input": 1.75 / ONE_MILLION,
            "output": 14 / ONE_MILLION,
        },
        "gpt-5-mini-2025-08-07": {
            "input": 0.25 / ONE_MILLION,
            "output": 2 / ONE_MILLION,
        },
        "gpt-5-nano-2025-08-07": {
            "input": 0.05 / ONE_MILLION,
            "output": 0.40 / ONE_MILLION,
        },
    }

    # map our ReasoningLevel to OpenAI's expected strings
    REASONING_MAP = {
        ReasoningLevel.LOW: "low",
        ReasoningLevel.MEDIUM: "medium",
        ReasoningLevel.HIGH: "high",
    }

    def __init__(self, usage_tracker: UsageTracker):
        self.usage_tracker = usage_tracker
        self._client = openai.AsyncClient(api_key=OPENAI_API_KEY)

    # -------------------------------------------------------------------------------- private methods

    def _format_reasoning_level(self, reasoning_level: ReasoningLevel | None) -> Reasoning | Omit:
        if reasoning_level:
            return Reasoning(effort=self.REASONING_MAP[reasoning_level])  # type: ignore
        return omit

    def _format_response(self, response: Response) -> ClientResponse:
        function_calls = []
        text_outputs = []

        for item in response.output:
            if item.type == "function_call":
                args = json.loads(item.arguments)
                function_calls.append(
                    FunctionCall(
                        id=item.call_id,
                        name=item.name,
                        arguments=args,
                    )
                )

            elif item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        text_outputs.append(content.text)

        return ClientResponse(
            text_outputs=text_outputs,
            function_calls=function_calls,
            client_response=response,
        )

    def _track_usage(self, run_id: str | None, response: Response) -> None:
        if run_id:
            model_name = response.model
            pricing = self.MODEL_PRICING.get(model_name)
            if not pricing:
                self._logger.warning(
                    "No pricing information found for model %s. Usage not tracked.",
                    model_name,
                )
                return

            if response.usage is None:
                self._logger.warning(
                    "No usage information found in response for model %s. Usage not tracked.",
                    model_name,
                )
                return

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            amount = pricing["input"] * input_tokens + pricing["output"] * output_tokens
            self.usage_tracker.add_usage(run_id=run_id, amount=amount)

    # -------------------------------------------------------------------------------- public methods

    async def generate_response(
        self,
        *,
        messages: list[dict[str, str]] | str,
        system_prompt: str | None = None,
        model_tier: ModelTier = ModelTier.BALANCED,
        reasoning_level: ReasoningLevel | None = None,
        tools: list[str] | None = None,
        tool_choice: str | None = None,
        run_id: str | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a response from OpenAI.

        Returns the native OpenAI Response object for backward compatibility.
        """
        _tools = get_tools(tools or [])

        last_error: APIError | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.responses.create(
                    model=self.MODEL_MAP[model_tier],
                    input=messages,
                    instructions=system_prompt or omit,
                    tools=_tools or omit,
                    tool_choice={"type": "function", "name": tool_choice} if tool_choice else omit,
                    reasoning=self._format_reasoning_level(reasoning_level),
                    **kwargs,
                )
                self._track_usage(run_id=run_id, response=response)
                return self._format_response(response)

            except (APIError, APIConnectionError, RateLimitError) as e:
                last_error = e
                self._logger.error("Error during OpenAI API call: %s", e, exc_info=True)

            # check if we've exhausted all retries
            if attempt >= self.MAX_RETRIES - 1:
                break

            # calculate delay with exponential backoff and wait before retrying
            delay = calculate_delay(attempt)
            self._logger.warning("Retrying after %.2f seconds...", delay)
            await sleep(delay)

        raise RuntimeError(
            f"failed to generate text response after {self.MAX_RETRIES} attempts. Last error: {last_error}"
        )

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, str]] | str,
        output_schema: Type[ResponseFormatT],
        system_prompt: str | None = None,
        model_tier: ModelTier = ModelTier.BALANCED,
        reasoning_level: ReasoningLevel | None = None,
        run_id: str | None = None,
        **kwargs,
    ) -> ResponseFormatT:
        """
        Generate a structured response from the OpenAI API.

        Sends a request to OpenAI's API and parses the response into the
        specified output schema. Automatically retries on transient failures
        with exponential backoff.

        Args:
            messages: List of message dicts with "role" and "content" keys.
                Or a single string user message.
            output_schema: A Pydantic model or TypedDict class defining the
                expected response structure.
            system_prompt: Optional system-level instructions for the model.
            model_tier: The model tier to use (FAST, BALANCED, or POWERFUL).
                Defaults to BALANCED.
            reasoning_level: Optional reasoning effort level (LOW, MEDIUM, HIGH).
                If None, reasoning is omitted from the request.
            **kwargs: Additional arguments passed directly to the OpenAI API.

        Returns:
            The parsed response matching the output_schema type.

        Raises:
            RuntimeError: If all retry attempts are exhausted.
        """
        last_error: APIError | None = None

        self._logger.debug(
            "Generating structured output with model tier: %s, reasoning level: %s - Messages:\n\n%s",
            model_tier,
            reasoning_level,
            messages,
        )

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.responses.parse(
                    model=self.MODEL_MAP[model_tier],
                    input=messages,
                    instructions=system_prompt or omit,
                    reasoning=self._format_reasoning_level(reasoning_level),
                    text_format=output_schema,
                    **kwargs,
                )
                self._track_usage(run_id=run_id, response=response)
                if response.output_parsed is None:
                    raise RuntimeError("Received response with no parsable output")

                return response.output_parsed

            except (APIError, APIConnectionError, RateLimitError) as e:
                last_error = e
                self._logger.warning(
                    "API error on attempt %d/%d: %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    e,
                )

            # check if we've exhausted all retries
            if attempt >= self.MAX_RETRIES - 1:
                break

            # calculate delay with exponential backoff and wait before retrying
            delay = calculate_delay(attempt)
            self._logger.warning("Retrying after %.2f seconds...", delay)
            await sleep(delay)

        raise RuntimeError(
            f"failed to generate structured output after {self.MAX_RETRIES} attempts. Last error: {last_error}"
        )
