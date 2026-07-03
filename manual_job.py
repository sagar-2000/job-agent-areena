"""
Manual job entry — paste a URL or job details and get a tailored
resume + cover letter emailed to you instantly. No Apify needed.

Usage:
    # From a URL (fetches and parses the job page)
    python manual_job.py --url "https://ie.indeed.com/viewjob?jk=abc123"

    # From manual details
    python manual_job.py --title "Data Analyst" --company "Stripe" --location "Dublin" --url "https://stripe.com/jobs/123"

    # Paste a full job description interactively
    python manual_job.py --title "Data Analyst" --company "Stripe" --location "Dublin" --url "https://stripe.com/jobs/123" --description "We are looking for..."
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
load_dotenv()

from startup import restore_gmail_token, ensure_data_dirs
from agent.scorer import score_job, load_user_profile
from agent.resume_tailor import run as tailor_resume
from agent.cover_letter import run as write_cover_letter
from emailer.digest import send_digest


def fetch_job_from_url(url: str) -> dict:
    """Fetch and extract job details from a URL using Claude."""
    import anthropic
    print(f"🌐 Fetching job from URL: {url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        # Take first 8000 chars to avoid token limits
        page_text = response.text[:8000]
    except Exception as e:
        print(f"⚠️  Could not fetch URL ({e}). Please provide --title, --company, --description manually.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Extract job details from this webpage HTML/text. Return ONLY valid JSON:
{{
  "title": "job title",
  "company": "company name",
  "location": "city, country",
  "salary": "salary range or null",
  "description": "full job description text (first 2000 chars)"
}}

Webpage content:
{page_text}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ]
    )

    raw = "{" + message.content[0].text.strip()
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        # Extract just the JSON object in case Claude added extra text
        start = raw.index("{")
        end = raw.rindex("}") + 1
        data = json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        print("⚠️  Could not auto-extract job details (LinkedIn often blocks scraping without login).")
        print("Please enter the details manually instead:\n")
        title = input("Job title: ").strip()
        company = input("Company: ").strip()
        loc = input("Location (default: Dublin, Ireland): ").strip() or "Dublin, Ireland"
        print("Paste the job description, then press Enter twice when done:\n")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        data = {
            "title": title,
            "company": company,
            "location": loc,
            "salary": None,
            "description": "\n".join(lines).strip(),
        }

    data["url"] = url
    data["source"] = "manual"
    data["id"] = None
    return data


def build_job_from_args(args) -> dict:
    """Build a job dict from command line arguments."""
    description = args.description or ""

    if not description:
        print("📝 Paste the job description below. Press Enter twice when done:\n")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        description = "\n".join(lines).strip()

    return {
        "id": None,
        "source": "manual",
        "title": args.title,
        "company": args.company,
        "location": args.location or "Dublin, Ireland",
        "salary": args.salary or None,
        "url": args.url or f"https://manual-entry/{args.company}/{args.title}".replace(" ", "-"),
        "description": description,
    }


def main():
    parser = argparse.ArgumentParser(description="Manually add a job and get tailored resume + cover letter emailed")
    parser.add_argument("--url", help="Job listing URL (auto-fetches details)")
    parser.add_argument("--title", help="Job title")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--location", help="Location (default: Dublin, Ireland)")
    parser.add_argument("--salary", help="Salary range (optional)")
    parser.add_argument("--description", help="Job description text (optional, will prompt if not provided)")
    args = parser.parse_args()

    # Validate args
    if not args.url and not (args.title and args.company):
        print("❌ Provide either --url OR both --title and --company")
        parser.print_help()
        sys.exit(1)

    restore_gmail_token()
    ensure_data_dirs()

    # Build job dict
    if args.url and not args.title:
        job = fetch_job_from_url(args.url)
        # Allow overrides
        if args.title:    job["title"] = args.title
        if args.company:  job["company"] = args.company
        if args.location: job["location"] = args.location
        if args.salary:   job["salary"] = args.salary
    else:
        job = build_job_from_args(args)
        if args.url:
            job["url"] = args.url

    print(f"\n📋 Job: {job['title']} @ {job['company']} ({job['location']})")

    # Score it
    print("🧠 Scoring job against your profile...")
    profile = load_user_profile()
    score, reason = score_job(job, profile)
    job["score"] = score
    job["score_reason"] = reason
    print(f"   ⭐ Score: {score}/10 — {reason}")

    # Tailor resume + cover letter
    print("\n✍️  Tailoring resume and cover letter...")
    resume_path = tailor_resume(job)
    cover_letter_path = write_cover_letter(job)

    # Send email
    print("\n📧 Sending email digest...")
    jobs_data = [{
        "job": job,
        "score": score,
        "score_reason": reason,
        "resume_path": resume_path,
        "cover_letter_path": cover_letter_path,
    }]
    send_digest(jobs_data)

    print("\n✅ Done! Check your inbox.")


if __name__ == "__main__":
    main()
