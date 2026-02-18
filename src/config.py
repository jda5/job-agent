import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent

load_dotenv(ROOT.parent / ".env")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
