"""Community-submitted migration experiences with pre-publication moderation.

No names, contact details, or profile/assessment data are required. Public
entries are plain text and become visible only after an administrator approves.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from .engine.engine import load_dataset
from .payments import _session_user

router = APIRouter(prefix="/api/experiences", tags=["community experiences"])
ADMIN = APIRouter(prefix="/api/admin/experiences", tags=["experience moderation"])
STAGES = {"planning", "applied", "approved", "refused", "moved", "living"}
MODERATION_STATES = {"pending", "approved", "rejected", "hidden"}
CONTACT_PATTERN = re.compile(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+?\d[\s().-]*){8,})")
URL_PATTERN = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)


def _db_path() -> Path:
    configured = os.getenv("EXPERIENCES_DB_PATH", "").strip()
    if configured:
        path = Path(configured).expanduser().resolve()
    else:
        path = Path(os.getenv("PAYMENTS_DATA_DIR", Path.cwd() / "data")).expanduser().resolve() / "experiences.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    db = sqlite3.connect(_db_path(), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("""
        CREATE TABLE IF NOT EXISTS migration_experiences (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            destination TEXT NOT NULL,
            visa_route TEXT NOT NULL DEFAULT '',
            stage TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            author_hash TEXT NOT NULL,
            moderation_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewed_by TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS experience_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experience_id TEXT NOT NULL,
            reporter_hash TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(experience_id, reporter_hash),
            FOREIGN KEY(experience_id) REFERENCES migration_experiences(id) ON DELETE CASCADE
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS experiences_public_idx ON migration_experiences(moderation_status, created_at DESC)")
    db.execute("CREATE INDEX IF NOT EXISTS experiences_author_idx ON migration_experiences(author_hash, created_at DESC)")
    db.execute("""
        CREATE TABLE IF NOT EXISTS experience_submission_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS experience_submission_events_idx ON experience_submission_events(author_hash, created_at DESC)")
    return db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _clean_text(value: str) -> str:
    # Keep ordinary punctuation and Persian/Latin text, strip control chars.
    return "".join(char for char in value.strip() if char in "\n\t" or ord(char) >= 32)


def _check_public_text(value: str, field: str) -> str:
    cleaned = _clean_text(value)
    if CONTACT_PATTERN.search(cleaned) or URL_PATTERN.search(cleaned):
        raise HTTPException(422, f"{field} must not include contact details or external links")
    return cleaned


def _require_admin(request: Request) -> str:
    username = _session_user(request)
    if not username:
        raise HTTPException(401, "Admin login required")
    return username


class ExperienceSubmission(BaseModel):
    title: str = Field(min_length=8, max_length=100)
    body: str = Field(min_length=80, max_length=3000)
    destination: str = Field(min_length=2, max_length=2)
    visaRoute: str = Field(default="", max_length=80)
    stage: str
    displayName: str = Field(default="", max_length=32)

    @field_validator("stage")
    @classmethod
    def valid_stage(cls, value: str) -> str:
        if value not in STAGES:
            raise ValueError("Unsupported experience stage")
        return value


class ExperienceReport(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ModerationUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in MODERATION_STATES - {"pending"}:
            raise ValueError("Unsupported moderation status")
        return value


def _public_item(row: sqlite3.Row, can_delete: bool = False, reports: int = 0) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "destination": row["destination"],
        "visaRoute": row["visa_route"],
        "stage": row["stage"],
        "displayName": row["display_name"] or None,
        "createdAt": row["created_at"],
        "canDelete": can_delete,
        "reportCount": reports,
        "moderationStatus": row["moderation_status"],
    }


@router.get("")
def list_public_experiences(
    destination: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    client_token: Optional[str] = Header(default=None, alias="X-Experience-Client-Token"),
):
    db = _connect()
    try:
        token_hash = _hash_token(client_token) if client_token else None
        clauses = ["(e.moderation_status='approved' OR e.author_hash=?)"] if token_hash else ["e.moderation_status='approved'"]
        params: list = [token_hash] if token_hash else []
        if destination:
            clauses.append("e.destination=?")
            params.append(destination.upper())
        if stage:
            if stage not in STAGES:
                raise HTTPException(422, "Unsupported experience stage")
            clauses.append("e.stage=?")
            params.append(stage)
        rows = db.execute(
            "SELECT e.*, (SELECT COUNT(*) FROM experience_reports r WHERE r.experience_id=e.id) AS reports "
            "FROM migration_experiences e WHERE " + " AND ".join(clauses) +
            " ORDER BY e.created_at DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        items = [_public_item(row, bool(token_hash and secrets.compare_digest(row["author_hash"], token_hash)), row["reports"]) for row in rows]
        count = db.execute("SELECT COUNT(*) FROM migration_experiences e WHERE " + " AND ".join(clauses), params).fetchone()[0]
        return {"items": items, "count": count, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.post("", status_code=201)
def submit_experience(
    payload: ExperienceSubmission,
    client_token: str = Header(alias="X-Experience-Client-Token", min_length=20, max_length=128),
):
    dataset = load_dataset()
    destinations = {country["code"] for country in dataset["countries"]}
    destination = payload.destination.upper()
    if destination not in destinations:
        raise HTTPException(422, "Unknown destination")
    title = _check_public_text(payload.title, "title")
    body = _check_public_text(payload.body, "body")
    display_name = _check_public_text(payload.displayName, "displayName") if payload.displayName else ""
    visa_route = _check_public_text(payload.visaRoute, "visaRoute") if payload.visaRoute else ""
    if len(title) < 8 or len(body) < 80:
        raise HTTPException(422, "Title or experience is too short")

    author_hash = _hash_token(client_token)
    db = _connect()
    try:
        db.execute("DELETE FROM experience_submission_events WHERE created_at < datetime('now', '-1 day')")
        recent = db.execute(
            "SELECT COUNT(*) FROM experience_submission_events WHERE author_hash=? AND created_at >= datetime('now', '-1 day')",
            (author_hash,),
        ).fetchone()[0]
        if recent >= 5:
            raise HTTPException(429, "Submission limit reached. Please try again later.")
        experience_id = secrets.token_urlsafe(12)
        created_at = _now()
        db.execute(
            "INSERT INTO migration_experiences "
            "(id,title,body,destination,visa_route,stage,display_name,author_hash,moderation_status,created_at) "
            "VALUES (?,?,?,?,?,?,?,?, 'pending',?)",
            (experience_id, title, body, destination, visa_route, payload.stage, display_name, author_hash, created_at),
        )
        db.execute("INSERT INTO experience_submission_events (author_hash,created_at) VALUES (?,?)", (author_hash, created_at))
        db.commit()
        return {"id": experience_id, "status": "pending", "message": "Your experience was submitted for review."}
    finally:
        db.close()


@router.delete("/{experience_id}")
def delete_own_experience(
    experience_id: str,
    client_token: str = Header(alias="X-Experience-Client-Token", min_length=20, max_length=128),
):
    db = _connect()
    try:
        result = db.execute(
            "DELETE FROM migration_experiences WHERE id=? AND author_hash=?",
            (experience_id, _hash_token(client_token)),
        )
        if not result.rowcount:
            raise HTTPException(404, "Experience not found or not owned by this device")
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


@router.post("/{experience_id}/report", status_code=201)
def report_experience(
    experience_id: str,
    payload: ExperienceReport,
    client_token: str = Header(alias="X-Experience-Client-Token", min_length=20, max_length=128),
):
    db = _connect()
    try:
        row = db.execute("SELECT moderation_status FROM migration_experiences WHERE id=?", (experience_id,)).fetchone()
        if not row or row["moderation_status"] != "approved":
            raise HTTPException(404, "Experience not found")
        try:
            db.execute(
                "INSERT INTO experience_reports (experience_id,reporter_hash,reason,created_at) VALUES (?,?,?,?)",
                (experience_id, _hash_token(client_token), _clean_text(payload.reason), _now()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "This experience was already reported from this device")
        db.commit()
        return {"reported": True}
    finally:
        db.close()


@ADMIN.get("")
def list_moderation_queue(
    request: Request,
    status: str = Query("pending"),
    limit: int = Query(100, ge=1, le=300),
):
    _require_admin(request)
    if status not in MODERATION_STATES | {"all", "reported"}:
        raise HTTPException(422, "Unsupported moderation filter")
    db = _connect()
    try:
        where = "" if status == "all" else ("WHERE e.moderation_status='approved' AND EXISTS (SELECT 1 FROM experience_reports x WHERE x.experience_id=e.id)" if status == "reported" else "WHERE e.moderation_status=?")
        params = () if status in {"all", "reported"} else (status,)
        rows = db.execute(
            "SELECT e.*, (SELECT COUNT(*) FROM experience_reports r WHERE r.experience_id=e.id) AS report_count "
            "FROM migration_experiences e " + where + " ORDER BY e.created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item.pop("author_hash", None)
            reasons = db.execute("SELECT reason FROM experience_reports WHERE experience_id=? ORDER BY created_at", (row["id"],)).fetchall()
            item["report_reasons"] = [report["reason"] for report in reasons]
            items.append(item)
        return {"items": items}
    finally:
        db.close()


@ADMIN.post("/{experience_id}/review")
def review_experience(experience_id: str, payload: ModerationUpdate, request: Request):
    username = _require_admin(request)
    db = _connect()
    try:
        result = db.execute(
            "UPDATE migration_experiences SET moderation_status=?, reviewed_at=?, reviewed_by=? WHERE id=?",
            (payload.status, _now(), username, experience_id),
        )
        if not result.rowcount:
            raise HTTPException(404, "Experience not found")
        db.commit()
        return {"status": payload.status}
    finally:
        db.close()
