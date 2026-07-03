"""
Ireland job scraper using Careerjet API (page 1).
Free, no hard usage limit for moderate volumes.
Register an affid at: https://www.careerjet.com/partners/register/as-publisher
"""

import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tracker.db import insert_job
from scraper.careerjet_common import fetch_careerjet_page, normalize_careerjet

load_dotenv()

TARGET_LOCATION = os.getenv("TARGET_LOCATION", "Dublin")


def scrape_indeed(role: str, location: str = None) -> list[dict]:
    location = location or TARGET_LOCATION
    print(f"🔍 Scraping Careerjet (p1) for: '{role}' in '{location}'...")
    raw_jobs = fetch_careerjet_page(role, location, page=1, results_per_page=25)
    print(f"✅ Found {len(raw_jobs)} listings.")
    return [normalize_careerjet(j, source="careerjet_p1") for j in raw_jobs]


def run():
    profile_path = os.path.join(os.path.dirname(__file__), "../data/profile.json")
    with open(profile_path) as f:
        profile = json.load(f)

    roles    = profile.get("target_roles", ["Data Analyst"])
    location = TARGET_LOCATION
    total    = 0

    for role in roles:
        jobs = scrape_indeed(role, location)
        for job in jobs:
            if not job["url"]:
                continue
            if insert_job(job):
                print(f"  ➕ {job['title']} @ {job['company']}")
                total += 1

    print(f"📦 {total} new jobs added to database across {len(roles)} role(s).")


if __name__ == "__main__":
    run()
