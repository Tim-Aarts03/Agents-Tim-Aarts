import pytest
from docx import Document

from tools.letter_docx import export_letter, letter_paragraphs

LETTER = """Beste Janine,

Eerste alinea met **nadruk**.
Nog een regel.

Met vriendelijke groet,

Tim Aarts
+31 6 00000000

---
Notities voor Tim: deze mogen niet in Word.
"""


def test_paragraphs_stop_at_notes_and_keep_line_breaks():
    assert letter_paragraphs(LETTER) == [
        ["Beste Janine,"],
        ["Eerste alinea met nadruk.", "Nog een regel."],
        ["Met vriendelijke groet,"],
        ["Tim Aarts", "+31 6 00000000"],
    ]


def test_export_writes_letter_without_notes(tmp_path):
    source = tmp_path / "letter_org_2026-11-18.md"
    source.write_text(LETTER, encoding="utf-8")

    target = export_letter(source)

    assert target == tmp_path / "letter_org_2026-11-18.docx"
    text = "\n".join(p.text for p in Document(target).paragraphs)
    assert "Beste Janine," in text
    assert "Tim Aarts\n+31 6 00000000" in text
    assert "Notities" not in text


def test_export_rejects_empty_letter(tmp_path):
    source = tmp_path / "empty.md"
    source.write_text("---\nOnly notes\n", encoding="utf-8")
    with pytest.raises(ValueError):
        export_letter(source)
