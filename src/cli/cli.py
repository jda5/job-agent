"""
Job Agent CLI — interactive interface for running the job application pipeline.
"""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

from agents.strategy_orchestration_agent import StrategyOrchestrationAgent
from agents.writer_agent import WriterAgent
from clients.openai_client import OpenAIClient
from controllers.project_controller import (
    APPLICATION_RESPONSE_FILENAME,
    ProjectController,
)
from controllers.usage_tracker import UsageTracker

console = Console()

# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────


def display_header() -> None:
    console.print()
    console.print(
        Panel.fit(
            "[bold white]Job Application Agent[/bold white]\n"
            "[dim]AI-powered research and writing for job applications[/dim]",
            border_style="bright_blue",
            padding=(1, 4),
        )
    )
    console.print()


def _status(msg: str) -> None:
    console.print(f"  [dim]{msg}[/dim]")


def _success(msg: str) -> None:
    console.print(f"  [green]✓[/green] {msg}")


def _info(msg: str) -> None:
    console.print(f"  [bright_blue]→[/bright_blue] {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow] {msg}")


def _section(title: str) -> None:
    console.print()
    console.print(Rule(f"[bold]{title}[/bold]", style="bright_blue"))
    console.print()


# -------------------------------------------------------------------------------- project selection


def get_or_create_project() -> ProjectController:
    _section("Project")

    project_name = Prompt.ask("  [bold]Project name[/bold]").strip().lower()

    # Check existence before the controller creates the directories
    projects_root = Path(__file__).parent.parent.parent / "projects"
    is_new = not (projects_root / project_name).exists()

    project = ProjectController(project_name)

    if is_new:
        _success(f"Created new project [bold]{project_name}[/bold]")
    else:
        _success(f"Loaded existing project [bold]{project_name}[/bold]")

    return project


# -------------------------------------------------------------------------------- job description


def _read_multiline(prompt_text: str) -> str:
    """
    Collect pasted / typed multi-line text; an empty line signals the end.
    """
    console.print(f"  [bold]{prompt_text}[/bold]")
    console.print("  [dim](Press Enter on a blank line when done)[/dim]")
    lines: list[str] = []
    while True:
        try:
            line = input("  ")
        except EOFError:
            break
        if line == "" and lines and lines[-1] == "":
            # Two blank lines in a row → done; strip the trailing blank
            lines.pop()
            break
        lines.append(line)
    return "\n".join(lines).strip()


def setup_job_description(project: ProjectController) -> None:
    if project.has_job_description():
        _info("Job description already on file — skipping setup.")
        return

    _section("Job Description")

    url = Prompt.ask(
        "  [bold]Job posting URL[/bold] [dim](optional, press Enter to skip)[/dim]",
        default="",
    ).strip()

    console.print()
    description = _read_multiline("Paste the job description:")

    if not description:
        _warn("No description entered — you can add one later by editing the context file.")
        return

    job_desc_path = project.get_job_description_path()

    content_lines = ["# Job URL", url or "N/A", "", "# Job Description", description]
    job_desc_path.write_text("\n".join(content_lines), encoding="utf-8")

    _success(f"Job description saved to [dim]{job_desc_path.name}[/dim]")


# -------------------------------------------------------------------------------- application questions


def _job_desc_has_questions(project: ProjectController) -> bool:
    path = project.get_job_description_path()
    if not path.exists():
        return False
    return "# Application Questions" in path.read_text(encoding="utf-8")


def _append_questions(project: ProjectController, questions: list[str]) -> None:
    path = project.get_job_description_path()
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    block = f"\n\n# Application Questions\n{numbered}"

    path.write_text(existing + block, encoding="utf-8")


def _overwrite_questions(project: ProjectController, questions: list[str]) -> None:
    """Replace the existing Application Questions section."""
    path = project.get_job_description_path()
    text = path.read_text(encoding="utf-8") if path.exists() else ""

    # Drop everything from the section header onwards
    marker = "# Application Questions"
    idx = text.find(marker)
    base = text[:idx].rstrip() if idx != -1 else text

    numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    path.write_text(base + f"\n\n# Application Questions\n{numbered}", encoding="utf-8")


def collect_questions(project: ProjectController, overwrite: bool = False) -> None:
    """Prompt the user to enter application-specific questions."""
    if not overwrite and _job_desc_has_questions(project):
        _info("Application questions already recorded — skipping.")
        return

    _section("Application Questions")

    has_questions = Confirm.ask(
        "  Does this application include specific questions to answer?",
        default=False,
    )
    if not has_questions:
        _info("No questions added.")
        return

    questions: list[str] = []
    console.print("  [dim]Enter one question per line. Leave blank to finish.[/dim]")
    console.print()

    while True:
        n = len(questions) + 1
        try:
            q = input(f"  Question {n}: ").strip()
        except EOFError:
            break
        if not q:
            break
        questions.append(q)

    if not questions:
        _info("No questions entered.")
        return

    if overwrite:
        _overwrite_questions(project, questions)
    else:
        _append_questions(project, questions)

    _success(f"Saved {len(questions)} question(s).")


# -------------------------------------------------------------------------------- results display


def view_results(project: ProjectController) -> None:
    _section("Application Results")

    try:
        raw = project.load_output(APPLICATION_RESPONSE_FILENAME)
        data = json.loads(raw)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        _warn(f"Could not load results: {e}")
        return

    # ── Plain text output (no rich markup) so it's easy to copy ────────────
    print()
    print("COVER LETTER")
    print("=" * 60)
    print(data.get("cover_letter", ""))
    print()

    question_answers: list[dict] = data.get("question_answers", [])
    if question_answers:
        print("APPLICATION QUESTIONS")
        print("=" * 60)
        for i, qa in enumerate(question_answers, 1):
            print(f"Q{i}: {qa.get('question', '')}")
            print()
            print(qa.get("answer", ""))
            print()

    input("  Press Enter to return to the menu...")

    # -------------------------------------------------------------------------------- agent execution


async def _run_agents_async(project: ProjectController) -> float | None:
    usage_tracker = UsageTracker()
    openai_client = OpenAIClient(usage_tracker)
    orchestration_agent = StrategyOrchestrationAgent(openai_client)
    writer_agent = WriterAgent(openai_client)
    run_id = uuid4().hex

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("  Researching company and strategy...", total=None)
        await orchestration_agent.run(project, run_id)

        progress.update(task, description="  Writing your application...")
        result = await writer_agent.run(project, run_id)

    if result is None:
        _warn("Writer agent returned no output — check logs for details.")
        return None

    return usage_tracker.get_run_cost(run_id)


def run_agents(project: ProjectController) -> None:
    _section("Running Agents")

    try:
        cost = asyncio.run(_run_agents_async(project))
    except RuntimeError as e:
        console.print(
            Panel(
                f"[red]Agent run failed:[/red]\n{e}",
                title="Error",
                border_style="red",
            )
        )
        return

    if cost is not None:
        _success(f"Done!  Run cost: [bold]${cost:.4f}[/bold]")
    else:
        _success("Done!")


# -------------------------------------------------------------------------------- main menu


def show_main_menu(project: ProjectController) -> None:
    while True:
        _section("Main Menu")

        has_results = project.has_results()
        has_strategy = project.has_strategy_brief()

        # Build menu dynamically based on project state
        options: list[tuple[str, str]] = []

        if has_results:
            options.append(("view", "View application results"))

        run_label = "Re-run agents" if (has_results or has_strategy) else "Run agents"
        options.append(("run", run_label))

        options.append(("questions", "Edit application questions"))
        options.append(("exit", "Exit"))

        # Print menu
        for i, (_, label) in enumerate(options, 1):
            console.print(f"  [bold bright_blue]{i}[/bold bright_blue]  {label}")

        # Show state summary in dim text
        console.print()
        if has_results:
            _status("Results available")
        elif has_strategy:
            _status("Strategy brief ready — writer not yet run")
        else:
            _status("No output generated yet")

        console.print()
        choice = Prompt.ask(
            "  [bold]Choose[/bold]",
            choices=[str(i) for i in range(1, len(options) + 1)],
        )

        action, _ = options[int(choice) - 1]

        if action == "view":
            view_results(project)

        elif action == "run":
            if has_results or has_strategy:
                confirmed = Confirm.ask(
                    "  This will overwrite existing output. Continue?",
                    default=False,
                )
                if not confirmed:
                    continue
            run_agents(project)

        elif action == "questions":
            collect_questions(project, overwrite=True)

        elif action == "exit":
            console.print()
            _info("Goodbye!")
            console.print()
            break


# -------------------------------------------------------------------------------- entry point


def cli() -> None:
    display_header()
    project = get_or_create_project()
    setup_job_description(project)
    collect_questions(project)
    show_main_menu(project)


if __name__ == "__main__":
    cli()
