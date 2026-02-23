from clients.openai_client import OpenAIClient
from controllers.project_controller import ProjectController
from models.agent_models import ClientResponse, ModelTier, ReasoningLevel
from utils.file_utils import STRATEGY_BRIEF_FILENAME, load_prompt
from utils.logging_utils import create_logger
from utils.research_agent_utils import run_research_agents


class StrategyOrchestrationAgent:
    """
    Orchestrates the research phase of the job application process.
    Delegates targeted research tasks to sub-agents and synthesizes their
    findings into a Strategic Brief for downstream Writer Agents.
    """

    _logger = create_logger("🧠 Orchestration Agent")

    MIN_RESEARCH_TURNS = 1
    MAX_RESEARCH_TURNS = 3
    SYSTEM_PROMPT = load_prompt("strategy_orchestration_agent.txt")

    def __init__(self, client: OpenAIClient):
        self._client = client

    # -------------------------------------------------------------------------------- private methods

    @staticmethod
    def _format_user_message(project: ProjectController) -> str:
        """
        Formats the initial user message, injecting the candidate's CV, job details,
        and clear instructions on the expected output.
        """
        context = "\n\n".join(project.load_context())

        return f"""
Please review the following context files containing my CV, the job description, and supporting information.

Your objective is twofold:
1. PHASE 1: Delegate targeted research to uncover deep, actionable insights about the company that align with my background.
2. PHASE 2: Synthesize those findings into a Strategic Brief that provides distinct angles and contextual ammunition for the downstream writer agents.

Do not write the application yourself. Focus purely on research and strategy.

### CONTEXT FILES ###
{context}
""".strip()

    def _format_response(self, project: ProjectController, response: ClientResponse) -> str:
        project.save_output(STRATEGY_BRIEF_FILENAME, response.output_text)
        return response.output_text

    # -------------------------------------------------------------------------------- public methods

    async def run(self, project: ProjectController, run_id: str | None = None) -> str:
        """
        Executes the agent loop, managing tool calls to research sub-agents
        until sufficient context is gathered or the maximum turn limit is reached.
        """
        self._logger.debug(
            "Starting orchestration run for project '%s' (run_id: %s)",
            project.project_name,
            run_id,
        )

        messages = [
            {
                "role": "user",
                "content": self._format_user_message(project),
            }
        ]

        for turn in range(self.MAX_RESEARCH_TURNS):
            self._logger.debug(
                "Turn %d of %d — sending request to model...", turn + 1, self.MAX_RESEARCH_TURNS
            )

            response = await self._client.generate_response(
                system_prompt=self.SYSTEM_PROMPT,
                messages=messages,
                model_tier=ModelTier.POWERFUL,
                reasoning_level=ReasoningLevel.MEDIUM,
                tools=["perform_research"],
                run_id=run_id,
            )

            # Delegate to sub-agents if the orchestrator decides to use the tool
            function_call, agent_responses = await run_research_agents(
                response=response,
                model_tier=ModelTier.BALANCED,
                reasoning_level=ReasoningLevel.MEDIUM,
                run_id=run_id,
            )

            # If no tool is called, the agent is attempting to finalize its response
            if not function_call:
                # Force continuation if the agent tries to finish before minimum turns are met
                if turn < self.MIN_RESEARCH_TURNS - 1:
                    self._logger.debug(
                        "Tried to wrap up too early (turn %d, minimum is %d) — nudging for more research",
                        turn + 1,
                        self.MIN_RESEARCH_TURNS,
                    )
                    messages.extend(
                        [
                            {"role": "assistant", "content": response.output_text},
                            {
                                "role": "user",
                                "content": "You have not gathered enough information yet. Please use the `perform_research` tool to delegate deeper, more focused research tasks to specialized web-browsing agents before synthesizing your brief.",
                            },
                        ]
                    )
                    continue

                # Minimum turns met; accept the final synthesized response
                self._logger.debug(
                    "Minimum turns satisfied — accepting final synthesis on turn %d", turn + 1
                )
                return self._format_response(project, response)

            self._logger.debug(
                "Model dispatched %d parallel research task(s) — waiting for results...",
                len(response.function_calls),
            )

            # Append tool responses and continue the loop
            messages.extend(agent_responses)
            self._logger.debug("Research results collected — continuing to next turn")

        # Max turns reached, force a final generation without providing tools
        self._logger.debug(
            "Reached the turn limit (%d) — forcing a final synthesis pass without tools",
            self.MAX_RESEARCH_TURNS,
        )
        response = await self._client.generate_response(
            system_prompt=self.SYSTEM_PROMPT,
            messages=messages,
            model_tier=ModelTier.POWERFUL,
            reasoning_level=ReasoningLevel.MEDIUM,
            run_id=run_id,
        )

        # Save the final response for downstream agents and return the output
        self._logger.debug("Saving strategic brief → '%s'", STRATEGY_BRIEF_FILENAME)

        return self._format_response(project, response)
