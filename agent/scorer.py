"""
Claude-powered job scorer — Areena Taneja's agent.
Scores each job 1-10 against her B2B marketing profile.
Jobs scoring >= SCORE_THRESHOLD are surfaced in the digest.
"""

import os
import sys
import json
import anthropic
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tracker.db import get_unscored_jobs, update_job_score

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCORE_THRESHOLD = 3


def load_user_profile() -> dict:
    profile_path = os.path.join(os.path.dirname(__file__), "../data/profile.json")
    with open(profile_path, "r") as f:
        return json.load(f)


def score_job(job: dict, profile: dict) -> tuple[int, str]:
    """
    Ask Claude to score a job listing against Areena's marketing profile.
    Returns (score: int, reason: str).
    """
    prompt = f"""You are a job matching assistant. Score how well this job matches the candidate profile.

## Candidate Profile
{json.dumps(profile, indent=2)}

## Job Listing
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Salary: {job['salary'] or 'Not specified'}
Description:
{(job['description'] or '')[:2000]}

## Scoring Rules
Score this job 1-10. Apply these checks IN ORDER:

STEP 1 — Level check (hard gate). The candidate has 4+ years of B2B marketing experience. She is NOT looking for junior/entry-level/intern/graduate roles.
- If the title or description indicates Intern, Trainee, Graduate, Apprentice, Entry-level: score 1-2 MAXIMUM. Say so explicitly.
- If the role requires 7+ years of experience, or is C-suite (VP, CMO, Chief Marketing Officer, Director of Marketing at a very senior level): score 1-2 MAXIMUM.
- Senior, Manager, Lead, Specialist, Executive, Coordinator levels: all fine — proceed to Step 2.

STEP 2 — Role relevance (only if Step 1 passed).
Give a HIGH score (7-10) if:
- Title or role involves: Marketing Manager, B2B Marketing, Campaign Manager, Marketing Lead, Events Marketing, Digital Marketing, Paid Media, Demand Generation, Marketing Communications, Content Marketing, Performance Marketing, Marketing Specialist, Marketing Executive
- Job requires skills matching candidate: LinkedIn Ads, Meta Ads, Google Ads, HubSpot, email marketing, demand generation, B2B campaigns, event marketing, content creation
- Located in Dublin or Remote

Give a MEDIUM score (5-6) if:
- Role is marketing-adjacent (e.g. Communications Manager, PR, Partnerships, Brand) and still involves campaign execution or digital skills

Give a LOW score (1-4) if:
- Title is completely unrelated (sales rep, engineer, accountant, developer, nurse, driver, etc.)
- Pure sales, finance, HR, or technical roles with no marketing component

IGNORE salary if not specified — do NOT penalise for missing salary.

Respond ONLY with valid JSON:
{{
  "score": <integer 1-10>,
  "reason": "<one sentence explaining the score>"
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ]
    )

    try:
        raw = "{" + message.content[0].text.strip()
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
        return int(result["score"]), result["reason"]
    except Exception as e:
        print(f"  ⚠️  Failed to parse score for job {job['id']}: {e} | Raw: {message.content[0].text[:100]!r}")
        return 0, "Parse error"


def run() -> list[dict]:
    """Score all unscored jobs. Returns jobs that scored >= threshold."""
    profile = load_user_profile()
    jobs = get_unscored_jobs()

    if not jobs:
        print("✅ No unscored jobs to process.")
        return []

    print(f"🧠 Scoring {len(jobs)} jobs with Claude...")
    top_jobs = []

    for job in jobs:
        score, reason = score_job(job, profile)
        update_job_score(job["id"], score, reason)

        indicator = "✅" if score >= SCORE_THRESHOLD else "❌"
        print(f"  {indicator} [{score}/10] {job['title']} @ {job['company']} — {reason}")

        if score >= SCORE_THRESHOLD:
            job["score"] = score
            job["score_reason"] = reason
            top_jobs.append(job)

    print(f"\n🎯 {len(top_jobs)} jobs scored {SCORE_THRESHOLD}+/10.")
    return top_jobs


if __name__ == "__main__":
    results = run()
    print(f"\nTop matches: {[j['title'] + ' @ ' + j['company'] for j in results]}")
