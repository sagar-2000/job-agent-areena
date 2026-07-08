"""
Gmail API sender — sends the daily digest from your own Gmail account.
Emails sent this way never go to spam since they come from your real account.

First-time setup:
1. Go to https://console.cloud.google.com
2. Create a new project → Enable Gmail API
3. Create OAuth credentials (Desktop App) → Download as credentials.json
4. Place credentials.json in the job-agent/ root directory
5. Run this file once: python emailer/gmail_sender.py
   → Opens browser to authorize → saves token.json for future runs
"""

import os
import base64
import pickle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")
# On Railway the startup.py restores token.json to the repo root from GMAIL_TOKEN_B64
TOKEN_PATH       = os.path.join(os.path.dirname(__file__), "../token.json")
TO_EMAIL         = os.getenv("TO_EMAIL")


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def build_message(jobs_data: list[dict]) -> MIMEMultipart:
    """Build the email message with HTML body and PDF attachments."""
    to = os.getenv("TO_EMAIL") or TO_EMAIL
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"🤖 Job Digest: {len(jobs_data)} match(es) today"
    msg["From"]    = to
    msg["To"]      = to

    # HTML body
    rows = ""
    for i, item in enumerate(jobs_data, 1):
        job = item["job"]
        rows += f"""
        <div style="border:1px solid #e0e0e0; border-radius:8px; padding:20px; margin-bottom:20px; font-family:sans-serif;">
            <h2 style="margin:0 0 4px 0; color:#1a1a1a;">#{i} {job['title']}</h2>
            <p style="margin:0 0 8px 0; color:#555;">
                <strong>{job['company']}</strong> &nbsp;·&nbsp; {job.get('location') or 'N/A'}
                {f" &nbsp;·&nbsp; {job['salary']}" if job.get('salary') else ""}
            </p>
            <p style="margin:0 0 12px 0;">
                <span style="background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:12px; font-size:13px;">
                    Match Score: {item['score']}/10
                </span>
                &nbsp;<span style="color:#666; font-size:13px;">{item['score_reason']}</span>
            </p>
            <p>
                <a href="{job['url']}" style="background:#0070f3; color:white; padding:8px 16px;
                   border-radius:6px; text-decoration:none; font-size:14px;">View Job →</a>
            </p>
            <p style="font-size:12px; color:#999;">
                📄 Resume: {os.path.basename(item.get('resume_path') or 'N/A')}<br>
                ✉️ Cover Letter: {os.path.basename(item.get('cover_letter_path') or 'N/A')}<br>
                Both attached as PDFs.
            </p>
        </div>
        """

    html = f"""
    <div style="max-width:700px; margin:0 auto; font-family:sans-serif; color:#1a1a1a;">
        <h1 style="color:#0070f3;">🤖 Your Daily Job Digest</h1>
        <p style="color:#555;">{len(jobs_data)} strong match(es) found today.</p>
        {rows}
        <hr style="border:none; border-top:1px solid #eee; margin:30px 0;">
        <p style="font-size:12px; color:#999;">Powered by your Job Application Agent</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    # Attach PDFs
    for item in jobs_data:
        for key in ["resume_path", "cover_letter_path"]:
            path = item.get(key)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    part = MIMEBase("application", "pdf")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(path)}"
                    )
                    msg.attach(part)

    return msg


def build_no_match_message() -> MIMEMultipart:
    """Build a simple no-matches email."""
    to = os.getenv("TO_EMAIL") or TO_EMAIL
    msg = MIMEMultipart("mixed")
    msg["Subject"] = "🤖 Job Digest: No strong matches today"
    msg["From"]    = to
    msg["To"]      = to
    html = """
    <div style="max-width:700px; margin:0 auto; font-family:sans-serif; color:#1a1a1a;">
        <h1 style="color:#0070f3;">🤖 Your Daily Job Digest</h1>
        <p style="color:#555;">No strong marketing matches found today. The agent will keep looking tomorrow.</p>
        <hr style="border:none; border-top:1px solid #eee; margin:30px 0;">
        <p style="font-size:12px; color:#999;">Powered by your Job Application Agent</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    return msg


def send_digest(jobs_data: list[dict]) -> bool:
    """Send digest via Gmail API. Returns True on success."""
    try:
        service = get_gmail_service()
        msg = build_message(jobs_data) if jobs_data else build_no_match_message()
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        to = os.getenv("TO_EMAIL") or TO_EMAIL
        print(f"📧 Digest sent via Gmail to {to}!")
        return True
    except Exception as e:
        print(f"❌ Gmail send failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Gmail authentication...")
    get_gmail_service()
    print("✅ Gmail authenticated successfully! token.json saved.")
