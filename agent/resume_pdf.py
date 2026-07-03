"""
PDF resume generator that replicates Sagar's exact resume format.
Takes structured resume data and outputs a pixel-perfect PDF.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether

# ── Colours ──────────────────────────────────────────────────────────────────
HEADER_COLOR   = HexColor("#1A252F")   # dark navy – section headers & name
RULE_COLOR     = HexColor("#1A252F")
BODY_COLOR     = black

# ── Font sizes ────────────────────────────────────────────────────────────────
NAME_SIZE      = 22
CONTACT_SIZE   = 9.5
SECTION_SIZE   = 11
BODY_SIZE      = 9.5
SMALL_SIZE     = 9

# ── Margins ───────────────────────────────────────────────────────────────────
LEFT_MARGIN  = 17 * mm
RIGHT_MARGIN = 17 * mm
TOP_MARGIN   = 12 * mm
BOT_MARGIN   = 12 * mm

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/output")


def _styles():
    """Return a dict of all paragraph styles."""
    return {
        "name": ParagraphStyle(
            "name",
            fontName="Helvetica-Bold",
            fontSize=NAME_SIZE,
            textColor=HEADER_COLOR,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=26,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontName="Helvetica",
            fontSize=CONTACT_SIZE,
            textColor=BODY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=13,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=SECTION_SIZE,
            textColor=HEADER_COLOR,
            spaceBefore=7,
            spaceAfter=2,
        ),
        "job_title": ParagraphStyle(
            "job_title",
            fontName="Helvetica-Bold",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
        ),
        "job_date": ParagraphStyle(
            "job_date",
            fontName="Helvetica-Bold",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            alignment=TA_RIGHT,
        ),
        "company": ParagraphStyle(
            "company",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
        ),
        "location": ParagraphStyle(
            "location",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            alignment=TA_RIGHT,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            leftIndent=10,
            firstLineIndent=0,
            spaceAfter=2,
            leading=12.5,
        ),
        "project_title": ParagraphStyle(
            "project_title",
            fontName="Helvetica-Bold",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            spaceBefore=5,
            spaceAfter=1,
        ),
        "edu_degree": ParagraphStyle(
            "edu_degree",
            fontName="Helvetica-Bold",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            spaceBefore=4,
        ),
        "edu_date": ParagraphStyle(
            "edu_date",
            fontName="Helvetica-Bold",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            alignment=TA_RIGHT,
            spaceBefore=4,
        ),
        "edu_uni": ParagraphStyle(
            "edu_uni",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
        ),
        "edu_loc": ParagraphStyle(
            "edu_loc",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            alignment=TA_RIGHT,
        ),
        "skill_line": ParagraphStyle(
            "skill_line",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            spaceAfter=3,
            leading=13,
        ),
        "summary": ParagraphStyle(
            "summary",
            fontName="Helvetica",
            fontSize=BODY_SIZE,
            textColor=BODY_COLOR,
            leading=13,
            spaceAfter=3,
        ),
    }


def _section_header(title: str, s: dict):
    """Section header + full-width rule."""
    return [
        Paragraph(title, s["section"]),
        HRFlowable(width="100%", thickness=0.75, color=RULE_COLOR, spaceAfter=4),
    ]


def _two_col(left_text, left_style, right_text, right_style, page_width):
    """Two-column row (e.g. job title | date)."""
    usable = page_width - LEFT_MARGIN - RIGHT_MARGIN
    data = [[Paragraph(left_text, left_style), Paragraph(right_text, right_style)]]
    t = Table(data, colWidths=[usable * 0.70, usable * 0.30])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
    ]))
    return t


def _safe_xml(text: str) -> str:
    """Escape special XML characters for ReportLab Paragraph content."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _bullet_text(text: str) -> str:
    """Convert plain bullet text to ReportLab-safe XML."""
    return f"• {_safe_xml(text)}"


def _safe_para(text: str, style) -> "Paragraph":
    """Create a Paragraph, safely escaping & < > unless text already contains <link> tags."""
    from reportlab.platypus import Paragraph as P
    # Only escape if it doesn't look like it already has XML tags
    if "<link" not in text and "<b>" not in text:
        text = _safe_xml(text)
    return P(text, style)


def generate_resume_pdf(data: dict, output_path: str) -> str:
    """
    Generate a PDF resume from structured data.

    Expected data format:
    {
      "name": "Sagar Mahajan",
      "contact": "email | phone | LinkedIn | Portfolio | GitHub | Location",
      "summary": "...",
      "experiences": [
        {
          "title": "Data Analyst Intern",
          "company": "Infinity Villas",
          "date": "Jun 2025 - Dec 2025",
          "location": "Remote, Ireland",
          "bullets": ["bullet 1", "bullet 2"]
        }
      ],
      "projects": [
        {
          "title": "Project Name (Tech1, Tech2)",
          "bullets": ["bullet 1", "bullet 2"]
        }
      ],
      "education": [
        {
          "degree": "MSc Computer Science (Data Science)",
          "university": "Technological University Dublin",
          "date": "Sept 2024 - Sept 2025",
          "location": "Dublin, Ireland"
        }
      ],
      "skills": [
        {"category": "Programming Languages", "items": "Python, SQL, R"},
        {"category": "Tools", "items": "DBT, Apache Airflow, ..."},
        {"category": "Technical Skills", "items": "Matplotlib, ..."}
      ]
    }
    """
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

    page_w = A4[0]
    story = []

    # ── Name ──────────────────────────────────────────────────────────────────
    story.append(Paragraph(data["name"], s["name"]))
    story.append(Paragraph(data["contact"], s["contact"]))  # contact may contain <link> tags

    # ── Summary ───────────────────────────────────────────────────────────────
    story += _section_header("Summary", s)
    story.append(_safe_para(data["summary"], s["summary"]))

    # ── Experience ────────────────────────────────────────────────────────────
    story += _section_header("Experiences", s)
    for exp in data.get("experiences", []):
        block = []
        block.append(_two_col(exp["title"], s["job_title"], exp["date"], s["job_date"], page_w))
        block.append(_two_col(exp["company"], s["company"], exp["location"], s["location"], page_w))
        for bullet in exp.get("bullets", []):
            block.append(Paragraph(_bullet_text(bullet), s["bullet"]))
        block.append(Spacer(1, 3))
        story.append(KeepTogether(block))

    # ── Projects ──────────────────────────────────────────────────────────────
    story += _section_header("Projects", s)
    for proj in data.get("projects", []):
        block = []
        block.append(_safe_para(proj["title"], s["project_title"]))
        for bullet in proj.get("bullets", []):
            block.append(Paragraph(_bullet_text(bullet), s["bullet"]))
        story.append(KeepTogether(block))

    # ── Education ─────────────────────────────────────────────────────────────
    story += _section_header("Education", s)
    for edu in data.get("education", []):
        block = []
        block.append(_two_col(edu["degree"], s["edu_degree"], edu["date"], s["edu_date"], page_w))
        block.append(_two_col(edu["university"], s["edu_uni"], edu["location"], s["edu_loc"], page_w))
        block.append(Spacer(1, 3))
        story.append(KeepTogether(block))

    # ── Skills ────────────────────────────────────────────────────────────────
    story += _section_header("Skills", s)
    for skill in data.get("skills", []):
        line = f"<b>{skill['category']} :</b> {skill['items']}"
        story.append(Paragraph(line, s["skill_line"]))

    doc.build(story)
    return output_path
