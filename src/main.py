from uuid import uuid4

from agents.strategy_orchestration_agent import StrategyOrchestrationAgent
from agents.writer_agent import WriterAgent
from clients.openai_client import OpenAIClient
from controllers.project_controller import ProjectController
from controllers.usage_tracker import UsageTracker


async def main():

    usage_tracker = UsageTracker()
    openai_client = OpenAIClient(usage_tracker)

    orchestration_agent = StrategyOrchestrationAgent(openai_client)
    writer_agent = WriterAgent(openai_client)

    project_controller = ProjectController("mthree")
    run_id = uuid4().hex

    response = await orchestration_agent.run(project_controller, run_id)
    response = await writer_agent.run(project_controller, run_id)
    if response is None:
        print("Writer Agent failed to generate a response.")
        return

    print("=== WRITER AGENT RESPONSE ===")
    print(response.model_dump_json(indent=2))

    print()
    print(f"Cost: ${usage_tracker.get_run_cost(run_id):.4f}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
