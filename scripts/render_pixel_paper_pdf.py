"""Render POCKET Pixel Translator full paper to PDF + notes copies."""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

md_path = Path(__file__).resolve().parents[1] / "docs" / "research" / "POCKET_PIXEL_TRANSLATOR_FULL_PAPER.md"
text = md_path.read_text(encoding="utf-8")

notes_dirs = [
    Path.home() / "OneDrive" / "Documents" / "POCKET_Notes",
    Path(__file__).resolve().parents[1] / "docs" / "research",
    Path.home() / ".pocket" / "notes",
]
for d in notes_dirs:
    d.mkdir(parents=True, exist_ok=True)

for d in (notes_dirs[0], notes_dirs[2]):
    (d / "POCKET_PIXEL_TRANSLATOR_FULL_PAPER.md").write_text(text, encoding="utf-8")


def clean(s: str) -> str:
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2026", "...")
    s = s.replace("\u2192", "->").replace("\u00d7", "x").replace("\u2022", "-")
    s = s.replace("\u2500", "-").replace("\u2502", "|")
    s = s.replace("\u2514", "+").replace("\u251c", "+").replace("\u250c", "+")
    s = s.replace("\u2510", "+").replace("\u2518", "+").replace("\u2524", "+")
    s = s.replace("\u2534", "+").replace("\u252c", "+").replace("\u253c", "+")
    s = s.replace("\u25cf", "*").replace("\u2713", "[ok]").replace("\u2011", "-")
    return s.encode("latin-1", "replace").decode("latin-1")


class PaperPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, "ItsNotAI Labs / Medina Tech Labs - Pixel-to-Meaning Host Co-Pilots", align="C")
            self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"INL-2026-POCKET.PIX.FULL.001  |  Page {self.page_no()}", align="C")


pdf = PaperPDF()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()
pdf.set_margins(18, 18, 18)

w = pdf.epw
for raw in text.splitlines():
    line = clean(raw.rstrip())
    if not line.strip():
        pdf.ln(3)
        continue
    # skip pure markdown separators
    if set(line.strip()) <= set("-|: "):
        continue
    try:
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(w, 7, line[2:].strip())
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(2)
            pdf.multi_cell(w, 6, line[3:].strip())
            pdf.ln(1)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(w, 5, line[4:].strip())
        elif line.startswith("|"):
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(40, 40, 40)
            cells = [c.strip() for c in line.strip("|").split("|")]
            row = " / ".join(cells)
            if len(row) > 110:
                row = row[:107] + "..."
            pdf.multi_cell(w, 4, row)
        elif line.startswith("```"):
            continue
        elif line.startswith("- ") or re.match(r"^\d+\.", line):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(w, 4.5, line)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(25, 25, 25)
            pdf.multi_cell(w, 4.5, line)
    except Exception:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w, 4, line[:200])

pdf_path = notes_dirs[1] / "POCKET_PIXEL_TRANSLATOR_FULL_PAPER.pdf"
pdf.output(str(pdf_path))
for d in (notes_dirs[0], notes_dirs[2]):
    pdf.output(str(d / "POCKET_PIXEL_TRANSLATOR_FULL_PAPER.pdf"))

print("PDF:", pdf_path, "bytes", pdf_path.stat().st_size)
print("Notes MD+PDF:", notes_dirs[0])
print("Home notes:", notes_dirs[2])
