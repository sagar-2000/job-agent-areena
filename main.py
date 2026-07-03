"""
Job Application Agent — Main Orchestrator
Runs the full pipeline: scrape → score → tailor → email digest
Also runs follow-up checks daily.

Usage:
    python main.py              # Run once immediately
    python main.py --schedule   # Run on daily schedule (8am)
"""

import os
import sys
import argparse
import schedule
import time
from dotenv import load_dotenv

from startup import restore_gmail_token, ensure_data_dirs
from tracker.db import init_db, reset_parse_errors, reset_all_scores, get_top_scored_jobs
from scraper.indeed import run as scrape_indeed
from scraper.linkedin import run as scrape_linkedin
from agent.scorer import run as score_jobs
from agent.resume_tailor import run as tailor_resume
from agent.cover_letter import run as write_cover_letter
from emailer.digest import send_digest
from emailer.followup import run as check_followups

load_dotenv()


def run_pipeline():
    """Full daily pipeline."""
    print("\n" + "="*60)
    print("🤖 JOB APPLICATION AGENT — STARTING PIPELINE")
    print("="*60 + "\n")

    # Step 1: Scrape jobs
    print("📡 STEP 1: Scraping job listings...\n")
    scrape_indeed()
    scrape_linkedin()

    # Step 2: Score jobs with Claude
    print("\n🧠 STEP 2: Scoring jobs against your profile...\n")
    top_jobs = score_jobs()

    if not top_jobs:
        print("\n😕 No strong matches today. Will try again tomorrow.")
        send_digest([])
        return

    # Step 3: Tailor resume + cover letter for each top job
    print(f"\n✍️  STEP 3: Preparing applications for {len(top_jobs)} top match(es)...\n")
    jobs_data = []

    for job in top_jobs:
        resume_path = tailor_resume(job)
        cover_letter_path = write_cover_letter(job)
        jobs_data.append({
            "job": job,
            "score": job["score"],
            "score_reason": job["score_reason"],
            "resume_path": resume_path,
            "cover_letter_path": cover_letter_path,
        })

    # Step 4: Send email digest
    print("\n📧 STEP 4: Sending daily digest email...\n")
    send_digest(jobs_data)

    # Step 5: Check for follow-ups
    print("\n📬 STEP 5: Checking for stale applications to follow up...\n")
    check_followups()

    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Job Application Agent")
    parser.add_argument("--schedule", action="store_true", help="Run on daily schedule")
    parser.add_argument("--rescore", action="store_true", help="Reset parse errors and re-score existing jobs")
    parser.add_argument("--digest-only", action="store_true", help="Skip scraping, use already-scored top jobs and re-send digest")
    args = parser.parse_args()

    # Restore cloud credentials and ensure dirs exist
    restore_gmail_token()
    ensure_data_dirs()

    # Always init DB first
    init_db()

    if args.digest_only:
        print("📬 Digest-only mode — using existing scored jobs...\n")
        top_jobs = get_top_scored_jobs()
        if not top_jobs:
            print("No scored jobs found. Run without --digest-only first.")
            return
        jobs_data = []
        for job in top_jobs:
            resume_path = tailor_resume(job)
            cover_letter_path = write_cover_letter(job)
            jobs_data.append({
                "job": job,
                "score": job["score"],
                "score_reason": job["score_reason"],
                "resume_path": resume_path,
                "cover_letter_path": cover_letter_path,
            })
        send_digest(jobs_data)
        return

    if args.rescore:
        reset_all_scores()
        top_jobs = score_jobs()
        print(f"\nTop matches: {[j['title'] + ' @ ' + j['company'] for j in top_jobs]}")

        if not top_jobs:
            print("No matches above threshold.")
            return

        # Continue to resume + cover letter + email
        print(f"\n✍️  Preparing applications for {len(top_jobs)} top match(es)...\n")
        jobs_data = []
        for job in top_jobs:
            resume_path = tailor_resume(job)
            cover_letter_path = write_cover_letter(job)
            jobs_data.append({
                "job": job,
                "score": job["score"],
                "score_reason": job["score_reason"],
                "resume_path": resume_path,
                "cover_letter_path": cover_letter_path,
            })

        print("\n📧 Sending digest email...\n")
        send_digest(jobs_data)
        return

    if args.schedule:
        print("⏰ Scheduling daily run at 8:00 AM...")
        schedule.every().day.at("08:00").do(run_pipeline)
        print("Agent is running. Press Ctrl+C to stop.\n")
        run_pipeline()  # Run once immediately on start
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_pipeline()


if __name__ == "__main__":
    main()
