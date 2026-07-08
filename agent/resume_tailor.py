"""
Claude-powered resume tailor — Areena Taneja's agent.
Tailors summary and bullet points to each job while preserving the exact CV structure.
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
    "experiences": [
        {
            "title": "Senior Marketing Lead",
            "company": "Ingenious Media (previously known as Premier Publishing and Events Ltd.)",
            "date": "March 2025 – Present",
            "location": "Dublin, Ireland",
            "bullets": [
                "Lead end-to-end campaign planning and execution for 12+ large-scale B2B conferences and exhibitions annually across Ireland and the UK",
                "Develop integrated multi-channel marketing campaigns across email, social media, paid media, event websites, partner marketing, and attendee communications",
                "Build campaign timelines, rollout plans, and project trackers while coordinating with sales, operations, exhibitors, sponsors, speakers, and external stakeholders",
                "Manage paid campaigns across LinkedIn, Meta, and Google Ads, reducing cost-per-registration by 23% while improving engagement and audience quality",
                "Developed exhibitor marketing and advocacy programmes using Gleanin referral marketing tools, achieving 70%+ participation in co-marketing initiatives",
                "Use automation and AI tools to improve workflow efficiency and reduce campaign turnaround times by approximately 40%",
                "Create and manage audience-facing content, including website copy, email campaigns, social posts, registration communications, promotional guides, exhibitor toolkits, and event collateral",
                "Produce multi-channel campaign assets in-house, including graphics, videos, banners, GIFs, presentations, and branded materials for digital and live event use",
                "Manage webinar and event-related communications, including registration journeys, speaker coordination, target audience promotion, reminder campaigns, and post-event follow-up communications",
                "Support on-site event execution through social media coverage, attendee engagement, exhibitor support, speaker coordination, and real-time content creation",
                "Coordinate closely with external advertising specialists and freelance designers to manage campaign delivery, creative approvals, timelines, and performance optimisation",
                "Monitor and analyse campaign performance across email, paid media, social media, and registration platforms using Google Analytics, Looker Studio, Power BI, and internal reporting dashboards",
                "Produce post-event reports and campaign analysis to evaluate performance, attendee engagement, registration sources, and ROI insights",
                "Manage multiple concurrent projects simultaneously in a fast-paced environment while ensuring campaign deadlines and deliverables are met",
            ],
            "highlights": [
                {
                    "heading": "2026: Key Event Highlight",
                    "text": "Led the end-to-end rebranding of the company from Premier Publishing and Events Ltd. to Ingenious Media, planning and executing the full brand transition across all marketing touchpoints, including campaign assets, event collateral, website copy, email templates, social channels, and exhibitor and sponsor communications, while coordinating with designers, external partners, and senior leadership to ensure a consistent and seamless brand rollout.",
                    "bullets": [],
                },
                {
                    "heading": "Biopharma & Life Sciences Connected Live – Cork",
                    "text": "",
                    "bullets": [
                        "Spearheaded a data-driven, multi-channel demand generation strategy for a flagship industry event with 100+ exhibitors and 14 sponsors, generating 1,096 registrations and converting 73% to in-person attendance (797 attendees)",
                        "Built and optimised a channel acquisition mix including Organic (510), Google Ads (230), Meta (160), Email (44), LinkedIn (30), Speaker promotions (11), and Exhibitor promotions (11)",
                    ],
                },
                {
                    "heading": "Medtech Innovation 2026 – Galway",
                    "text": "",
                    "bullets": [
                        "Spearheaded the launch marketing strategy for a first-time medtech industry event held at Dexcom Stadium, Galway, positioning the event within Ireland's growing medtech ecosystem",
                        "Delivered a 45% attendee conversion rate through integrated campaign execution across email marketing, paid advertising, social media, exhibitor promotion, website communications, and partner marketing",
                    ],
                },
            ],
        },
        {
            "title": "Digital Marketing Executive",
            "company": "Premier Publishing and Events Ltd.",
            "date": "Oct 2022 – March 2025",
            "location": "Dublin, Ireland",
            "bullets": [
                "Managed digital marketing campaigns for 12+ annual B2B conferences, delivering 7,000+ registrations for flagship industry events, including large-scale exhibition events and smaller tabletop industry forums",
                "Updated and maintained 13 event websites and exhibitor portals, ensuring seamless user journeys and up-to-date content",
                "Designed and executed organic and paid social strategies, growing LinkedIn audiences by 176% across event brands",
                "Managed a portfolio of 240+ exhibitors as Exhibitor Administrator, supporting marketing coordination and platform adoption",
                "Curated graphics and posts for the company's social media platforms using Canva and Hootsuite",
                "Designed marketing packs, PR materials, and exhibitor toolkits, achieving 70%+ adoption of ready-made promotional assets",
                "Wrote and built email campaigns, landing pages, and social content aligned with event positioning and audience needs",
                "Reported on campaign performance using Google Analytics, Looker Studio, and Power BI, informing optimisation decisions",
                "Monitored engagement metrics and adjusted messaging and targeting based on performance insights",
                "Supported customer onboarding and engagement by maintaining information hubs, updating portals, and ensuring users could successfully access and use platforms",
            ],
            "highlights": [],
        },
    ],
    "education": [
        {
            "degree": "MSc Digital Marketing: First Class Honours (1.1) - GPA 3.69",
            "university": "UCD Michael Smurfit Graduate Business School",
            "date": "2021 - 2022",
            "location": "Dublin, Ireland",
            "modules": "Corporate Marketing Strategy, Consumer Insights & Analytics, Consumers in a Digital Age, Omnichannel Marketing, Programmatic, Tracking & Attribution, Social Media Marketing, Digital Bus Model & eCommerce",
        },
        {
            "degree": "Bachelors of Commerce • Grade (1.1)",
            "university": "Mehr Chand Mahajan (MCM) DAV College For Women",
            "date": "2017 - 2020",
            "location": "Chandigarh, India",
            "modules": "",
        },
    ],
    "skills": [
        {"category": "Core Marketing", "items": ["B2B Campaign Management", "Multi-Channel Marketing", "End-to-End Campaign Execution", "Content Marketing", "Thought Leadership Promotion", "Demand Generation", "Email Marketing & Segmentation", "Marketing Communications", "Stakeholder & Relationship Management", "Market Research & Analysis"]},
        {"category": "Events & Webinars", "items": ["Event Planning & Management", "Webinar Coordination", "Speaker Briefing", "Exhibitor & Sponsor Management", "On-site Event Support", "Target List Development", "Event Collateral Production"]},
        {"category": "Paid & Digital", "items": ["LinkedIn Ads", "Meta Ads", "Google Ads", "Google Display", "DV360", "SEO", "Paid Media Strategy", "Performance Optimisation"]},
        {"category": "Martech Platforms", "items": ["HubSpot", "Mailchimp", "Marketo (in progress)", "Eventbrite", "Gleanin", "Qualtrics"]},
        {"category": "Analytics", "items": ["Google Analytics", "Looker Studio", "Power BI", "Tableau", "Google Sheets", "Excel"]},
        {"category": "Creative & Content", "items": ["Canva", "WordPress", "Wix", "Shopify", "Blog Writing", "Social Media Curation", "Video & GIF Production"]},
        {"category": "Project Tools", "items": ["ClickUp", "Google Workspace", "Zoom", "Cross-functional Teamwork", "Agile Working"]},
        {"category": "AI & Automation", "items": ["ChatGPT", "Claude", "HubSpot Automation", "Gleanin", "Smart Workflows for Campaign Optimisation"]},
    ],
    "certifications": [
        "Display & Video 360 Certification by Google",
        "Hootsuite Platform Certification",
        "Hootsuite's Social Marketing Certification",
        "Stukent's Mimic Consumer Behaviour",
        "Certified Technical, Financial, Market, and Equity Research Analyst by Magnum Educorporates",
        "Intercultural Development Training Programme at UCD Michael Smurfit Graduate Business School",
        "Global Leadership Programme at UCD Michael Smurfit Graduate Business School",
        "TV Masters from Thinkbox",
    ],
}


def tailor_resume(job: dict) -> dict:
    """
    Ask Claude to tailor only the summary and bullet points.
    Everything else (structure, education, skills, certs, highlights) is preserved as-is.
    """
    prompt = f"""You are an expert resume writer. Tailor this candidate's resume for the specific job below.

## Job Details
Title: {job['title']}
Company: {job['company']}
Description:
{(job['description'] or '')[:3000]}

## Instructions
1. Write a SUMMARY (3-4 sentences) that speaks directly to this role. Always say "4+ years of experience". Mirror keywords from the JD naturally.
2. For each experience, reorder and reword the MAIN BULLETS to highlight the most relevant ones first.
   - Keep exactly the same number of bullets as the original.
   - Do NOT change facts, numbers, dates, company names, or technologies.
   - If the JD mentions something not explicitly in the bullets but clearly part of her experience (e.g. CRM management, brand strategy, stakeholder reporting), you may naturally incorporate it into an existing bullet — do not invent metrics.
   - Keep bullet length similar to originals — do not shorten.
3. Do NOT change or return: highlights, education, skills, certifications. These are preserved exactly.

## Original bullets to tailor

Senior Marketing Lead bullets:
{json.dumps(BASE_RESUME["experiences"][0]["bullets"], indent=2)}

Digital Marketing Executive bullets:
{json.dumps(BASE_RESUME["experiences"][1]["bullets"], indent=2)}

## Output Format
Return ONLY valid JSON (no markdown):
{{
  "summary": "tailored summary here",
  "experience_0_bullets": ["bullet 1", "bullet 2", ...],
  "experience_1_bullets": ["bullet 1", "bullet 2", ...]
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2500,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ]
    )

    raw = "{" + message.content[0].text.strip()
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    tailored = json.loads(raw)

    result = json.loads(json.dumps(BASE_RESUME))  # deep copy
    result["summary"] = tailored["summary"]
    result["experiences"][0]["bullets"] = tailored["experience_0_bullets"]
    result["experiences"][1]["bullets"] = tailored["experience_1_bullets"]
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
        "title": "Marketing Manager",
        "company": "Flynn O'Driscoll",
        "location": "Dublin, Ireland",
        "description": "Looking for a Marketing Manager with experience in B2B campaigns, demand generation, paid media, HubSpot, and stakeholder management.",
    }
    path = run(sample_job)
    print(f"Generated: {path}")
