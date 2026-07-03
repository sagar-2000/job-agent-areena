"""
Wellfound (AngelList) job scraper using Apify.
Searches for roles matching your criteria and stores them in the DB.
"""

import os
import sys
from apify_client import ApifyClient
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tracker.db import insert_job

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
TARGET_ROLE = os.getenv("TARGET_ROLE", "Software Engineer")
TARGET_LOCATION = os.getenv("TARGET_LOCATION", "Remote")


def scrape_wellfound(role: str = None, location: str = None) -> list[dict]:
    """
    Scrape Wellfound job listings using Apify actor.
    Returns list of raw job dicts.
    """
    role = role or TARGET_ROLE
    location = location or TARGET_LOCATION

    client = ApifyClient(APIFY_TOKEN)

    print(f"🔍 Scraping Wellfound for: '{role}' in '{location}'...")

    run_input = {
        "countryName": "",        # No country filter — Wellfound is sparse outside the US
        "locationName": "Remote", # Remote roles are most plentiful & Dublin-compatible
        "includeKeyword": role,
        "pagesToFetch": 3,
        "datePosted": "month",
    }

    # Run the Wellfound scraper actor
    run = client.actor("orgupdate/wellfound-jobs-scraper").call(run_input=run_input)

    # run is a Run object — access dataset id via attribute or dict-style depending on SDK version
    dataset_id = run.default_dataset_id if hasattr(run, "default_dataset_id") else run["defaultDatasetId"]

    jobs = []
    for item in client.dataset(dataset_id).iterate_items():
        jobs.append(item)

    print(f"✅ Found {len(jobs)} listings on Wellfound.")

    # Debug: print field names from first result so we can verify normalization
    if jobs:
        print(f"🔍 Sample fields from first result: {list(jobs[0].keys())}")

    return jobs


def normalize_wellfound(raw: dict) -> dict:
    """Map Wellfound actor output to our standard job schema."""
    # Try multiple common field name variations
    return {
        "source": "wellfound",
        "job_id": str(raw.get("id") or raw.get("jobId") or raw.get("job_id") or ""),
        "title": (raw.get("title") or raw.get("jobTitle") or raw.get("job_title") or "").strip(),
        "company": (raw.get("company") or raw.get("companyName") or raw.get("company_name") or raw.get("organizationName") or "").strip(),
        "location": (raw.get("location") or raw.get("locationName") or raw.get("city") or "").strip(),
        "salary": str(raw.get("salary") or raw.get("compensation") or raw.get("salaryRange") or ""),
        "url": (raw.get("url") or raw.get("jobUrl") or raw.get("job_url") or raw.get("applyUrl") or "").strip(),
        "description": (raw.get("description") or raw.get("jobDescription") or raw.get("body") or "").strip(),
    }


def run(role: str = None, location: str = None) -> int:
    """
    Full pipeline: scrape → normalize → store in DB.
    Returns count of new jobs inserted.
    """
    raw_jobs = scrape_wellfound(role, location)
    new_count = 0

    for raw in raw_jobs:
        job = normalize_wellfound(raw)

        # Skip if missing critical fields
        if not job["title"] or not job["url"]:
            continue

        row_id = insert_job(job)
        if row_id:
            new_count += 1
            print(f"  ➕ {job['title']} @ {job['company']}")

    print(f"\n📦 {new_count} new jobs added to database.")
    return new_count


if __name__ == "__main__":
    from tracker.db import init_db
    init_db()
    run()
