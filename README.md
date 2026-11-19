# Job Agent

🤖 Readme written by Claude, code mostly written by me 🙋‍♂️

A small command-line tool that drafts job applications. Give it your CV and a job description, and it researches the company, works out an angle, and writes a cover letter plus answers to any application questions.

## How it works

1. **Strategy agent** reads your CV and the job description, then sends research sub-agents to search the web for relevant facts about the company.
2. It condenses what they find into a short strategy brief.
3. **Writer agent** uses the brief, your CV and the job description to draft the cover letter and question answers.

It uses the OpenAI API, and prints the cost of each run when it finishes.

## Setup

You need an [OpenAI API key](https://platform.openai.com/api-keys) and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # then add your key
mkdir -p projects/_default
```

On macOS you can run `./install.sh` instead, which does all of the above (and installs uv if it's missing).

Then put your CV, and anything else that describes you (LinkedIn export, past applications), in `projects/_default/` as plain text files. Everything in that folder is sent to the model as candidate background for every application.

## Usage

```bash
uv run src/main.py
```

Or double-click `Launch Job Agent.command` on macOS.

You'll be asked for a project name (one per application), the job description, and any application questions. Then choose **Run agents** from the menu.

Each project gets its own folder:

```
projects/
├── _default/              # your CV etc., shared by all projects
└── <project-name>/
    ├── context/           # job description and questions
    └── output/            # strategy-brief.txt, application-responses.json
```

`projects/` is git-ignored, since it holds personal data.

## Notes

- The models used and their prices are set in `src/clients/openai_client.py`.
- The prompts live in `src/prompts/` and are worth tweaking: they currently assume UK applications.
- Always read the output before sending it. The writer is told not to invent experience, but check anyway.
