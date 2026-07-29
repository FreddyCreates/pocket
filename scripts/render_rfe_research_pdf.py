"""Render RFE-v1 architectural synthesis research journal to PDF."""
from __future__ import annotations

from pathlib import Path
import shutil

from fpdf import FPDF

md_path = (
    Path.home()
    / "OneDrive"
    / "Documents"
    / "POCKET_Research"
    / "RFE_Recursive_Fusion_Engine"
    / "RFE_v1_Architectural_Synthesis.md"
)
out_dir = md_path.parent
text = md_path.read_text(encoding="utf-8")

for d in (
    Path.home() / "OneDrive" / "Documents" / "POCKET_Notes",
    Path.home() / ".pocket" / "notes",
    Path(__file__).resolve().parents[1] / "docs" / "research",
):
    d.mkdir(parents=True, exist_ok=True)
    (d / md_path.name).write_text(text, encoding="utf-8")


def clean(s: str) -> str:
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2026", "...")
    s = s.replace("\u2192", "->").replace("\u00d7", "x").replace("\u2022", "-")
    s = s.replace("\u2265", ">=").replace("\u2011", "-")
    return s.encode("latin-1", "replace").decode("latin-1")


class PaperPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, "ItsNotAI Labs - RFE-v1 Architectural Synthesis (RFE-2023-X1)", align="C")
            self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"INL-2026-POCKET.RFE.v1  |  Page {self.page_no()}", align="C")


pdf = PaperPDF()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()
pdf.set_margins(18, 18, 18)
w = pdf.epw
in_code = False

for raw in text.splitlines():
    line = clean(raw.rstrip())
    if line.strip().startswith("```"):
        in_code = not in_code
        continue
    if not line.strip():
        pdf.ln(2)
        continue
    if set(line.strip()) <= set("-|: ="):
        continue
    try:
        if in_code:
            pdf.set_font("Courier", "", 7)
            pdf.multi_cell(w, 3.5, line[:160])
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(w, 7, line[2:].strip())
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.ln(2)
            pdf.multi_cell(w, 6, line[3:].strip())
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(w, 5, line[4:].strip())
        elif line.startswith("|"):
            pdf.set_font("Helvetica", "", 8)
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            pdf.multi_cell(w, 4, "  |  ".join(cells)[:180])
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(w, 4.5, "  - " + line[2:].strip())
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(w, 4.5, line)
    except Exception:
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w, 4, line[:200])

pdf_path = out_dir / "RFE_v1_Architectural_Synthesis.pdf"
pdf.output(str(pdf_path))
for d in (
    Path.home() / "OneDrive" / "Documents" / "POCKET_Notes",
    Path.home() / ".pocket" / "notes",
    Path(__file__).resolve().parents[1] / "docs" / "research",
):
    try:
        shutil.copy2(pdf_path, d / pdf_path.name)
    except Exception:
        pass
print("PDF:", pdf_path)
