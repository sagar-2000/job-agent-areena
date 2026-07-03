"""
Claude-powered cover letter generator — Areena Taneja's agent.
Returns structured JSON then renders it as a PDF.
"""

import os
import sys
import json
import anthropic
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from agent.coverletter_pdf import generate_coverletter_pdf

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_DATA_DIR  = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "../data"))
OUTPUT_DIR = os.path.join(_DATA_DIR, "output")

CANDIDATE_BACKGROUND = """
Name: Areena Taneja
Location: Dublin, Ireland
Contact: areenataneja1333@gmail.com | +353899525044
Stamp 4 (Ireland) — No sponsorship required

Experience:
- Senior Marketing Lead @ Ingenious Media (March 2025 – Present): Lead end-to-end campaign planning for 12+ B2B conferences annually.
  Reduced cost-per-registration by 23% through paid media across LinkedIn, Meta, and Google Ads.
  Achieved 70%+ exhibitor participation in co-marketing using Gleanin.
  Cut campaign turnaround times by 40% using automation and AI tools.
  Generated 1,096 registrations for Biopharma & Life Sciences Connected Live (73% converted to in-person attendance).
  Delivered 45% attendee conversion for Medtech Innovation 2026 (first-time event).
  Led full company rebrand from Premier Publishing and Events Ltd. to Ingenious Media.

- Digital Marketing Executive @ Premier Publishing and Events Ltd. (Oct 2022 – March 2025): Delivered 7,000+ registrations for flagship B2B conference events.
  Grew LinkedIn audiences by 176% across event brands through organic and paid social.
  Managed 240+ exhibitors and maintained 13 event websites.
  Designed email campaigns, landing pages, social content, marketing packs, and exhibitor toolkits.

Education:
- MSc Digital Marketing: First Class Honours (1.1), GPA 3.69 — UCD Michael Smurfit Graduate Business School (2021-2022)
- Bachelor of Commerce (1.1) — MCM DAV College, Chandigarh (2017-2020)

Key Skills: LinkedIn Ads, Meta Ads, Google Ads, DV360, SEO, HubSpot, Mailchimp, Marketo (in progress),
Eventbrite, Gleanin, Google Analytics, Looker Studio, Power BI, Tableau, Canva, WordPress,
B2B Campaign Management, Demand Generation, Email Marketing, Event Marketing, Content Marketing
"""


def generate_cover_letter(job: dict) -> dict:
    """Ask Claude to write a cover letter and return structured JSON."""
    prompt = f"""You are an expert cover letter writer. Write a compelling cover letter for this job application.

## Candidate Background
{CANDIDATE_BACKGROUND}

## Job Details
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description:
{(job['description'] or '')[:3000]}

## Style Guide
- Write like a real person, not an AI. Sound natural and conversational, not polished or corporate.
- NEVER use em dashes (—). Use commas, full stops, or rewrite the sentence instead.
- NEVER use phrases like "I am writing to apply", "I am excited to", "I would be a great fit", "leverage", "utilise", "passionate about", "dynamic", "innovative".
- Avoid overly complex sentence structures. Keep sentences direct and clear.
- Reference 1-2 specific things about the company or role from the job description.
- Connect Areena's strongest relevant experience to the role's key needs.
- 4-5 paragraphs: opening interest, marketing skills fit, company-specific fit, business impact, closing.
- Each paragraph 3-5 sentences, no bullet points.
- End with a confident but natural closing, not overly formal.

## Output Format
Return ONLY valid JSON, no markdown:
{{
  "salutation": "Dear [Company Name] Hiring Team,",
  "paragraphs": [
    "Opening paragraph...",
    "Marketing skills fit paragraph...",
    "Company-specific paragraph...",
    "Business impact paragraph...",
    "Closing paragraph..."
  ]
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ]
    )

    raw = "{" + message.content[0].text.strip()
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    def clean(text: str) -> str:
        return text.replace(" — ", ", ").replace("—", ", ")

    data["salutation"] = clean(data.get("salutation", ""))
    data["paragraphs"] = [clean(p) for p in data.get("paragraphs", [])]
    return data


def run(job: dict) -> str:
    """Generate cover letter and save as PDF. Returns path to saved PDF."""
    print(f"✉️  Writing cover letter for: {job['title']} @ {job['company']}...")

    letter_data = generate_cover_letter(job)
    letter_data["company"] = job["company"]
    letter_data["date"] = datetime.today().strftime("%-d %B %Y")

    company_slug = job["company"].replace(" ", "_").replace("/", "-")[:30]
    title_slug   = job["title"].replace(" ", "_").replace("/", "-")[:30]
    filename     = f"coverletter_{title_slug}_{company_slug}.pdf"
    output_path  = os.path.join(OUTPUT_DIR, filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_coverletter_pdf(letter_data, output_path)

    word_count = sum(len(p.split()) for p in letter_data["paragraphs"])
    print(f"  ✅ Cover letter saved: {output_path} ({word_count} words)")
    return output_path


if __name__ == "__main__":
    sample_job = {
        "id": 1,
        "title": "B2B Marketing Manager",
        "company": "TestCo",
        "location": "Dublin, Ireland",
        "description": "Looking for a B2B Marketing Manager with experience in demand generation, paid media, and HubSpot.",
    }
    path = run(sample_job)
    print(f"Generated: {path}")
