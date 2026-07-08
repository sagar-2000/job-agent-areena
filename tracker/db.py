"""
SQLite database for tracking jobs and application status.
"""

import sqlite3
import os
from datetime import datetime

# On Railway, mount a volume at /data and set DATA_DIR=/data
# Locally falls back to the repo's data/ folder
_DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "../data"))
DB_PATH = os.path.join(_DATA_DIR, "jobs.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            job_id TEXT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            url TEXT NOT NULL UNIQUE,
            description TEXT,
            score INTEGER DEFAULT 0,
            score_reason TEXT,
            status TEXT DEFAULT 'new',
            -- new | approved | applied | followed_up | rejected | offer
            applied_at TEXT,
            last_action_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER REFERENCES jobs(id),
            resume_path TEXT,
            cover_letter TEXT,
            follow_up_sent INTEGER DEFAULT 0,
            follow_up_sent_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


def insert_job(job: dict) -> int | None:
    """
    Insert a job if it doesn't already exist.
    Deduplicates by URL first, then by (title + company) to catch
    the same job posted on multiple platforms (Indeed + LinkedIn).
    Returns the row id or None if it already existed.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO jobs (source, job_id, title, company, location, salary, url, description)
            VALUES (:source, :job_id, :title, :company, :location, :salary, :url, :description)
        """, job)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # duplicate URL
    finally:
        conn.close()


def get_top_scored_jobs(threshold: int = 6) -> list[dict]:
    """Return already-scored jobs above threshold, deduped by title+company."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        WHERE score >= ? AND status = 'new'
        GROUP BY LOWER(TRIM(title)), LOWER(TRIM(company))
        ORDER BY score DESC
    """, (threshold,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_unscored_jobs() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    # Include jobs with score=0 regardless of score_reason (catches parse errors too)
    cursor.execute("SELECT * FROM jobs WHERE score = 0 AND status = 'new'")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def reset_parse_errors():
    """Reset jobs that failed to score so they can be retried."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET score = 0, score_reason = NULL WHERE score_reason = 'Parse error'")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"🔄 Reset {count} jobs with parse errors for re-scoring.")


def reset_all_scores():
    """Reset ALL job scores so they can be re-scored with updated profile."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET score = 0, score_reason = NULL WHERE status = 'new'")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"🔄 Reset all {count} jobs for re-scoring.")


def update_job_score(job_id: int, score: int, reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jobs SET score = ?, score_reason = ? WHERE id = ?",
        (score, reason, job_id)
    )
    conn.commit()
    conn.close()


def get_approved_jobs() -> list[dict]:
    """Jobs the user approved for application."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE status = 'approved'")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_stale_applications(days: int = 7) -> list[dict]:
    """Applications with no follow-up after N days."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.*, a.id as app_id, a.follow_up_sent
        FROM jobs j
        JOIN applications a ON a.job_id = j.id
        WHERE j.status = 'applied'
          AND a.follow_up_sent = 0
          AND julianday('now') - julianday(j.applied_at) >= ?
    """, (days,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def mark_applied(job_id: int, resume_path: str, cover_letter: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "UPDATE jobs SET status = 'applied', applied_at = ?, last_action_at = ? WHERE id = ?",
        (now, now, job_id)
    )
    cursor.execute("""
        INSERT INTO applications (job_id, resume_path, cover_letter)
        VALUES (?, ?, ?)
    """, (job_id, resume_path, cover_letter))
    conn.commit()
    conn.close()


def mark_follow_up_sent(app_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "UPDATE applications SET follow_up_sent = 1, follow_up_sent_at = ? WHERE id = ?",
        (now, app_id)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
