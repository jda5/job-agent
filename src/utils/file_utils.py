from config import ROOT

APPLICATION_RESPONSE_FILENAME = "application-responses.json"
JOB_DESCRIPTION_FILENAME = "job-description.txt"
STRATEGY_BRIEF_FILENAME = "strategy-brief.txt"


def load_prompt(filename: str) -> str:
    """
    Loads a prompt template from the prompts directory.
    """
    filepath = ROOT / "prompts" / filename
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read().strip()
