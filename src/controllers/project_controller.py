from pathlib import Path
from typing import Generator

from config import ROOT
from utils.file_utils import APPLICATION_RESPONSE_FILENAME, STRATEGY_BRIEF_FILENAME


class ProjectController:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_root = ROOT.parent / "projects" / project_name
        self.default_dir = ROOT.parent / "projects" / "_default"
        self.output_dir = self.project_root / "output"
        self.context_dir = self.project_root / "context"
        self._initialize_project_structure()

    # -------------------------------------------------------------------------------- private methods

    def _initialize_project_structure(self) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_content(self, filename: str, content: str) -> str:
        return f"<{filename}>\n{content.strip()}\n</{filename}>"

    # -------------------------------------------------------------------------------- public methods

    def load_candidate_files(self) -> Generator[str, None, None]:
        """
        Loads the candidate's files (CV etc.) from the shared `_default` directory,
        yielding their content formatted with filename tags.
        """
        for file in self.default_dir.glob("*"):
            if file.is_file():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                yield self._format_content(file.name, content)

    def load_job_files(self) -> Generator[str, None, None]:
        """
        Loads the job's files (description, questions) from the project's context
        directory, yielding their content formatted with filename tags.
        """
        for file in self.context_dir.glob("*"):
            if file.is_file():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                yield self._format_content(file.name, content)

    def load_output(self, filename: str) -> str:
        """
        Loads a specific file from the project's output directory.
        """
        output_file = self.output_dir / filename
        if not output_file.exists():
            raise FileNotFoundError(f"Output file '{filename}' not found in project '{self.project_name}'.")

        with open(output_file, "r", encoding="utf-8") as f:
            return f.read()

    def save_output(self, filename: str, content: str) -> None:
        output_file = self.output_dir / filename
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

    def has_job_description(self) -> bool:
        return self.context_dir.exists() and any(self.context_dir.iterdir())

    def has_results(self) -> bool:
        return (self.output_dir / APPLICATION_RESPONSE_FILENAME).exists()

    def has_strategy_brief(self) -> bool:
        return (self.output_dir / STRATEGY_BRIEF_FILENAME).exists()

    def get_job_description_path(self) -> Path:
        return self.context_dir / f"{self.project_name}-job-description.txt"
