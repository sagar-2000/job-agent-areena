"""
Claude-powered resume tailor — Areena Taneja's agent.
Asks Claude to return structured JSON tailored to a job,
then renders it as a PDF matching Areena's resume format.
"""

import os
import sys
import json
import anthropic
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from agent.resume_pdf import generate_resume_pdf

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_DATA_DIR  = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "../data"))
OUTPUT_DIR = os.path.join(_DATA_DIR, "output")

BASE_RESUME = {
    "name": "Areena Taneja",
    "contact": (
        'areenataneja1333@gmail.com | +353899525044 | '
        '<link href="https://www.linkedin.com/in/areena-taneja/" color="#1155CC">LinkedIn</link> | '
        'Dublin, Ireland | Stamp 4 – No sponsorship required'
    ),
    "experiences": [
        {
            "title": "Senior Marketing Lead",
            "company": "Ingenious Media (previously Premier Publishing and Events Ltd.)",
            "date": "March 2025 – Present",
            "location": "Dublin, Ireland",
            "bullets": [
                "Lead end-to-end campaign planning and execution for 12+ large-scale B2B conferences and exhibitions annually across Ireland and the UK.",
                "Manage paid campaigns across LinkedIn, Meta, and Google Ads, reducing cost-per-registration by 23% while improving engagement and audience quality.",
                "Developed exhibitor marketing and advocacy programmes using Gleanin referral marketing tools, achieving 70%+ participation in co-marketing initiatives.",
                "Use automation and AI tools to improve workflow efficiency and reduce campaign turnaround times by approximately 40%.",
                "Led the end-to-end rebranding from Premier Publishing and Events Ltd. to Ingenious Media, coordinating full brand rollout across all marketing touchpoints.",
                "Spearheaded demand generation strategy for Biopharma & Life Sciences Connected Live: generated 1,096 registrations with 73% converting to in-person attendance (797 attendees).",
                "Delivered a 45% attendee conversion rate for Medtech Innovation 2026 through integrated campaign execution across email, paid, social, exhibitor, and partner channels.",
            ],
        },
        {
            "title": "Digital Marketing Executive",
            "company": "Premier Publishing and Events Ltd.",
            "date": "Oct 2022 – March 2025",
            "location": "Dublin, Ireland",
            "bullets": [
                "Managed digital marketing campaigns for 12+ annual B2B conferences, delivering 7,000+ registrations for flagship industry events.",
                "Designed and executed organic and paid social strategies, growing LinkedIn audiences by 176% across event brands.",
                "Managed a portfolio of 240+ exhibitors as Exhibitor Administrator, supporting marketing coordination and platform adoption.",
                "Updated and maintained 13 event websites and exhibitor portals, ensuring seamless user journeys and up-to-date content.",
                "Wrote and built email campaigns, landing pages, and social content aligned with event positioning and audience needs.",
                "Reported on campaign performance using Google Analytics, Looker Studio, and Power BI, informing optimisation decisions.",
                "Designed marketing packs, PR materials, and exhibitor toolkits, achieving 70%+ adoption of ready-made promotional assets.",
            ],
        },
    ],
    "education": [
        {
            "degree": "MSc Digital Marketing: First Class Honours (1.1) – GPA 3.69",
            "university": "UCD Michael Smurfit Graduate Business School",
            "date": "2021 – 2022",
            "location": "Dublin, Ireland",
        },
        {
            "degree": "Bachelor of Commerce (1.1)",
            "university": "Mehr Chand Mahajan (MCM) DAV College For Women",
            "date": "2017 – 2020",
            "location": "Chandigarh, India",
        },
    ],
    "skills": [
        {"category": "Paid & Digital", "items": "LinkedIn Ads, Meta Ads, Google Ads, Google Display, DV360, SEO, Paid Media Strategy, Performance Optimisation"},
        {"category": "Martech Platforms", "items": "HubSpot, Mailchimp, Marketo (in progress), Eventbrite, Gleanin, Qualtrics"},
        {"category": "Analytics", "items": "Google Analytics, Looker Studio, Power BI, Tableau, Google Sheets, Excel"},
        {"category": "Creative & Content", "items": "Canva, WordPress, Wix, Shopify, Blog Writing, Social Media Curation, Video & GIF Production"},
        {"category": "Core Marketing", "items": "B2B Campaign Management, Demand Generation, Email Marketing, Event Marketing, Content Marketing, Stakeholder Management"},
        {"category": "AI & Automation", "items": "Claude, HubSpot Automation, Smart Workflows for Campaign Optimisation"},
    ],
}


def tailor_resume(job: dict) -> dict:
    """
    Ask Claude to tailor only the summary and bullet points for this job.
    Returns a modified copy of BASE_RESUME with tailored text.
    """
    prompt = f"""You are an expert resume writer. Tailor this candidate's resume for the specific job below.

## Job Details
Title: {job['title']}
Company: {job['company']}
Description:
{(job['description'] or '')[:3000]}

## Instructions
- Rewrite the SUMMARY to speak directly to this role (2-3 sentences max)
- Reorder and reword BULLET POINTS across experiences to highlight the most relevant ones first
- Mirror keywords from the job description naturally — do NOT invent new experience or metrics
- Keep all facts, numbers, dates, company names, and technologies truthful and unchanged
- Keep exactly the same number of bullet points per experience as the original
- Keep bullet points at the SAME LENGTH as the original — do not shorten them, the resume must fill one full page
- Do NOT change education, contact info, or skills section

## Original Resume Data
{json.dumps(BASE_RESUME, indent=2)}

## Output Format
Return ONLY valid JSON with this exact structure (no markdown, no commentary):
{{
  "summary": "tailored summary text here",
  "experiences": [
    {{
      "title": "same as original",
      "company": "same as original",
      "date": "same as original",
      "location": "same as original",
      "bullets": ["reworded bullet 1", "reworded bullet 2", ...]
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ]
    )

    raw = "{" + message.content[0].text.strip()
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    tailored = json.loads(raw)

    result = dict(BASE_RESUME)
    result["summary"] = tailored["summary"]
    result["experiences"] = tailored["experiences"]
    return result


def run(job: dict) -> str:
    """Tailor resume for a job and save as PDF. Returns path to saved PDF."""
    print(f"📝 Tailoring resume for: {job['title']} @ {job['company']}...")

    resume_data = tailor_resume(job)

    company_slug = job["company"].replace(" ", "_").replace("/", "-")[:30]
    title_slug   = job["title"].replace(" ", "_").replace("/", "-")[:30]
    filename     = f"resume_{title_slug}_{company_slug}.pdf"
    output_path  = os.path.join(OUTPUT_DIR, filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_resume_pdf(resume_data, output_path)

    print(f"  ✅ Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    sample_job = {
        "id": 1,
        "title": "B2B Marketing Manager",
        "company": "TestCo",
        "description": "Looking for a B2B Marketing Manager with experience in LinkedIn Ads, HubSpot, demand generation, and event marketing.",
    }
    path = run(sample_job)
    print(f"Generated: {path}")
