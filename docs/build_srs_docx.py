"""Generate SRS.docx from docs/SRS.md using python-docx."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCS = Path(__file__).resolve().parent
SRS_MD = DOCS / "SRS.md"
SRS_DOCX = DOCS / "SRS.docx"

# Colours
INK    = RGBColor(0x0f, 0x17, 0x2a)
ACCENT = RGBColor(0x05, 0x96, 0x69)
MUTED  = RGBColor(0x47, 0x55, 0x69)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
HEADER_BG = "E2EFE9"   # table header fill
ALT_BG    = "F8FAFB"


# ── helpers ──────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_bottom_border(paragraph, color="059669", size=12):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_hr(doc, color="CBD5E1"):
    p = doc.add_paragraph()
    add_bottom_border(p, color=color, size=4)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    return p


def apply_inline_md(paragraph, text):
    """Add runs with bold/italic/code formatting from markdown inline syntax."""
    # Tokenise into plain / bold / italic / code spans
    pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)")
    parts = pattern.split(text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif (part.startswith("*") and part.endswith("*") and len(part) > 2) or \
             (part.startswith("_") and part.endswith("_") and len(part) > 2):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Courier New"
            run.font.size = Pt(9)
        else:
            paragraph.add_run(part)


def parse_table_rows(lines):
    rows = []
    for line in lines:
        line = line.strip()
        # Skip separator rows like |---|---|
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        if not line or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def add_md_table(doc, rows):
    if not rows:
        return
    n_cols = len(rows[0])
    table = doc.add_table(rows=0, cols=n_cols)
    table.style = "Table Grid"
    table.autofit = True

    for ri, row_data in enumerate(rows):
        row = table.add_row()
        for ci, cell_text in enumerate(row_data):
            cell = row.cells[ci]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            if ri == 0:
                set_cell_bg(cell, HEADER_BG)
                run = p.add_run(cell_text)
                run.bold = True
                run.font.size = Pt(9)
            else:
                if ri % 2 == 0:
                    set_cell_bg(cell, ALT_BG)
                p.paragraph_format.space_after = Pt(2)
                apply_inline_md(p, cell_text)
                for run in p.runs:
                    run.font.size = Pt(9)
    doc.add_paragraph()  # spacing after table


# ── main builder ─────────────────────────────────────────────────────────────

def build():
    md_text = SRS_MD.read_text(encoding="utf-8")
    doc = Document()

    # Page setup – A4
    section = doc.sections[0]
    section.page_width  = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin  = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin  = Cm(2.2)

    # Base styles
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = INK

    for sname in ["Heading 1", "Heading 2", "Heading 3", "Heading 4"]:
        s = doc.styles[sname]
        s.font.name = "Calibri"
        s.font.color.rgb = INK
        for border_el in s.element.iter(qn("w:pBdr")):
            border_el.getparent().remove(border_el)

    doc.styles["Heading 1"].font.size = Pt(16)
    doc.styles["Heading 1"].font.bold = True
    doc.styles["Heading 2"].font.size = Pt(13)
    doc.styles["Heading 2"].font.bold = True
    doc.styles["Heading 3"].font.size = Pt(11)
    doc.styles["Heading 3"].font.color.rgb = ACCENT
    doc.styles["Heading 4"].font.size = Pt(10.5)
    doc.styles["Heading 4"].font.bold = True

    # Footer
    footer_para = section.footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer_para.add_run(
        "Smart Public Transport System  |  CS201 Software Engineering  |  IIIT Lucknow  |  IEEE 830    "
    )
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = MUTED

    # ── Parse markdown ────────────────────────────────────────────────────────
    lines = md_text.splitlines()
    # Strip ToC block
    md_no_toc = re.sub(
        r"## Table of Contents.*?(?=\n## 1\.|\n---)",
        "", md_text, flags=re.DOTALL
    )
    lines = md_no_toc.splitlines()

    i = 0
    in_code = False
    code_buf = []
    table_buf = []
    cover_done = False
    after_first_hr = False

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        # ── Code fence ───────────────────────────────────────────────────────
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                p = doc.add_paragraph("\n".join(code_buf))
                p.style = "No Spacing"
                for run in p.runs:
                    run.font.name = "Courier New"
                    run.font.size = Pt(8.5)
                code_buf = []
            i += 1
            continue

        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        # ── Flush table if next line is not table ────────────────────────────
        if table_buf and not line.startswith("|"):
            add_md_table(doc, parse_table_rows(table_buf))
            table_buf = []

        # ── Table line ───────────────────────────────────────────────────────
        if line.startswith("|"):
            table_buf.append(line)
            i += 1
            continue

        # ── HR / separator ───────────────────────────────────────────────────
        if re.match(r"^-{3,}$", line) or re.match(r"^\*{3,}$", line):
            if not after_first_hr:
                after_first_hr = True
                # Cover page break after first ---
                doc.add_page_break()
            else:
                add_hr(doc)
            i += 1
            continue

        # ── Blank ────────────────────────────────────────────────────────────
        if not line:
            i += 1
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        h = re.match(r"^(#{1,4})\s+(.*)", line)
        if h:
            level = len(h.group(1))
            text = h.group(2)
            heading = doc.add_heading(level=level)
            heading.clear()
            apply_inline_md(heading, text)
            if level == 1:
                add_bottom_border(heading, color="059669", size=8)
            i += 1
            continue

        # ── Blockquote ───────────────────────────────────────────────────────
        if line.startswith(">"):
            text = line.lstrip("> ").strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            apply_inline_md(p, text)
            for run in p.runs:
                run.font.italic = True
                run.font.color.rgb = MUTED
                run.font.size = Pt(9.5)
            i += 1
            continue

        # ── Bullet ───────────────────────────────────────────────────────────
        bl = re.match(r"^[-*]\s+(.*)", line)
        num = re.match(r"^\d+\.\s+(.*)", line)
        if bl or num:
            text = (bl or num).group(1)
            p = doc.add_paragraph(style="List Bullet" if bl else "List Number")
            apply_inline_md(p, text)
            for run in p.runs:
                run.font.size = Pt(10)
            i += 1
            continue

        # ── Plain paragraph ───────────────────────────────────────────────────
        p = doc.add_paragraph()
        apply_inline_md(p, line)
        p.paragraph_format.space_after = Pt(6)
        i += 1

    # flush trailing table
    if table_buf:
        add_md_table(doc, parse_table_rows(table_buf))

    doc.save(SRS_DOCX)
    print(f"✅  Built {SRS_DOCX}  ({SRS_DOCX.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
