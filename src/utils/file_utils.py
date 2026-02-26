from config import ROOT

APPLICATION_RESPONSE_FILENAME = "application_responses.json"
STRATEGY_BRIEF_FILENAME = "strategy_brief.txt"


def load_prompt(filename: str) -> str:
    """
    Loads a prompt template from the prompts directory.
    """
    filepath = ROOT / "prompts" / filename
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read().strip()
