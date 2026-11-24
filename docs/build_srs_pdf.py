"""Generate SRS.pdf from docs/SRS.md using reportlab."""
import sys
import re
from pathlib import Path

# Compatibility patch for Python 3.9 environments
_orig_v = sys.version_info
if sys.version_info < (3, 10):
    sys.version_info = (3, 11, 0, 'final', 0)
    import typing
    try:
        import typing_extensions
        typing.TypeGuard = typing_extensions.TypeGuard
    except Exception:
        class TypeGuard: pass
        typing.TypeGuard = TypeGuard

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

if _orig_v < (3, 10):
    sys.version_info = _orig_v

DOCS = Path(__file__).resolve().parent
SRS_MD = DOCS / "SRS.md"
SRS_PDF = DOCS / "SRS.pdf"

# ── Colour palette ──────────────────────────────────────────────────────────
C_INK      = colors.HexColor("#0f172a")
C_ACCENT   = colors.HexColor("#059669")
C_HEADER   = colors.HexColor("#e2efe9")
C_BORDER   = colors.HexColor("#cbd5e1")
C_MUTED    = colors.HexColor("#475569")
C_WHITE    = colors.white
C_ALTROW   = colors.HexColor("#f8fafb")


def build_styles():
    base = getSampleStyleSheet()

    def add(name, **kw):
        if name not in base:
            base.add(ParagraphStyle(name, **kw))
        return base[name]

    add("Cover_Title",    fontName="Helvetica-Bold",  fontSize=22, leading=28,
        spaceAfter=10, textColor=C_INK, alignment=TA_LEFT)
    add("Cover_Sub",      fontName="Helvetica",       fontSize=11, leading=15,
        spaceAfter=4,  textColor=C_MUTED)
    add("Cover_Meta",     fontName="Helvetica",       fontSize=10, leading=14,
        spaceAfter=3,  textColor=C_INK)
    add("H1",             fontName="Helvetica-Bold",  fontSize=16, leading=20,
        spaceBefore=18, spaceAfter=6, textColor=C_INK)
    add("H2",             fontName="Helvetica-Bold",  fontSize=12, leading=16,
        spaceBefore=14, spaceAfter=4, textColor=C_INK)
    add("H3",             fontName="Helvetica-Bold",  fontSize=10.5, leading=14,
        spaceBefore=10, spaceAfter=3, textColor=C_ACCENT)
    add("H4",             fontName="Helvetica-Bold",  fontSize=10, leading=13,
        spaceBefore=8,  spaceAfter=3, textColor=C_INK)
    add("Body",           fontName="Helvetica",       fontSize=9.5, leading=14,
        spaceAfter=6,  textColor=C_INK)
    add("Bullet",         fontName="Helvetica",       fontSize=9.5, leading=13,
        spaceAfter=3,  textColor=C_INK, leftIndent=14, bulletIndent=0)
    add("Code",           fontName="Courier",         fontSize=8, leading=12,
        spaceAfter=4,  textColor=C_INK, backColor=colors.HexColor("#f1f5f9"),
        leftIndent=10, rightIndent=10)
    add("TableHead",      fontName="Helvetica-Bold",  fontSize=8.5, leading=11,
        textColor=C_INK)
    add("TableCell",      fontName="Helvetica",       fontSize=8.5, leading=11,
        textColor=C_INK)
    add("TableCellCode",  fontName="Courier",         fontSize=7.5, leading=10,
        textColor=C_INK)
    add("Footer",         fontName="Helvetica",       fontSize=7.5, leading=10,
        textColor=C_MUTED)
    add("NoteBox",        fontName="Helvetica-Oblique", fontSize=9, leading=13,
        spaceAfter=8, textColor=C_MUTED, leftIndent=12)
    return base


def footer_cb(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(14*mm, 10*mm,
        "Smart Public Transport System  |  CS201 Software Engineering  |  IIIT Lucknow  |  IEEE 830")
    canvas.drawRightString(A4[0] - 14*mm, 10*mm, str(doc.page))
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(14*mm, 13*mm, A4[0] - 14*mm, 13*mm)
    canvas.restoreState()


def escape_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def md_inline(text):
    """Convert basic inline markdown (bold, code, italic) to valid reportlab XML."""
    code_spans = []
    def save_code(m):
        code_spans.append(escape_xml(m.group(1)))
        return f"__CODE_SPAN_{len(code_spans)-1}__"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = escape_xml(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"<i>\1</i>", text)

    for idx, code in enumerate(code_spans):
        text = text.replace(f"__CODE_SPAN_{idx}__", f'<font name="Courier">{code}</font>')

    return text


def parse_table(lines):
    """Parse a markdown table into list-of-lists."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line or set(line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set():
            continue  # separator row
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def build_pdf_table(rows, styles, col_widths=None):
    """Build a reportlab Table from markdown rows."""
    page_w = A4[0] - 28*mm
    if col_widths is None:
        n = len(rows[0]) if rows else 1
        col_widths = [page_w / n] * n

    data = []
    for ri, row in enumerate(rows):
        pdf_row = []
        for ci, cell in enumerate(row):
            sty = styles["TableHead"] if ri == 0 else styles["TableCell"]
            # cells with only code-like content
            if re.match(r"^`[^`]+`$", cell.strip()):
                sty = styles["TableCellCode"]
                cell = cell.strip().strip("`")
            else:
                cell = md_inline(cell)
            pdf_row.append(Paragraph(cell, sty))
        data.append(pdf_row)

    tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  C_HEADER),
        ("BACKGROUND",   (0, 1), (-1, -1), C_WHITE),
        ("ROWBACKGROUNDS",(0, 1),(-1, -1), [C_WHITE, C_ALTROW]),
        ("GRID",         (0, 0), (-1, -1), 0.4, C_BORDER),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    return tbl


def md_to_story(md_text, styles):
    story = []
    lines = md_text.splitlines()
    page_w = A4[0] - 28*mm
    i = 0
    in_code_block = False
    code_lines = []
    table_lines = []
    in_table = False

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        # ── Code block ───────────────────────────────────────────────────────
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = escape_xml("\n".join(code_lines))
                story.append(Paragraph(code_text.replace("\n", "<br/>"), styles["Code"]))
                story.append(Spacer(1, 4))
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(raw)
            i += 1
            continue

        # ── Table ────────────────────────────────────────────────────────────
        if line.startswith("|"):
            table_lines.append(line)
            i += 1
            continue
        else:
            if table_lines:
                rows = parse_table(table_lines)
                table_lines = []
                if rows:
                    # Determine col widths from header
                    n = len(rows[0])
                    # heuristic widths based on column count
                    if n == 2:
                        cw = [page_w * 0.28, page_w * 0.72]
                    elif n == 3:
                        cw = [page_w * 0.15, page_w * 0.55, page_w * 0.30]
                    elif n == 4:
                        cw = [page_w * 0.12, page_w * 0.35, page_w * 0.28, page_w * 0.25]
                    else:
                        cw = [page_w / n] * n
                    story.append(build_pdf_table(rows, styles, col_widths=cw))
                    story.append(Spacer(1, 8))

        # ── Blank line ───────────────────────────────────────────────────────
        if not line:
            story.append(Spacer(1, 4))
            i += 1
            continue

        # ── Horizontal rule ──────────────────────────────────────────────────
        if re.match(r"^-{3,}$", line) or re.match(r"^\*{3,}$", line):
            story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6))
            i += 1
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        h_match = re.match(r"^(#{1,4})\s+(.*)", line)
        if h_match:
            level = len(h_match.group(1))
            text = h_match.group(2)
            sty = {1: "H1", 2: "H2", 3: "H3", 4: "H4"}.get(level, "H4")
            if level == 1:
                story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=4))
            story.append(Paragraph(md_inline(text), styles[sty]))
            i += 1
            continue

        # ── Blockquote / Note ────────────────────────────────────────────────
        if line.startswith(">"):
            text = line.lstrip("> ").strip()
            story.append(Paragraph(md_inline(text), styles["NoteBox"]))
            i += 1
            continue

        # ── Bullet / list items ──────────────────────────────────────────────
        bl_match = re.match(r"^[-*]\s+(.*)", line)
        num_match = re.match(r"^\d+\.\s+(.*)", line)
        if bl_match or num_match:
            text = (bl_match or num_match).group(1)
            bullet = "•" if bl_match else "○"
            story.append(Paragraph(f"{bullet}  {md_inline(text)}", styles["Bullet"]))
            i += 1
            continue

        # ── Plain paragraph ──────────────────────────────────────────────────
        story.append(Paragraph(md_inline(line), styles["Body"]))
        i += 1

    return story


def build():
    md_text = SRS_MD.read_text(encoding="utf-8")
    styles = build_styles()

    # Split into cover section and body
    # Cover = everything before first "---" separator
    parts = re.split(r"\n---+\n", md_text, maxsplit=1)
    cover_md = parts[0] if len(parts) > 1 else ""
    body_md  = parts[1] if len(parts) > 1 else md_text

    story = []

    # ── Cover page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20*mm))
    # Green accent bar
    story.append(HRFlowable(width="100%", thickness=4, color=C_ACCENT, spaceAfter=14))

    for line in cover_md.strip().splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("# "):
            story.append(Paragraph(escape_xml(line[2:]), styles["Cover_Title"]))
        elif line.startswith("**"):
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape_xml(line))
            story.append(Paragraph(text, styles["Cover_Meta"]))
        elif line.startswith("|"):
            pass  # skip table on cover for now
        else:
            story.append(Paragraph(escape_xml(line), styles["Cover_Sub"]))

    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Spacer(1, 4*mm))

    # Team table on cover
    team = [
        ["Name", "Enrollment No.", "Role"],
        ["Dhruvika Rawat",   "LCB2025012", "Data Pipeline & Testing"],
        ["Ganga Kaur",       "LCI2025033", "UI Design & Frontend"],
        ["Harshita Punia",   "LCB2025011", "ML Model & Evaluation"],
        ["Ocean Kesarwani",  "LCI2025019", "Routing Algorithm & Backend"],
    ]
    page_w = A4[0] - 28*mm
    story.append(build_pdf_table(team, styles, col_widths=[page_w*0.33, page_w*0.25, page_w*0.42]))
    story.append(PageBreak())

    # ── Body ──────────────────────────────────────────────────────────────────
    # Remove the ToC section (between "## Table of Contents" and next "---" or "## 1.")
    body_md = re.sub(
        r"## Table of Contents.*?(?=\n## 1\.|\n---)",
        "", body_md, flags=re.DOTALL
    )

    story += md_to_story(body_md, styles)

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        str(SRS_PDF),
        pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=16*mm,  bottomMargin=18*mm,
    )
    doc.build(story, onFirstPage=footer_cb, onLaterPages=footer_cb)
    print(f"✅  Built {SRS_PDF}  ({SRS_PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
