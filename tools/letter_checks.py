"""Deterministic checks for cover letters, used by the QA fact-checker."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pydantic import BaseModel

MIN_WORDS = 250
MAX_WORDS = 400
STYLE_GUIDE = Path("knowledge/letter_style.md")
PROFILE = Path("knowledge/profile.md")

# Known spelling mistakes from Tim's earlier letters: wrong -> right.
KNOWN_TYPOS: dict[str, str] = {
    "hard sneller": "hart sneller",
    "hield ik geld op": "haalde ik geld op",
    "opzoek": "op zoek",
    "doormiddel": "door middel",
    "buiteland": "buitenland",
}
PLACEHOLDER = re.compile(r"\[[^\]]+\]")


class LetterReport(BaseModel):
    word_count: int
    length_ok: bool
    typos: list[str]
    banned_phrases: list[str]
    wrong_age: bool
    placeholders: list[str]

    @property
    def passed(self) -> bool:
        return self.length_ok and not self.typos and not self.banned_phrases and not self.wrong_age


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def load_banned_phrases(style_guide: Path = STYLE_GUIDE) -> list[str]:
    """Read bullet lines under the '## Banned phrases' heading."""
    if not style_guide.exists():
        return []
    phrases: list[str] = []
    in_section = False
    for line in style_guide.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## banned phrases"
            continue
        if in_section and line.startswith("- "):
            phrases.append(line[2:].strip().strip('"'))
    return phrases


def load_age(profile: Path = PROFILE) -> int | None:
    if not profile.exists():
        return None
    match = re.search(r"Age:\s*(\d+)", profile.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else None


def check_letter(text: str, banned_phrases: list[str], age: int | None) -> LetterReport:
    lower = text.lower()
    words = count_words(text)
    stated_ages = [int(a) for a in re.findall(r"\b(\d{2}) jaar\b", text)]
    return LetterReport(
        word_count=words,
        length_ok=MIN_WORDS <= words <= MAX_WORDS,
        typos=[f"{wrong} -> {right}" for wrong, right in KNOWN_TYPOS.items() if wrong in lower],
        banned_phrases=[p for p in banned_phrases if p.lower() in lower],
        wrong_age=age is not None and any(a != age for a in stated_ages),
        placeholders=PLACEHOLDER.findall(text),
    )


def main() -> None:
    """CLI: `python -m tools.letter_checks output/career/letter.md`"""
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    report = check_letter(text, load_banned_phrases(), load_age())
    print(report.model_dump_json(indent=2))
    print("PASSED" if report.passed else "FAILED")


if __name__ == "__main__":
    main()
