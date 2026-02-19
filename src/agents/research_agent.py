from clients.openai_client import OpenAIClient
from models.agent_models import ModelTier, ReasoningLevel
from utils.file_utils import load_prompt
from utils.logging_utils import create_logger


class ResearchAgent:
    """
    Agent responsible for conducting research on a given topic using the LLM and tools like web search.
    """

    _logger = create_logger("🔬 Research Agent")

    SYSTEM_PROMPT = load_prompt("research_agent_system_prompt.txt")

    def __init__(
        self,
        client: OpenAIClient,
        research_topic: str,
        *,
        call_id: str | None = None,
        run_id: str | None = None,
    ):
        self.client = client
        self.research_topic = research_topic

        self.call_id = call_id
        self.run_id = run_id

        self._agent_output: str | None = None

    async def search(
        self,
        model_tier: ModelTier = ModelTier.FAST,
        reasoning_level: ReasoningLevel = ReasoningLevel.LOW,
    ) -> str:
        """
        Conduct research on the specified topic using the LLM.
        """
        self._logger.debug("Starting web search for: '%s'", self.research_topic)

        try:
            response = await self.client.generate_response(
                model_tier=model_tier,
                messages=[
                    {
                        "role": "user",
                        "content": self._format_user_message(),
                    }
                ],
                system_prompt=self.SYSTEM_PROMPT,
                tools=["web_search"],
                reasoning_level=reasoning_level,
                run_id=self.run_id,
            )

            self._agent_output = response.output_text

            self._logger.debug(
                "Search finished — got %d characters back for topic: '%s'",
                len(self._agent_output),
                self.research_topic,
            )
            return self._agent_output

        except RuntimeError:
            self._logger.error("Search failed for topic: '%s'", self.research_topic)
            self._agent_output = "Error during research. Could not retrieve information."
            return self._agent_output

    def _format_user_message(self) -> str:
        return f"Please search the web for to gather data on the following:\n\n{self.research_topic}"

    @property
    def output(self) -> str:
        """
        Retrieve the research output after the search is complete.
        """
        if self._agent_output is None:
            return "Unable to retrieve response."
        return self._agent_output
