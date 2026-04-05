import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import get_settings


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.settings = get_settings()
        self.db_path = db_path or self.settings.sqlite_db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    text TEXT NOT NULL,
                    features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    resume_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    final_score REAL,
                    breakdown TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id),
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_resume(self, filename: str, text: str, features: dict = None) -> dict:
        resume_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO resumes (id, filename, text, features) VALUES (?, ?, ?, ?)",
                (resume_id, filename, text, json.dumps(features) if features else None),
            )
            conn.commit()
        return self.get_resume(resume_id)

    def get_resume(self, resume_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_resumes(self, resume_ids: List[str] = None) -> List[dict]:
        with self._get_connection() as conn:
            if resume_ids:
                placeholders = ",".join("?" * len(resume_ids))
                query = f"SELECT * FROM resumes WHERE id IN ({placeholders})"
                cursor = conn.execute(query, resume_ids)
            else:
                cursor = conn.execute("SELECT * FROM resumes")
            return [dict(row) for row in cursor.fetchall()]

    def create_job(self, title: str, text: str, features: dict = None) -> dict:
        job_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO jobs (id, title, text, features) VALUES (?, ?, ?, ?)",
                (job_id, title, text, json.dumps(features) if features else None),
            )
            conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_jobs(self) -> List[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs")
            return [dict(row) for row in cursor.fetchall()]

    def save_match(
        self, resume_id: str, job_id: str, final_score: float, breakdown: dict
    ) -> dict:
        match_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO matches (id, resume_id, job_id, final_score, breakdown) VALUES (?, ?, ?, ?, ?)",
                (match_id, resume_id, job_id, final_score, json.dumps(breakdown)),
            )
            conn.commit()
        return {
            "id": match_id,
            "resume_id": resume_id,
            "job_id": job_id,
            "final_score": final_score,
        }

    def get_match(self, resume_id: str, job_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM matches WHERE resume_id = ? AND job_id = ? ORDER BY created_at DESC LIMIT 1",
                (resume_id, job_id),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def delete_resume(self, resume_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            conn.execute("DELETE FROM matches WHERE resume_id = ?", (resume_id,))
            conn.commit()
            return True

    def delete_job(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.execute("DELETE FROM matches WHERE job_id = ?", (job_id,))
            conn.commit()
            return True

    def clear_all_resumes(self) -> int:
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM matches WHERE resume_id IN (SELECT id FROM resumes)"
            )
            conn.execute("DELETE FROM resumes")
            conn.commit()
            cursor = conn.execute("SELECT changes()")
            return cursor.fetchone()[0]

    def clear_all_jobs(self) -> int:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM matches WHERE job_id IN (SELECT id FROM jobs)")
            conn.execute("DELETE FROM jobs")
            conn.commit()
            cursor = conn.execute("SELECT changes()")
            return cursor.fetchone()[0]

    def clear_all(self) -> dict:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM matches")
            conn.execute("DELETE FROM resumes")
            conn.execute("DELETE FROM jobs")
            conn.commit()
            return {
                "resumes_deleted": True,
                "jobs_deleted": True,
                "matches_deleted": True,
            }


db = Database()
