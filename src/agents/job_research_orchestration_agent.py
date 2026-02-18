"""
Orchestrates multi-turn research to identify high-probability target segments
for cold email campaigns based on company information.
"""

import json

from clients.openai_client import OpenAIClient
from models.agent_models import ModelTier, ReasoningLevel
from utils.file_utils import load_prompt
from utils.logging_utils import create_logger
from utils.research_agent_utils import run_research_agents


class JobResearchOrchestrationAgent:
    """ """

    _logger = create_logger("Job Research Orchestration Agent")

    MIN_TURNS = 2
    MAX_TURNS = 5

    SYSTEM_PROMPT = load_prompt("job_research_orchestration_agent.txt")

    def __init__(self, client: OpenAIClient):
        self._client = client

    # -------------------------------------------------------------------------------- private methods

    @staticmethod
    def _format_user_message(company_info: str) -> str:
        """
        Format the initial user message with company context.
        """
        return f"""
I am about to launch a cold lead generation campaign.
Based on the extracted offering information below, identify the Best-Fit Target Segments.

# Offering

{company_info}
""".strip()

    def _log_messages(self, messages: list[dict]) -> None:
        """
        Log the current conversation history for debugging.
        """
        formatted = "\n\n----------------------------------------\n\n".join(
            json.dumps(msg, indent=2) for msg in messages
        )
        self._logger.debug(
            "Current conversation messages:\n\n"
            "========================================\n\n"
            "%s\n\n"
            "========================================\n\n",
            formatted,
        )

    # -------------------------------------------------------------------------------- public methods

    async def run(self, run_id: str | None = None) -> str:
        """ """
        self._logger.debug("Starting Job Research Orchestration Agent with run_id=%s", run_id)

        messages = [
            {
                "role": "user",
                "content": self._format_user_message(offering),
            }
        ]

        for turn in range(self.MAX_TURNS):
            self._logger.debug("Starting turn %d of ICP analysis.", turn + 1)

            response = await self._client.generate_response(
                system_prompt=self.SYSTEM_PROMPT,
                messages=messages,
                model_tier=ModelTier.POWERFUL,
                reasoning_level=ReasoningLevel.MEDIUM,
                tools=["perform_research"],
                run_id=run_id,
            )

            self._logger.debug("Received response from turn %d of ICP analysis.", turn + 1)

            function_call, agent_responses = await run_research_agents(
                response=response,
                model_tier=ModelTier.BALANCED,
                reasoning_level=ReasoningLevel.MEDIUM,
                run_id=run_id,
            )

            # No function call means the agent wants to complete
            if not function_call:
                if turn < self.MIN_TURNS - 1:
                    # Force continuation to ensure analysis depth
                    messages.extend(
                        [
                            {"role": "assistant", "content": response.output_text},
                            {
                                "role": "user",
                                "content": "Continue your analysis independently. Do not ask me for input.",
                            },
                        ]
                    )
                    self._logger.debug(
                        "Turn %d did not yield a function call. Continuing to next turn.",
                        turn + 1,
                    )
                    continue

                self._logger.debug(
                    "ICP analysis complete after turn %d. Response:\n\n%s\n",
                    turn + 1,
                    response.output_text,
                )
                return response.output_text

            messages.extend(agent_responses)
            self._logger.debug("Turn %d/%d complete.", turn + 1, self.MAX_TURNS)

        # Max turns reached, generate final response without tools
        response = await self._client.generate_response(
            system_prompt=self.SYSTEM_PROMPT,
            messages=messages,
            model_tier=ModelTier.POWERFUL,
            reasoning_level=ReasoningLevel.MEDIUM,
            run_id=run_id,
        )

        self._logger.debug("ICP analysis complete after max turns.")
        return response.output_text
