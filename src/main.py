from uuid import uuid4

from agents.strategy_orchestration_agent import StrategyOrchestrationAgent
from clients.openai_client import OpenAIClient
from controllers.project_controller import ProjectController
from controllers.usage_tracker import UsageTracker
from utils.file_utils import STRATEGY_BRIEF_FILENAME


async def main():

    usage_tracker = UsageTracker()
    openai_client = OpenAIClient(usage_tracker)

    orchestration_agent = StrategyOrchestrationAgent(openai_client)

    project_controller = ProjectController("interface")
    run_id = uuid4().hex

    response = await orchestration_agent.run(project_controller, run_id)

    project_controller.save_output(STRATEGY_BRIEF_FILENAME, response)

    print()
    print(f"Cost: ${usage_tracker.get_run_cost(run_id):.4f}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
