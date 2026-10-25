"""ساختار جامع ورودی‌ها (پروفایل متقاضی).

فیلدها آگاهانه «مسطح» نگه داشته شده‌اند تا فرم چندمرحله‌ای، API و ذخیره‌سازی
همگی ساده بمانند؛ اما همه‌ی ابعاد مؤثر در ارزیابی مهاجرت پوشش داده می‌شود.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

LanguageLevel = Literal["none", "a1", "a2", "b1", "b2", "c1", "c2"]
EducationLevel = Literal[
    "none", "secondary", "diploma1", "diploma2", "bachelor", "master", "two_or_more", "phd"
]
MaritalStatus = Literal["single", "married", "common_law", "divorced", "widowed"]
Recognition = Literal["full", "partial", "none", "unknown"]


class LanguageProfile(BaseModel):
    """سطح زبان + نمره‌ی آزمون (اختیاری)."""

    level: LanguageLevel = "none"
    test: str = ""
    listening: float | None = None
    reading: float | None = None
    writing: float | None = None
    speaking: float | None = None
    test_date: date | None = None
    clb: int | None = Field(default=None, ge=0, le=12)

    def has_scores(self) -> bool:
        return all(
            v is not None for v in (self.listening, self.reading, self.writing, self.speaking)
        )


class Documents(BaseModel):
    passport_valid_years: float = Field(default=3, ge=0, le=20)
    police_clearance: bool = False
    medical: bool = False
    eca: bool = False
    language_certificate: bool = False
    birth_certificate: bool = False
    marriage_certificate: bool = False
    proof_of_funds: bool = False
    education_transcripts: bool = False
    employment_letters: bool = False


class Profile(BaseModel):
    # ------------------------------------------------ هویت و وضعیت پایه
    name: str = "پروفایل من"
    nationality: str = "IR"
    residence: str = "IR"
    birth_date: date
    marital_status: MaritalStatus = "single"
    spouse_included: bool = False
    dependents: int = Field(default=0, ge=0, le=10)

    # ------------------------------------------------ تحصیلات
    education_level: EducationLevel = "bachelor"
    education_field: str = "stem"  # stem | health | business | arts | education | trades | other
    education_country: str = "IR"
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    eca: bool = False  # ارزیابی مدارک برای کانادا
    recognition: Recognition = "unknown"  # وضعیت شناسایی مدرک در آلمان/هلند
    nz_qualification_level: int = Field(default=0, ge=0, le=10)

    # ------------------------------------------------ زبان‌ها
    english: LanguageProfile = LanguageProfile(level="b2")
    german: LanguageProfile = LanguageProfile(level="none")
    french: LanguageProfile = LanguageProfile(level="none")

    # ------------------------------------------------ سابقه‌ی کاری
    occupation_title: str = ""
    occupation_code: str = ""
    occupation_shortage: bool = False
    total_experience_years: float = Field(default=0, ge=0, le=50)
    experience_last5: float = Field(default=0, ge=0, le=50)
    experience_last7: float = Field(default=0, ge=0, le=50)
    experience_last10: float = Field(default=0, ge=0, le=50)
    canadian_experience_years: float = Field(default=0, ge=0, le=50)
    australian_experience_years: float = Field(default=0, ge=0, le=50)
    nz_experience_years: float = Field(default=0, ge=0, le=50)
    skills_assessment: bool = False  # ارزیابی مهارت استرالیا
    registration_years: float = Field(default=0, ge=0, le=50)  # ثبت حرفه‌ای (NZ)

    # ------------------------------------------------ پیشنهاد شغلی
    has_job_offer: bool = False
    job_offer_country: str = ""
    job_offer_salary: float = Field(default=0, ge=0)
    job_offer_currency: str = "EUR"
    job_offer_recognized_sponsor: bool = False
    job_offer_contract_years: float = Field(default=1, ge=0, le=10)
    job_offer_wage_multiple: float = Field(default=0, ge=0, le=5)  # مضرب میانه‌ی دستمزد (کانادا)
    job_offer_going_rate: bool = True  # نرخ رایج شغل (بریتانیا)
    job_offer_shortage: bool = False

    # ------------------------------------------------ مالی و خانواده
    savings_eur: float = Field(default=0, ge=0)
    monthly_income_eur: float = Field(default=0, ge=0)
    passive_income_eur: float = Field(default=0, ge=0)
    remote_work: bool = False
    spouse_education: EducationLevel = "none"
    spouse_english: LanguageProfile = LanguageProfile(level="none")
    spouse_canadian_experience_years: float = Field(default=0, ge=0, le=50)
    relatives_in: list[str] = []
    prior_stay: list[str] = []

    # ------------------------------------------------ ترجیحات
    target_countries: list[str] = []
    priorities: list[str] = []
    max_budget_eur: float = Field(default=6000, ge=0)
    willing_to_learn_language: bool = True

    documents: Documents = Documents()
    notes: str = ""

    @field_validator("birth_date")
    @classmethod
    def _not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("تاریخ تولد نمی‌تواند در آینده باشد")
        if value.year < 1930:
            raise ValueError("سال تولد معتبر نیست")
        return value

    def age(self, on: date | None = None) -> int:
        on = on or date.today()
        years = on.year - self.birth_date.year
        if (on.month, on.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return max(0, years)


class ProfileRecord(BaseModel):
    id: str
    profile: Profile
    created_at: str
    updated_at: str


class AssessmentRecord(BaseModel):
    id: str
    profile_id: str
    created_at: str
    rule_date: date
    results: list[dict]
    readiness: int
    top_program: str | None = None
