"""
Cloud startup helper.
Restores token.json from GMAIL_TOKEN_B64 environment variable before the
pipeline runs. This lets us store the OAuth token securely as a Railway
environment variable instead of committing the file to git.
"""

import os
import base64

TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")


def restore_gmail_token():
    b64 = os.getenv("GMAIL_TOKEN_B64")
    if not b64:
        return  # running locally with token.json already on disk
    if os.path.exists(TOKEN_PATH):
        return  # already restored

    try:
        decoded = base64.b64decode(b64).decode("utf-8")
        with open(TOKEN_PATH, "w") as f:
            f.write(decoded)
        print("✅ Gmail token restored from environment variable.")
    except Exception as e:
        print(f"⚠️  Could not restore Gmail token: {e}")


def ensure_data_dirs():
    """Make sure data directories exist (Railway ephemeral filesystem)."""
    data_dir = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "resumes"), exist_ok=True)


if __name__ == "__main__":
    restore_gmail_token()
    ensure_data_dirs()
