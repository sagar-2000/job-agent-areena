"""
PDF resume generator matching Areena Taneja's exact CV format.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether

HEADER_COLOR = HexColor("#1A252F")
BODY_COLOR   = black

LEFT_MARGIN  = 14 * mm
RIGHT_MARGIN = 14 * mm
TOP_MARGIN   = 10 * mm
BOT_MARGIN   = 10 * mm


def _styles():
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=20,
            textColor=HEADER_COLOR, alignment=TA_CENTER, spaceAfter=1, leading=24),
        "location": ParagraphStyle("location", fontName="Helvetica", fontSize=9,
            textColor=BODY_COLOR, alignment=TA_CENTER, spaceAfter=3),
        "contact_left": ParagraphStyle("contact_left", fontName="Helvetica", fontSize=8.5,
            textColor=BODY_COLOR, alignment=TA_LEFT, leading=12),
        "contact_right": ParagraphStyle("contact_right", fontName="Helvetica", fontSize=8.5,
            textColor=BODY_COLOR, alignment=TA_RIGHT, leading=12),
        "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=9,
            textColor=BODY_COLOR, leading=12, spaceAfter=3, spaceBefore=4),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=10,
            textColor=HEADER_COLOR, spaceBefore=7, spaceAfter=2),
        "job_title": ParagraphStyle("job_title", fontName="Helvetica-Bold", fontSize=9,
            textColor=BODY_COLOR, spaceAfter=0),
        "company_line": ParagraphStyle("company_line", fontName="Helvetica", fontSize=9,
            textColor=BODY_COLOR, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=8.8,
            textColor=BODY_COLOR, leftIndent=8, spaceAfter=1.5, leading=12),
        "sub_heading": ParagraphStyle("sub_heading", fontName="Helvetica-Bold", fontSize=9,
            textColor=BODY_COLOR, spaceBefore=5, spaceAfter=2),
        "sub_text": ParagraphStyle("sub_text", fontName="Helvetica", fontSize=8.8,
            textColor=BODY_COLOR, leading=12.5, spaceAfter=3),
        "edu_degree": ParagraphStyle("edu_degree", fontName="Helvetica-Bold", fontSize=9,
            textColor=BODY_COLOR, spaceBefore=4),
        "edu_detail": ParagraphStyle("edu_detail", fontName="Helvetica", fontSize=9,
            textColor=BODY_COLOR, leading=12, spaceAfter=2),
        "skill_line": ParagraphStyle("skill_line", fontName="Helvetica", fontSize=8.8,
            textColor=BODY_COLOR, spaceAfter=3, leading=12.5),
        "cert": ParagraphStyle("cert", fontName="Helvetica", fontSize=8.8,
            textColor=BODY_COLOR, leading=13, spaceAfter=2),
    }


def _section_header(title, s):
    return [
        Paragraph(title, s["section"]),
        HRFlowable(width="100%", thickness=0.75, color=HEADER_COLOR, spaceAfter=4),
    ]


def _safe(text):
    if "<link" in text or "<b>" in text:
        return text
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_resume_pdf(data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    s = _styles()
    page_w = A4[0]
    usable_w = page_w - LEFT_MARGIN - RIGHT_MARGIN

    doc = SimpleDocTemplate(output_path, pagesize=A4,
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOT_MARGIN)

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Areena Taneja", s["name"]))
    story.append(Paragraph("Dublin, Ireland", s["location"]))

    # Two-column contact row
    contact_data = [[
        Paragraph(
            'Email: <link href="mailto:areenataneja1333@gmail.com" color="#1155CC">areenataneja1333@gmail.com</link>'
            '<br/>Contact: +353899525044', s["contact_left"]),
        Paragraph(
            'LinkedIn: <link href="https://www.linkedin.com/in/areena-taneja/" color="#1155CC">https://www.linkedin.com/in/areena-taneja/</link>'
            '<br/>Stamp 4 (Ireland) – No sponsorship required', s["contact_right"]),
    ]]
    contact_table = Table(contact_data, colWidths=[usable_w * 0.5, usable_w * 0.5])
    contact_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(contact_table)
    story.append(HRFlowable(width="100%", thickness=0.75, color=HEADER_COLOR, spaceBefore=4, spaceAfter=0))

    # ── Summary ───────────────────────────────────────────────────────────────
    story.append(Paragraph(_safe(data.get("summary", "")), s["summary"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=HEADER_COLOR, spaceAfter=0))

    # ── Work Experience ───────────────────────────────────────────────────────
    story += _section_header("WORK EXPERIENCE", s)

    for exp in data.get("experiences", []):
        # Keep only the title + company line together to avoid orphaned headers
        header_block = [
            Paragraph(f'<u>{_safe(exp["title"])}</u>', s["job_title"]),
            Paragraph(f'<b>{_safe(exp["company"])}</b> • {_safe(exp["location"])} • {_safe(exp["date"])}', s["company_line"]),
        ]
        story.append(KeepTogether(header_block))

        for bullet in exp.get("bullets", []):
            story.append(Paragraph(f"• {_safe(bullet)}", s["bullet"]))

        # Key event highlights / sub-sections
        for sub in exp.get("highlights", []):
            sub_block = [Paragraph(_safe(sub.get("heading", "")), s["sub_heading"])]
            if sub.get("text"):
                sub_block.append(Paragraph(_safe(sub["text"]), s["sub_text"]))
            for b in sub.get("bullets", []):
                sub_block.append(Paragraph(f"• {_safe(b)}", s["bullet"]))
            story.append(KeepTogether(sub_block))

        story.append(Spacer(1, 5))

    # ── Academic Qualifications ───────────────────────────────────────────────
    story += _section_header("ACADEMIC QUALIFICATIONS", s)

    for edu in data.get("education", []):
        degree_line = f'<b>{_safe(edu["degree"])}</b> • {_safe(edu["date"])}'
        story.append(Paragraph(degree_line, s["edu_degree"]))
        story.append(Paragraph(_safe(edu["university"]) + ", " + _safe(edu["location"]), s["edu_detail"]))
        if edu.get("modules"):
            story.append(Paragraph(f'<b>Core Modules:</b> {_safe(edu["modules"])}', s["edu_detail"]))
        story.append(Spacer(1, 5))

    # ── Skills ────────────────────────────────────────────────────────────────
    story += _section_header("SKILLS", s)

    for skill in data.get("skills", []):
        items_str = " • ".join(skill["items"]) if isinstance(skill["items"], list) else skill["items"]
        line = f'<b>{_safe(skill["category"])}</b> - {_safe(items_str)}'
        story.append(Paragraph(line, s["skill_line"]))

    # ── Certifications ────────────────────────────────────────────────────────
    certs = data.get("certifications", [])
    if certs:
        story += _section_header("CERTIFICATIONS", s)
        mid = (len(certs) + 1) // 2
        left_certs = certs[:mid]
        right_certs = certs[mid:]

        left_text  = "<br/>".join(f"• {_safe(c)}" for c in left_certs)
        right_text = "<br/>".join(f"• {_safe(c)}" for c in right_certs)

        cert_data = [[
            Paragraph(left_text, s["cert"]),
            Paragraph(right_text, s["cert"]),
        ]]
        cert_table = Table(cert_data, colWidths=[usable_w * 0.5, usable_w * 0.5])
        cert_table.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(cert_table)

    doc.build(story)
    return output_path
