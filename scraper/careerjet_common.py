"""
Shared Careerjet helpers for Ireland job search — Areena Taneja's agent.
Free public API, no signup wall for basic search volume.
"""

import os
import re
import requests
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

API_URL = "http://public.api.careerjet.net/search"
HEADERS = {
    "Referer": "https://github.com/areena-job-agent",
}

# Areena has 4+ years — reject intern/graduate/trainee roles (overqualified)
JUNIOR_KEYWORDS = [
    "intern", "internship", "graduate", "trainee", "apprentice",
    "entry level", "entry-level", "junior", "jr ", "jr.",
]

MAX_AGE_DAYS = 5


def is_appropriate_level(title: str) -> bool:
    """Reject intern/graduate/trainee titles — Areena is mid-to-senior level."""
    lowered = title.lower()
    return not any(kw in lowered for kw in JUNIOR_KEYWORDS)


def is_recent(date_str: str, max_age_days: int = MAX_AGE_DAYS) -> bool:
    """Check if a Careerjet date string is within the allowed age window."""
    if not date_str:
        return True
    try:
        posted = parsedate_to_datetime(date_str)
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - posted
        return age <= timedelta(days=max_age_days)
    except Exception:
        return True


def fetch_careerjet_page(role: str, location: str, page: int = 1, results_per_page: int = 25) -> list[dict]:
    """Fetch one page of Careerjet Ireland results for a role/location."""
    affid = os.getenv("CAREERJET_AFFID")
    if not affid:
        print("⚠️  CAREERJET_AFFID not set.")
        return []

    params = {
        "locale_code": "en_IE",
        "keywords": role,
        "location": location,
        "affid": affid,
        "user_ip": "192.168.1.1",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "page": page,
        "pagesize": results_per_page,
        "sort": "date",
    }

    try:
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("type") == "ERROR":
            print(f"❌ Careerjet error for '{role}': {data.get('error')}")
            return []

        jobs = data.get("jobs", [])
        junior_rejects = sum(1 for j in jobs if not is_appropriate_level(j.get("title", "")))
        stale_rejects  = sum(1 for j in jobs if not is_recent(j.get("date", "")))
        filtered = [
            j for j in jobs
            if is_appropriate_level(j.get("title", "")) and is_recent(j.get("date", ""))
        ]
        if junior_rejects or stale_rejects:
            print(f"   🚫 Filtered out {junior_rejects} junior/intern-titled, {stale_rejects} stale (>{MAX_AGE_DAYS}d) listing(s).")
        return filtered
    except Exception as e:
        print(f"❌ Careerjet fetch failed for '{role}' page {page}: {e}")
        return []


def normalize_careerjet(job: dict, source: str = "careerjet") -> dict:
    """Normalize a Careerjet job dict to our standard format."""
    description = job.get("description", "")
    description = re.sub(r"</?b>", "", description)
    salary = job.get("salary") or None
    return {
        "source": source,
        "job_id": job.get("url", "")[-40:],
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("locations", "Ireland"),
        "salary": salary,
        "url": job.get("url", ""),
        "description": description[:5000],
    }
