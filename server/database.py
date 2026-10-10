"""SQLite for the single-node pilot. Persistent volume required in production."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return uuid4().hex


@contextmanager
def connect():
    path = Path(os.environ.get("DATABASE_PATH", "storage/pesteyar.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize():
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE,
                password_hash TEXT, role TEXT NOT NULL DEFAULT 'user',
                is_demo INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                subscription_until TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orchards (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL, province TEXT NOT NULL, city TEXT NOT NULL,
                cultivar TEXT NOT NULL, area REAL NOT NULL, trees INTEGER NOT NULL,
                irrigation TEXT NOT NULL, age INTEGER NOT NULL, is_sample INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                orchard_id TEXT REFERENCES orchards(id) ON DELETE SET NULL,
                tree_part TEXT NOT NULL, notes TEXT NOT NULL, data TEXT NOT NULL,
                image_path TEXT, status TEXT NOT NULL, is_sample INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                orchard_id TEXT REFERENCES orchards(id) ON DELETE CASCADE,
                title TEXT NOT NULL, kind TEXT NOT NULL, due_date TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0, is_sample INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                plan TEXT NOT NULL, amount_rial INTEGER NOT NULL, duration_days INTEGER NOT NULL,
                authority TEXT UNIQUE, status TEXT NOT NULL, ref_id TEXT,
                created_at TEXT NOT NULL, paid_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit (
                id TEXT PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL,
                entity_id TEXT, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_orchards_user ON orchards(user_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id, due_date);
            CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at);
        """)
        # Small forward-only migrations for existing pilot databases.
        for table, column, definition in [
            ("payments", "is_sandbox", "INTEGER NOT NULL DEFAULT 0"),
            ("users", "subscription_is_sandbox", "INTEGER NOT NULL DEFAULT 0"),
        ]:
            existing = {r[1] for r in db.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def seed_demo(db, user_id):
    now = now_iso()
    orchard_one, orchard_two = uid(), uid()
    for orchard_id, name, city, cultivar, area, trees, age in [
        (orchard_one, "باغ سبز رفسنجان", "رفسنجان", "اکبری", 5.2, 840, 14),
        (orchard_two, "باغ آفتاب سیرجان", "سیرجان", "احمدآقایی", 3.8, 620, 11),
    ]:
        db.execute(
            "INSERT INTO orchards VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (orchard_id, user_id, name, "کرمان", city, cultivar, area, trees, "قطره‌ای", age, 1, now),
        )
    for delta, title, kind in [
        (0, "بازدید پشت برگ‌ها و ثبت حضور حشرات", "monitoring"),
        (1, "بررسی رطوبت خاک و یکنواختی آبیاری", "irrigation"),
        (3, "هماهنگی آزمایش آب و خاک باغ", "nutrition"),
    ]:
        db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)", (
            uid(), user_id, orchard_one, title, kind,
            (datetime.now(timezone.utc) + timedelta(days=delta)).date().isoformat(), 0, 1, now,
        ))
    for delta, part, title, urgency, image in [
        (1, "برگ", "بررسی اولیه برگ پسته", "medium", "pistachio-leaves.jpg"),
        (3, "میوه", "بررسی اولیه خوشه پسته", "low", "pistachio-harvest.jpg"),
    ]:
        report = sample_report(title, urgency)
        report["sample_image"] = f"/images/{image}"
        db.execute("INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?)", (
            uid(), user_id, orchard_one if part == "برگ" else orchard_two,
            part, "این یک گزارش نمونه است و از تحلیل عکس شما تولید نشده است.",
            json.dumps(report, ensure_ascii=False), None, "complete", 1,
            (datetime.now(timezone.utc) - timedelta(days=delta)).isoformat(),
        ))


def sample_report(title="نمونه گزارش بررسی برگ", urgency="medium"):
    return {
        "title": title,
        "summary": "این گزارش صرفاً نحوه نمایش نتیجه را نشان می‌دهد و هیچ تصویری را تشخیص نداده است. در تحلیل واقعی، مشاهدات، فرضیه‌های محتمل و اقدام بعدی جداگانه نمایش داده می‌شوند.",
        "quality": "نمونه نمایشی", "is_pistachio": None,
        "observations": ["در نسخه واقعی، فقط ویژگی‌های قابل مشاهده در تصویر اینجا ثبت می‌شوند.", "اطلاعات آب، خاک و ریشه از روی عکس قابل اندازه‌گیری نیست."],
        "hypotheses": [{"name": "نیاز به بررسی افتراقی آفت و تنش محیطی", "confidence": 0.62,
                        "evidence": "عدد اطمینان در این نمونه فرضی است؛ امتیاز مدل، دقت آزمایش‌شده نیست.",
                        "next_step": "پشت و روی برگ، الگوی پراکندگی و سابقه آبیاری بررسی شود."}],
        "actions": ["از پشت و روی برگ و کل تاج عکس واضح تهیه کنید.", "زمان شروع علائم و آخرین آبیاری را ثبت کنید.", "پیش از مصرف سم یا کود، با کارشناس محلی مشورت کنید."],
        "needed_tests": ["اگر تغییر رنگ ادامه داشت، آزمایش برگ، خاک و آب طبق نظر کارشناس."],
        "follow_up_questions": ["علائم در یک درخت است یا چند بخش باغ؟", "آیا مصرف کود یا سم اخیر داشته‌اید؟"],
        "urgency": urgency, "knowledge_ids": ["sampling", "nutrition", "psylla"],
        "disclaimer": "نمونه نمایشی؛ جایگزین تشخیص حضوری یا آزمایش نیست.",
        "provider": "demo", "knowledge_version": "2026-10-09.1",
    }
