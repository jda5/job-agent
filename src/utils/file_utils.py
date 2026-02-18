import json

from config import ROOT


def load_prompt(filename: str) -> str:
    filepath = ROOT / "prompts" / filename
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read().strip()


def load_output(project_name: str, filename: str) -> dict:
    filepath = ROOT.parent / "projects" / project_name / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
