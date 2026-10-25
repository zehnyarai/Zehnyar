"""مدل‌های خروجی موتور ارزیابی مهاجرت.

هر برنامه (مسیر مهاجرتی) با یک ``ProgramResult`` توصیف می‌شود تا رابط کاربری،
مقایسه و خروجی JSON همه از یک ساختار واحد استفاده کنند.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["eligible", "potential", "needs_job_offer", "ineligible"]
Severity = Literal["blocker", "major", "minor", "info"]


class Factor(BaseModel):
    """یک عامل امتیازآور یا شرط کلیدی."""

    key: str
    label: str
    value: str
    points: float | None = None
    max_points: float | None = None
    note: str | None = None


class Gap(BaseModel):
    """شکاف بین وضعیت فعلی و شرط برنامه، همراه با راه‌حل."""

    key: str
    label: str
    severity: Severity
    detail: str
    fix: str
    impact: int = 0  # تأثیر تقریبی بر آمادگی (۰ تا ۱۰۰)


class CostItem(BaseModel):
    label: str
    amount: float
    currency: str
    note: str | None = None
    approximate: bool = False
    refundable: bool = False


class Step(BaseModel):
    phase: str
    title: str
    detail: str
    duration: str
    cost: str | None = None
    done: bool = False


class Source(BaseModel):
    title: str
    url: str


class ProgramResult(BaseModel):
    program_id: str
    country_code: str
    country_name: str
    country_flag: str
    program_name: str
    category: str
    summary: str

    status: Status
    status_label: str
    readiness: int = Field(ge=0, le=100)

    score: float | None = None
    score_threshold: float | None = None
    score_unit: str | None = None
    score_note: str | None = None
    band: str | None = None
    band_label: str | None = None

    factors: list[Factor] = []
    gaps: list[Gap] = []
    costs: list[CostItem] = []
    total_cost_eur: float | None = None
    timeline_months: str | None = None
    pr_path: str | None = None
    citizenship_path: str | None = None
    official_url: str
    verified_on: date
    highlights: list[str] = []
    warnings: list[str] = []
    steps: list[Step] = []
    sources: list[Source] = []
    preference_score: float = 0.0

    @property
    def blockers(self) -> list[Gap]:
        return [g for g in self.gaps if g.severity == "blocker"]
