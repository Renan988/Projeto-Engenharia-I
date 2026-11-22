from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "relatorio-scrum.md"
OUTPUT = BASE / "relatorio-scrum.pdf"

styles = getSampleStyleSheet()
body = ParagraphStyle(
    "Corpo",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.5,
    leading=13.5,
    alignment=TA_LEFT,
    spaceAfter=5,
)
h1 = ParagraphStyle(
    "Titulo",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=19,
    leading=23,
    spaceAfter=14,
)
h2 = ParagraphStyle(
    "Secao",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12.5,
    leading=16,
    spaceBefore=14,
    spaceAfter=6,
    textColor=colors.HexColor("#17365D"),
)
h3 = ParagraphStyle(
    "Subsecao",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=14,
    spaceBefore=9,
    spaceAfter=4,
)
cell = ParagraphStyle("Celula", parent=body, fontSize=8.2, leading=11, spaceAfter=0)
cell_header = ParagraphStyle("Cabecalho", parent=cell, fontName="Helvetica-Bold")
cover_title = ParagraphStyle(
    "CapaTitulo",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=24,
    leading=29,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#17365D"),
    spaceAfter=10,
)
cover_subtitle = ParagraphStyle(
    "CapaSubtitulo",
    parent=body,
    fontName="Helvetica",
    fontSize=12,
    leading=17,
    alignment=TA_CENTER,
    spaceAfter=24,
)
cover_note = ParagraphStyle(
    "CapaNota",
    parent=body,
    fontSize=9,
    leading=13,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"),
)


def inline(text):
    value = escape(text).replace("`", "")
    parts = value.split("**")
    for index in range(1, len(parts), 2):
        parts[index] = f"<b>{parts[index]}</b>"
    return "".join(parts).replace("\u2022", "-")


def table_block(lines, widths=None):
    rows = []
    for line in lines:
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if all(set(part) <= set("-: ") for part in cells):
            continue
        style = cell_header if not rows else cell
        rows.append([Paragraph(inline(part), style) for part in cells])

    if widths is None:
        widths = [160 / len(rows[0]) * mm] * len(rows[0])
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA7B5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def render_content(lines, story):
    paragraph = []
    index = 0

    def flush():
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph)), body))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        if line.startswith("| "):
            flush()
            block = []
            while index < len(lines) and lines[index].startswith("| "):
                block.append(lines[index])
                index += 1
            story.append(table_block(block))
            story.append(Spacer(1, 5))
            continue
        if not line.strip():
            flush()
        elif line.startswith("# "):
            flush()
            story.append(Paragraph(inline(line[2:]), h1))
        elif line.startswith("## "):
            flush()
            story.append(Paragraph(inline(line[3:]), h2))
        elif line.startswith("### "):
            flush()
            story.append(Paragraph(inline(line[4:]), h3))
        elif line.startswith("- ") or (len(line) > 2 and line[0].isdigit() and line[1:3] == ". "):
            flush()
            story.append(Paragraph(inline(line), body))
        elif line.startswith("<!-- PAGE_BREAK -->"):
            flush()
            story.append(PageBreak())
        else:
            paragraph.append(line.strip())
        index += 1
    flush()


def render_cover(lines, story):
    paragraphs = []
    tables = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("| "):
            block = []
            while index < len(lines) and lines[index].startswith("| "):
                block.append(lines[index])
                index += 1
            tables.append(block)
            continue
        if line.strip():
            paragraphs.append(line.strip())
        index += 1

    story.append(Spacer(1, 22 * mm))
    if paragraphs:
        titulo = paragraphs[0][2:] if paragraphs[0].startswith("# ") else paragraphs[0]
        story.append(Paragraph(inline(titulo), cover_title))
    if len(paragraphs) > 1:
        story.append(Paragraph(inline(paragraphs[1]), cover_subtitle))

    if tables:
        story.append(table_block(tables[0], widths=[38 * mm, 122 * mm]))
        story.append(Spacer(1, 12 * mm))

    if len(tables) > 1:
        story.append(Paragraph("Integrantes do grupo", h2))
        story.append(table_block(tables[1], widths=[70 * mm, 90 * mm]))

    if len(paragraphs) > 2:
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(inline(paragraphs[2]), cover_note))

    story.append(PageBreak())


def build():
    text = SOURCE.read_text(encoding="utf-8")
    segments = text.split("<!-- PAGE_BREAK -->")
    story = []

    render_cover(segments[0].splitlines(), story)
    for segment in segments[1:]:
        render_content(segment.splitlines(), story)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Relatório de prática Scrum - Intech Sistemas",
        author="Equipe Projeto-Engenharia-I",
    )
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
