"""Load prompt text from the repo ``prompts/`` directory."""

from pathlib import Path


def load_prompt(name: str) -> str:
    here = Path(__file__).resolve()
    for parent in here.parents:
        path = parent / "prompts" / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(name)
