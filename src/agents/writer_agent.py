from clients.openai_client import OpenAIClient
from controllers.project_controller import ProjectController
from models.agent_models import ModelTier, ReasoningLevel
from utils.file_utils import STRATEGY_BRIEF_FILENAME, load_prompt
from utils.logging_utils import create_logger


class WriterAgent:
    """
    Agent responsible for writing a tailored job application (cover letter, resume, etc.)
    based on the strategic brief and research findings provided by the Strategy Orchestration Agent.
    """

    _logger = create_logger("✍️ Writer Agent")

    SYSTEM_PROMPT = load_prompt("writer_agent_system_prompt.txt")

    def __init__(self, client: OpenAIClient):
        self.client = client

    # -------------------------------------------------------------------------------- private methods

    @staticmethod
    def _format_user_message(project: ProjectController) -> str:
        """
        Formats the initial user message, injecting the candidate's CV, job details,
        and clear instructions on the expected output.
        """
        context = "\n\n".join(project.load_context())

        strategy_brief = project.load_output(STRATEGY_BRIEF_FILENAME)

        return f"""
Please write a tailored job application based on the following context and strategic brief.
        
## CONTEXT FILES
{context}

## STRATEGIC BRIEF

{strategy_brief}
""".strip()

    async def run(self, project: ProjectController, run_id: str | None = None) -> str | None:
        """ """

        try:
            response = await self.client.generate_response(
                model_tier=ModelTier.POWERFUL,
                messages=[
                    {
                        "role": "user",
                        "content": self._format_user_message(project),
                    }
                ],
                system_prompt=self.SYSTEM_PROMPT,
                reasoning_level=ReasoningLevel.MEDIUM,
                run_id=run_id,
            )
            project.save_output("writer-agent-output.txt", response.output_text)
            return response.output_text

        except RuntimeError:
            return None
