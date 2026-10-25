"""ذخیره‌سازی محلی با SQLite (بدون وابستگی اضافه)."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import Profile


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    readiness INTEGER NOT NULL,
                    rule_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_assessments_profile
                    ON assessments(profile_id, created_at DESC);
                """
            )

    # ------------------------------------------------------------ profiles
    def save_profile(self, profile: Profile, profile_id: str | None = None) -> str:
        pid = profile_id or str(uuid.uuid4())
        now = _now()
        payload = json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))
        with self._connect() as conn:
            row = conn.execute("SELECT created_at FROM profiles WHERE id = ?", (pid,)).fetchone()
            if row:
                conn.execute(
                    "UPDATE profiles SET name = ?, payload = ?, updated_at = ? WHERE id = ?",
                    (profile.name, payload, now, pid),
                )
            else:
                conn.execute(
                    "INSERT INTO profiles (id, name, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (pid, profile.name, payload, now, now),
                )
        return pid

    def get_profile(self, profile_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "profile": Profile.model_validate_json(row["payload"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_profiles(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.created_at, p.updated_at,
                       (SELECT COUNT(*) FROM assessments a WHERE a.profile_id = p.id) AS assessments,
                       (SELECT MAX(a.created_at) FROM assessments a WHERE a.profile_id = p.id) AS last_assessment
                FROM profiles p ORDER BY p.updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_profile(self, profile_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        return cur.rowcount > 0

    # ---------------------------------------------------------- assessments
    def save_assessment(
        self,
        profile_id: str,
        results: list[dict],
        readiness: int,
        rule_date: str,
    ) -> str:
        aid = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO assessments (id, profile_id, payload, readiness, rule_date, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (aid, profile_id, json.dumps(results, ensure_ascii=False, separators=(",", ":")), readiness, rule_date, _now()),
            )
        return aid

    def get_assessment(self, assessment_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "results": json.loads(row["payload"]),
            "readiness": row["readiness"],
            "rule_date": row["rule_date"],
            "created_at": row["created_at"],
        }

    def latest_assessment(self, profile_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM assessments WHERE profile_id = ? ORDER BY created_at DESC LIMIT 1",
                (profile_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "results": json.loads(row["payload"]),
            "readiness": row["readiness"],
            "rule_date": row["rule_date"],
            "created_at": row["created_at"],
        }

    def list_assessments(self, profile_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, readiness, rule_date, created_at FROM assessments"
                " WHERE profile_id = ? ORDER BY created_at DESC",
                (profile_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        with self._connect() as conn:
            profiles = conn.execute("SELECT COUNT(*) AS c FROM profiles").fetchone()["c"]
            assessments = conn.execute("SELECT COUNT(*) AS c FROM assessments").fetchone()["c"]
        return {"profiles": profiles, "assessments": assessments}
