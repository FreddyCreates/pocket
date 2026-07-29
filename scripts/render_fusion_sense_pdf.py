"""Render Fusion-Sense Interface Paradigm research to PDF."""
from __future__ import annotations

import shutil
from pathlib import Path

from fpdf import FPDF

md_path = (
    Path.home()
    / "OneDrive"
    / "Documents"
    / "POCKET_Research"
    / "Fusion_Sense_Interface_Paradigm"
    / "FUSION_SENSE_INTERFACE_PARADIGM.md"
)
text = md_path.read_text(encoding="utf-8")


def clean(s: str) -> str:
    table = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2192": "->",
        "\u2022": "-",
    }
    for a, b in table.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


class Paper(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"INL-2026-POCKET.FUSION_SENSE.001  |  Page {self.page_no()}", align="C")


pdf = Paper()
pdf.set_auto_page_break(auto=True, margin=16)
pdf.add_page()
pdf.set_margins(16, 16, 16)
w = pdf.epw

for raw in text.splitlines():
    line = clean(raw.rstrip())
    if not line.strip():
        pdf.ln(2)
        continue
    if set(line.strip()) <= set("-|:= ") or line.strip().startswith("```"):
        continue
    try:
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(w, 7, line[2:])
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.ln(1)
            pdf.multi_cell(w, 6, line[3:])
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(w, 5, line[4:])
        elif line.startswith("|"):
            pdf.set_font("Helvetica", "", 8)
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            pdf.multi_cell(w, 4, " | ".join(cells)[:170])
        elif line.startswith("- "):
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(w, 4.5, "  - " + line[2:])
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(w, 4.5, line)
    except Exception:
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w, 4, line[:180])

out = md_path.with_suffix(".pdf")
pdf.output(str(out))
for d in (
    Path.home() / "OneDrive" / "Documents" / "POCKET_Notes",
    Path.home() / ".pocket" / "notes",
    Path(__file__).resolve().parents[1] / "docs" / "research",
):
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, d / out.name)
    (d / md_path.name).write_text(text, encoding="utf-8")
print("PDF:", out)
