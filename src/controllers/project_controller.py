from typing import Generator

from config import ROOT


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
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        print(self.output_dir)

    def _format_context(self, filename: str, content: str) -> str:
        return f"<{filename}>\n{content.strip()}\n</{filename}>"

    # -------------------------------------------------------------------------------- public methods

    def load_files(self) -> Generator[str, None, None]:
        for path in [self.context_dir, self.default_dir]:
            for file in path.glob("*"):
                if file.is_file():
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                    yield self._format_context(file.name, content)

    def save_output(self, filename: str, content: str) -> None:
        output_file = self.output_dir / filename
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
