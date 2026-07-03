"""
Cover letter PDF generator — Areena Taneja's format.
Same header as resume, then date / salutation / body paragraphs / sign-off.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

HEADER_COLOR = HexColor("#1A252F")
BODY_COLOR   = black

LEFT_MARGIN  = 17 * mm
RIGHT_MARGIN = 17 * mm
TOP_MARGIN   = 12 * mm
BOT_MARGIN   = 12 * mm

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/output")

CONTACT_LINE = (
    'areenataneja1333@gmail.com | +353899525044 | '
    '<link href="https://www.linkedin.com/in/areena-taneja/" color="#1155CC">LinkedIn</link> | '
    'Dublin, Ireland | Stamp 4 – No sponsorship required'
)


def _styles():
    return {
        "name": ParagraphStyle(
            "name",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=HEADER_COLOR,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=26,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=BODY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=13,
        ),
        "date": ParagraphStyle(
            "date",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_COLOR,
            alignment=TA_LEFT,
            spaceBefore=14,
            spaceAfter=10,
        ),
        "salutation": ParagraphStyle(
            "salutation",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_COLOR,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_COLOR,
            alignment=TA_LEFT,
            leading=14,
            spaceAfter=10,
        ),
        "signoff": ParagraphStyle(
            "signoff",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_COLOR,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=14,
        ),
        "name_end": ParagraphStyle(
            "name_end",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_COLOR,
            alignment=TA_LEFT,
        ),
    }


def generate_coverletter_pdf(data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    s = _styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
    )

    story = []

    story.append(Paragraph("Areena Taneja", s["name"]))
    story.append(Paragraph(CONTACT_LINE, s["contact"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HEADER_COLOR, spaceAfter=0))

    date_str = data.get("date") or datetime.today().strftime("%-d %B %Y")
    story.append(Paragraph(date_str, s["date"]))

    story.append(Paragraph(data["salutation"], s["salutation"]))

    for para in data["paragraphs"]:
        para = para.replace("&", "&amp;")
        story.append(Paragraph(para, s["body"]))

    story.append(Paragraph("Yours sincerely,", s["signoff"]))
    story.append(Paragraph("Areena Taneja", s["name_end"]))

    doc.build(story)
    return output_path
