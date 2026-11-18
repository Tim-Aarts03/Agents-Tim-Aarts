"""Turn an approved cover letter (Markdown in /output) into a Word file Tim can send.

Only the letter itself is exported: everything from the first `---` line onwards
("Notities voor Tim") stays in the Markdown file.
"""

import sys
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

NOTES_SEPARATOR = "---"
FONT_NAME = "Calibri"
FONT_SIZE_PT = 11
MARGIN_CM = 2.5


def letter_paragraphs(markdown: str) -> list[list[str]]:
    """Paragraphs of the letter (blank-line separated); each keeps its own line breaks (e.g. signature)."""
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if line == NOTES_SEPARATOR:
            break
        if not line:
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append(line.replace("**", ""))
    if current:
        paragraphs.append(current)
    return paragraphs


def build_document(paragraphs: list[list[str]]) -> Document:
    doc = Document()
    for section in doc.sections:
        section.page_height, section.page_width = Cm(29.7), Cm(21.0)  # A4
        section.top_margin = section.bottom_margin = Cm(MARGIN_CM)
        section.left_margin = section.right_margin = Cm(MARGIN_CM)
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(FONT_SIZE_PT)
    style.paragraph_format.space_after = Pt(10)
    style.paragraph_format.line_spacing = 1.15
    for lines in paragraphs:
        paragraph = doc.add_paragraph()
        for i, line in enumerate(lines):
            run = paragraph.add_run(line)
            if i < len(lines) - 1:
                run.add_break()
    return doc


def export_letter(markdown_path: Path, docx_path: Path | None = None) -> Path:
    paragraphs = letter_paragraphs(markdown_path.read_text(encoding="utf-8"))
    if not paragraphs:
        raise ValueError(f"No letter text found in {markdown_path}")
    target = docx_path or markdown_path.with_suffix(".docx")
    build_document(paragraphs).save(target)
    return target


def main() -> None:
    """CLI: python -m tools.letter_docx output/career/letter_<org>_<date>.md [more.md ...]"""
    if len(sys.argv) < 2:
        sys.exit("usage: python -m tools.letter_docx <letter.md> [<letter.md> ...]")
    for name in sys.argv[1:]:
        print(export_letter(Path(name)))


if __name__ == "__main__":
    main()
