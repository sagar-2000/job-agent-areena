"""
Follow-up tracker.
Checks for applications with no response after 7 days,
drafts a follow-up email and sends it to the user for review.
Uses Gmail API (same as digest).
"""

import os
import sys
import anthropic
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tracker.db import get_stale_applications, mark_follow_up_sent

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
TO_EMAIL = os.getenv("TO_EMAIL")


def draft_followup(job: dict) -> str:
    """Ask Claude to draft a polite follow-up email."""
    prompt = f"""Draft a short, polite follow-up email for a job application that received no response after 7 days.

Job: {job['title']} at {job['company']}
Applied: {job['applied_at']}

The email should:
- Be 3-4 sentences max
- Reiterate genuine interest
- Ask for a status update politely
- Not sound desperate or pushy

Output ONLY the email body (no subject line)."""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def send_followup_digest(stale_jobs: list[dict]):
    """Email the user a digest of follow-ups via Gmail."""
    if not stale_jobs:
        print("✅ No stale applications to follow up on.")
        return

    rows = ""
    drafts = []
    for job in stale_jobs:
        draft = draft_followup(job)
        drafts.append((job, draft))
        rows += f"""
        <div style="border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin-bottom:16px; font-family:sans-serif;">
            <h3 style="margin:0 0 4px 0;">{job['title']} @ {job['company']}</h3>
            <p style="color:#999; font-size:12px;">Applied: {job['applied_at']}</p>
            <h4>Suggested Follow-Up:</h4>
            <div style="background:#f9f9f9; padding:12px; border-radius:6px; font-size:14px; white-space:pre-wrap;">{draft}</div>
            <p><a href="{job['url']}">View original job →</a></p>
        </div>
        """
        mark_follow_up_sent(job["app_id"])

    html_body = f"""
    <div style="max-width:700px; margin:0 auto; font-family:sans-serif;">
        <h1>📬 Follow-Up Reminders</h1>
        <p>{len(stale_jobs)} application(s) haven't heard back in 7+ days. Here are drafted follow-ups:</p>
        {rows}
    </div>
    """

    try:
        from emailer.gmail_sender import get_gmail_service
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"📬 {len(stale_jobs)} follow-up(s) ready to send"
        msg["From"] = TO_EMAIL
        msg["To"] = TO_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        service = get_gmail_service()
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"📧 Follow-up digest sent for {len(stale_jobs)} applications.")
    except Exception as e:
        print(f"❌ Failed to send follow-up digest: {e}")


def run():
    stale = get_stale_applications(days=7)
    print(f"🔍 Found {len(stale)} stale application(s).")
    send_followup_digest(stale)


if __name__ == "__main__":
    run()
