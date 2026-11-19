"""Deterministic checks for cover letters, used by the QA fact-checker.

Only the letter itself is checked: the "Notities voor Tim" below the first `---`
line are not part of what gets sent (same rule as tools.letter_docx).
Letters are written in the recipient's language, so the language is detected
and the Dutch-only checks (known typos) are skipped for English letters.
"""

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
NOTES_SEPARATOR = "---"
DUTCH_MARKERS = {"de", "het", "een", "en", "ik", "van", "mijn", "niet", "zijn", "met", "voor", "ben"}
ENGLISH_MARKERS = {"the", "a", "and", "i", "of", "my", "not", "is", "with", "for", "am", "to"}
AGE_PATTERNS = {
    "nl": re.compile(r"\b(\d{2}) jaar\b"),
    "en": re.compile(r"\b(\d{2})(?:-year-old| years? old)\b", re.IGNORECASE),
}


class LetterReport(BaseModel):
    language: str
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


def letter_part(markdown: str) -> str:
    """Everything above the first `---` line: the text that is actually sent."""
    lines = []
    for line in markdown.splitlines():
        if line.strip() == NOTES_SEPARATOR:
            break
        lines.append(line)
    return "\n".join(lines)


def detect_language(text: str) -> str:
    words = re.findall(r"[a-z]+", text.lower())
    dutch = sum(w in DUTCH_MARKERS for w in words)
    english = sum(w in ENGLISH_MARKERS for w in words)
    return "en" if english > dutch else "nl"


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
    text = letter_part(text)
    lower = text.lower()
    language = detect_language(text)
    words = count_words(text)
    stated_ages = [int(a) for a in AGE_PATTERNS[language].findall(text)]
    typos = KNOWN_TYPOS if language == "nl" else {}
    return LetterReport(
        language=language,
        word_count=words,
        length_ok=MIN_WORDS <= words <= MAX_WORDS,
        typos=[f"{wrong} -> {right}" for wrong, right in typos.items() if wrong in lower],
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
