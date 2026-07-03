"""
Email digest sender.
Compiles top-scored jobs with tailored resumes + cover letters,
sends a daily digest email for user approval.
"""

import os
import sys
import base64
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")


def build_html_digest(jobs_data: list[dict]) -> str:
    """
    Build a clean HTML email body.
    Each job_data item: { job, score, score_reason, cover_letter, resume_path }
    """
    if not jobs_data:
        return "<p>No strong matches found today. The agent will keep looking.</p>"

    rows = ""
    for i, item in enumerate(jobs_data, 1):
        job = item["job"]
        rows += f"""
        <div style="border:1px solid #e0e0e0; border-radius:8px; padding:20px; margin-bottom:20px; font-family:sans-serif;">
            <h2 style="margin:0 0 4px 0; color:#1a1a1a;">#{i} {job['title']}</h2>
            <p style="margin:0 0 8px 0; color:#555;">
                <strong>{job['company']}</strong> &nbsp;·&nbsp; {job['location'] or 'Location N/A'}
                {f" &nbsp;·&nbsp; {job['salary']}" if job.get('salary') else ""}
            </p>
            <p style="margin:0 0 12px 0;">
                <span style="background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:12px; font-size:13px;">
                    Match Score: {item['score']}/10
                </span>
                &nbsp; <span style="color:#666; font-size:13px;">{item['score_reason']}</span>
            </p>

            <p style="margin:12px 0 4px 0;">
                <a href="{job['url']}" style="background:#0070f3; color:white; padding:8px 16px; border-radius:6px; text-decoration:none; font-size:14px;">
                    View Job →
                </a>
            </p>
            <p style="font-size:12px; color:#999;">
                📄 Resume: {os.path.basename(item.get('resume_path', 'N/A'))}<br>
                ✉️ Cover Letter: {os.path.basename(item.get('cover_letter_path', 'N/A'))}<br>
                Both attached as PDFs.
            </p>
        </div>
        """

    return f"""
    <div style="max-width:700px; margin:0 auto; font-family:sans-serif; color:#1a1a1a;">
        <h1 style="color:#0070f3;">🤖 Your Daily Job Digest</h1>
        <p style="color:#555;">{len(jobs_data)} strong match(es) found today. Review below and reply with job numbers to approve.</p>
        {rows}
        <hr style="border:none; border-top:1px solid #eee; margin:30px 0;">
        <p style="font-size:12px; color:#999;">Powered by your Job Application Agent</p>
    </div>
    """


def print_digest(jobs_data: list[dict]):
    """Print digest to terminal for testing without SendGrid."""
    if not jobs_data:
        print("No strong matches found today.")
        return
    print("\n" + "="*60)
    print("📬 DAILY JOB DIGEST")
    print("="*60)
    for i, item in enumerate(jobs_data, 1):
        job = item["job"]
        print(f"\n#{i} {job['title']} @ {job['company']}")
        print(f"    📍 {job['location']}  |  💰 {job['salary'] or 'Salary not listed'}")
        print(f"    🔗 {job['url']}")
        print(f"    ⭐ Match Score: {item['score']}/10 — {item['score_reason']}")
        print(f"\n    📄 Resume:       {item.get('resume_path', 'N/A')}")
        print(f"    ✉️  Cover Letter: {item.get('cover_letter_path', 'N/A')}")
    print("\n" + "="*60)


def send_digest(jobs_data: list[dict]) -> bool:
    """
    Send the daily digest email via Gmail.
    Returns True on success.
    """
    try:
        from emailer.gmail_sender import send_digest as gmail_send
        return gmail_send(jobs_data)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print_digest(jobs_data)
        return False


if __name__ == "__main__":
    # Test with dummy data
    test_data = [{
        "job": {
            "id": 1,
            "title": "Senior Engineer",
            "company": "TestCo",
            "location": "Remote",
            "salary": "$120k",
            "url": "https://example.com/job/1"
        },
        "score": 9,
        "score_reason": "Strong Python + React match, remote, within salary range.",
        "cover_letter": "Dear Hiring Manager,\n\nThis is a test cover letter...",
        "resume_path": None
    }]
    send_digest(test_data)
