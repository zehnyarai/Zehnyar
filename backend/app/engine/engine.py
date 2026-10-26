"""Visayar assessment engine.

Declarative rule evaluation shared (by spec) with the TypeScript engine in
mobile/src/core/engine.js.  Every rule kind is documented in docs/engine-spec.md.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared", "dataset.json")

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
CLB_TO_CEFR = [(10, "C2"), (9, "C1"), (7, "B2"), (5, "B1"), (3, "A2"), (0, "A1")]
CEFR_TO_CLB = {"A1": 2, "A2": 4, "B1": 6, "B2": 8, "C1": 9, "C2": 10}
SKILLS = ["listening", "reading", "writing", "speaking"]

_dataset: Optional[dict] = None


def load_dataset() -> dict:
    global _dataset
    if _dataset is None:
        with open(DATASET_PATH, encoding="utf-8") as handle:
            _dataset = json.load(handle)
    return _dataset


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
class Spouse(BaseModel):
    educationId: Optional[str] = None
    languageTestId: Optional[str] = None
    languageClb: Optional[float] = None
    workYears: float = 0


class LanguageResult(BaseModel):
    testId: str
    skills: Dict[str, float] = Field(default_factory=dict)
    cefr: Optional[str] = None


class Work(BaseModel):
    totalYears: float = 0
    overseasYears: float = 0
    inCountryYears: float = 0
    occupationCode: Optional[str] = None
    jobOffer: bool = False
    salaryAnnualLocal: Optional[float] = None
    salaryCurrency: str = "USD"
    licensing: bool = False
    selfEmployedYears: float = 0


class Funds(BaseModel):
    availableUsd: float = 0
    cashUsd: float = 0
    assetsUsd: float = 0


class Adaptability(BaseModel):
    relativeInCountry: bool = False
    priorStudyInCountry: bool = False
    priorWorkInCountry: bool = False
    eca: bool = False


class Profile(BaseModel):
    age: int = 30
    maritalStatus: str = "single"
    spouse: Optional[Spouse] = None
    educationId: str = "bachelor"
    educationStem: bool = False
    languages: List[LanguageResult] = Field(default_factory=list)
    work: Work = Field(default_factory=Work)
    funds: Funds = Field(default_factory=Funds)
    adaptability: Adaptability = Field(default_factory=Adaptability)
    goal: str = "work"
    familySize: int = 1
    investmentUsd: float = 0
    remoteIncomeUsd: float = 0
    startupBacking: bool = False
    studyOffer: bool = False
    recentGraduate: bool = False
    achievement: bool = False
    nomination: bool = False


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------
def clb_to_cefr(clb: float) -> str:
    for floor, label in CLB_TO_CEFR:
        if clb >= floor:
            return label
    return "A1"


def education_rank(dataset: dict, education_id: Optional[str]) -> int:
    for level in dataset["educationLevels"]:
        if level["id"] == education_id:
            return level["rank"]
    return 1


def test_meta(dataset: dict, test_id: Optional[str]) -> Optional[dict]:
    if not test_id:
        return None
    for test in dataset["languageTests"]:
        if test["id"] == test_id:
            return test
    return None


def band_to_clb(thresholds: List[List[float]], value: float) -> float:
    result = 0.0
    for floor, clb in thresholds:
        if value >= floor:
            result = clb
    return result


def normalise_language(dataset: dict, result: LanguageResult) -> Optional[dict]:
    """Return {group, clb, minClb, cefr, testId, skills:{...}} or None."""
    meta = test_meta(dataset, result.testId)
    if not meta:
        return None
    group = meta["group"]
    skills: Dict[str, float] = {}
    if meta["kind"] == "cefr":
        cefr = result.cefr
        if cefr not in CEFR_TO_CLB:
            return None
        clb = float(CEFR_TO_CLB[cefr])
        skills = {s: clb for s in SKILLS}
    elif meta.get("overallOnly"):
        raw = result.skills.get("overall")
        if raw is None:
            return None
        clb = band_to_clb(meta["thresholds"]["overall"], raw)
        skills = {s: clb for s in SKILLS}
    else:
        for skill in SKILLS:
            raw = result.skills.get(skill)
            if raw is None:
                return None
            skills[skill] = band_to_clb(meta["thresholds"][skill], raw)
        clb = min(skills.values())
    return {
        "group": group,
        "testId": result.testId,
        "skills": skills,
        "clb": clb,
        "minClb": min(skills.values()) if skills else clb,
        "cefr": clb_to_cefr(clb),
    }


def resolve_language(dataset: dict, profile: Profile, group: str) -> Optional[dict]:
    candidates = []
    for result in profile.languages:
        normalised = normalise_language(dataset, result)
        if normalised and normalised["group"] == group:
            candidates.append(normalised)
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item["minClb"], item["clb"]))


def fx_rate(dataset: dict, currency: str) -> float:
    entry = dataset["fx"].get(currency)
    return entry["rate"] if entry else 1.0


def to_usd(dataset: dict, amount: Optional[float], currency: str) -> float:
    if amount is None:
        return 0.0
    return amount * fx_rate(dataset, currency)


def occupation(dataset: dict, code: Optional[str]) -> Optional[dict]:
    if not code:
        return None
    for item in dataset["occupations"]:
        if item["noc"] == code:
            return item
    return None


def build_flags(dataset: dict, profile: Profile, country_code: str) -> Dict[str, bool]:
    occ = occupation(dataset, profile.work.occupationCode)
    in_demand = bool(occ and country_code in occ["inDemand"])
    return {
        "jobOffer": profile.work.jobOffer,
        "studyOffer": profile.studyOffer,
        "startupBacking": profile.startupBacking,
        "achievement": profile.achievement,
        "nomination": profile.nomination,
        "licensing": profile.work.licensing,
        "inDemandOccupation": in_demand,
        "educationStem": profile.educationStem or bool(occ and occ.get("stem")),
        "relativeInCountry": profile.adaptability.relativeInCountry,
        "priorStudyInCountry": profile.adaptability.priorStudyInCountry,
        "priorWorkInCountry": profile.adaptability.priorWorkInCountry,
        "spouseLanguage": bool(profile.spouse and (profile.spouse.languageClb or 0) >= 4),
        "eca": profile.adaptability.eca,
        "recentGraduateTop": profile.recentGraduate,
    }


def annual_salary_usd(dataset: dict, profile: Profile) -> float:
    return to_usd(dataset, profile.work.salaryAnnualLocal, profile.work.salaryCurrency)


def within_band(bands: List[List[float]], value: float) -> float:
    """Bands are (floor, points) pairs declared in descending order."""
    for band in sorted(bands, key=lambda item: item[0], reverse=True):
        floor, score = band[0], band[1]
        if value >= floor:
            return float(score)
    return 0.0


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------
def evaluate_rule(dataset: dict, rule: dict, profile: Profile, flags: Dict[str, bool],
                  salary_usd: float, settlement_usd: float) -> float:
    kind = rule["kind"]
    if kind == "age_band":
        for low, high, points in rule["bands"]:
            if low <= profile.age <= high:
                return float(points)
        return 0.0
    if kind == "education_rank":
        rank = education_rank(dataset, profile.educationId)
        mapping = rule["map"]
        by_rank = {education_rank(dataset, eid): pts for eid, pts in mapping.items()}
        return float(by_rank.get(rank, 0))
    if kind == "language_skills":
        lang = resolve_language(dataset, profile, rule["group"])
        if not lang:
            return 0.0
        total = 0.0
        for skill in SKILLS:
            total += within_band(rule["bands"], lang["skills"].get(skill, 0))
        cap = rule.get("cap")
        return min(total, cap) if cap else total
    if kind == "language_best":
        lang = resolve_language(dataset, profile, rule["group"])
        if not lang:
            return 0.0
        return within_band(rule["bands"], lang["minClb"])
    if kind == "experience_band":
        scope = rule.get("scope", "any")
        years = {"any": profile.work.totalYears, "overseas": profile.work.overseasYears,
                 "inCountry": profile.work.inCountryYears}.get(scope, 0)
        occ = occupation(dataset, profile.work.occupationCode)
        teer = rule.get("teer")
        if teer and occ and occ["teer"] not in teer:
            return 0.0
        return within_band(rule["bands"], years)
    if kind == "flag":
        return float(rule["points"]) if flags.get(rule["key"]) else 0.0
    if kind == "salary_band":
        metric = rule.get("metric", "annualSalaryUsd")
        value = salary_usd if metric == "annualSalaryUsd" else 0.0
        return within_band(rule["bands"], value)
    if kind == "numeric_band":
        metric = rule["metric"]
        value = {"investmentUsd": profile.investmentUsd,
                 "remoteIncomeUsd": profile.remoteIncomeUsd}.get(metric, 0.0)
        return within_band(rule["bands"], value)
    if kind == "funds_ratio":
        points = float(rule.get("points", 0))
        if settlement_usd <= 0:
            return points
        ratio = profile.funds.availableUsd / settlement_usd
        return min(points, points * max(0.0, min(1.0, ratio / rule.get("scale", 1.0))))
    if kind == "adaptability":
        total = 0.0
        for factor in rule["factors"]:
            if flags.get(factor):
                total += float(rule["each"])
        cap = rule.get("cap")
        return min(total, cap) if cap else total
    if kind == "spouse":
        if not profile.spouse:
            return 0.0
        parts = rule["parts"]
        total = 0.0
        if "language" in parts:
            total += within_band(parts["language"], profile.spouse.languageClb or 0)
        if "education" in parts:
            total += within_band(parts["education"], education_rank(dataset, profile.spouse.educationId))
        if "work" in parts:
            total += within_band(parts["work"], profile.spouse.workYears or 0)
        cap = rule.get("cap")
        return min(total, cap) if cap else total
    return 0.0


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
def settlement_usd(dataset: dict, visa: dict, family_size: int) -> float:
    table = visa.get("settlement")
    if not table:
        return 0.0
    amounts = table["byFamilySize"]
    index = max(0, min(len(amounts) - 1, family_size - 1))
    return to_usd(dataset, amounts[index], table["currency"])


def chancenkarte_points(dataset: dict, profile: Profile, flags: Dict[str, bool]) -> int:
    points = 0
    rank = education_rank(dataset, profile.educationId)
    if rank >= 4:
        points += 4
    elif rank >= 2:
        points += 2
    de = resolve_language(dataset, profile, "de")
    if de:
        points += 3 if de["minClb"] >= 8 else 2 if de["minClb"] >= 6 else 1
    if profile.work.totalYears >= 5:
        points += 3
    elif profile.work.totalYears >= 2:
        points += 2
    if profile.age < 35:
        points += 2
    elif profile.age < 40:
        points += 1
    if flags.get("inDemandOccupation"):
        points += 1
    return points


def nz_points(dataset: dict, profile: Profile, flags: Dict[str, bool], salary_usd: float) -> int:
    rank = education_rank(dataset, profile.educationId)
    points = 0
    if rank >= 6:
        points += 6
    elif rank >= 5:
        points += 5
    elif rank >= 4:
        points += 4
    elif rank >= 2:
        points += 3
    if salary_usd >= 120000:
        points += 6
    elif salary_usd >= 90000:
        points += 5
    elif salary_usd >= 65000:
        points += 3
    if flags.get("inDemandOccupation"):
        points += 1
    if profile.work.totalYears >= 5:
        points += 1
    return points


def evaluate_gates(dataset: dict, visa: dict, profile: Profile, flags: Dict[str, bool],
                   total_points: float, salary_usd: float, settlement: float) -> List[dict]:
    results = []
    for gate_rule in visa["gates"]:
        kind = gate_rule["kind"]
        advisory = bool(gate_rule.get("advisory"))
        passed = True
        detail_fa = gate_rule.get("failFa", "")
        detail_en = gate_rule.get("failEn", "")

        if kind == "age_gate":
            passed = profile.age <= gate_rule["max"]
        elif kind == "language_gate":
            lang = resolve_language(dataset, profile, gate_rule["group"])
            passed = bool(lang and lang["minClb"] >= gate_rule["minClb"])
        elif kind == "experience_gate":
            if profile.work.totalYears < gate_rule.get("minYears", 0):
                passed = False
            teer = gate_rule.get("teer")
            if teer:
                occ = occupation(dataset, profile.work.occupationCode)
                if occ and occ["teer"] not in teer:
                    passed = False
        elif kind == "points_gate":
            min_points = gate_rule["min"]
            if gate_rule.get("scale"):
                passed = total_points / gate_rule["scale"] >= min_points
            else:
                passed = total_points >= min_points
        elif kind == "funds_gate":
            if settlement > 0:
                passed = profile.funds.availableUsd >= settlement
            if not passed and profile.funds.availableUsd == 0:
                detail_fa = "مبلغ تمکن مالی وارد نشده است."
                detail_en = "Settlement funds have not been entered."
        elif kind == "education_gate":
            rank = education_rank(dataset, profile.educationId)
            passed = rank >= gate_rule.get("minRank", 1)
            if not passed and gate_rule.get("allowItExperience") and profile.work.totalYears >= 3:
                passed = True
        elif kind == "flag_gate":
            passed = bool(flags.get(gate_rule["key"]))
        elif kind == "salary_gate":
            passed = _salary_gate_passes(dataset, gate_rule, profile, salary_usd, flags)
            if profile.work.salaryAnnualLocal is None:
                detail_fa = "حقوق پیشنهادی را وارد کنید تا این شرط بررسی شود."
                detail_en = "Enter the offered salary to evaluate this condition."
        elif kind == "investment_gate":
            required = to_usd(dataset, gate_rule["minAmount"], gate_rule["currency"])
            passed = profile.investmentUsd >= required
        elif kind == "remote_income_gate":
            passed = profile.remoteIncomeUsd >= gate_rule["minMonthlyUsd"]
        elif kind == "custom_points":
            grid = gate_rule["grid"]
            if grid == "chancenkarte":
                passed = chancenkarte_points(dataset, profile, flags) >= gate_rule["min"]
            elif grid == "nz_smc":
                passed = nz_points(dataset, profile, flags, salary_usd) >= gate_rule["min"]
            else:
                passed = True
        if passed:
            continue
        results.append({
            "kind": kind,
            "advisory": advisory,
            "messageFa": detail_fa,
            "messageEn": detail_en,
        })
    return results


def _salary_gate_passes(dataset: dict, gate_rule: dict, profile: Profile,
                        salary_usd: float, flags: Dict[str, bool]) -> bool:
    if profile.work.salaryAnnualLocal is None:
        return False
    required_local = float(gate_rule["minAmount"])
    if gate_rule.get("under30Min") and profile.age < 30:
        required_local = min(required_local, float(gate_rule["under30Min"]))
    if gate_rule.get("reducedMin") and (flags.get("inDemandOccupation") or profile.age <= 30):
        required_local = min(required_local, float(gate_rule["reducedMin"]))
    if gate_rule.get("shortageMin") and flags.get("inDemandOccupation"):
        required_local = min(required_local, float(gate_rule["shortageMin"]))
    if gate_rule.get("newEntrantMin") and profile.age < 26:
        required_local = min(required_local, float(gate_rule["newEntrantMin"]))
    required_usd = to_usd(dataset, required_local, gate_rule["currency"])
    if gate_rule.get("monthly"):
        return salary_usd / 12 >= required_usd
    if gate_rule.get("hourly"):
        return salary_usd / 2080 >= required_usd
    return salary_usd >= required_usd


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
EFFORT = {
    "language": "medium", "funds": "medium", "education": "hard",
    "experience": "hard", "adaptability": "medium", "age": "locked",
}

BAND_FA = [(85, "بسیار قوی"), (70, "قوی"), (55, "متوسط"), (35, "ضعیف"), (0, "بسیار ضعیف")]
BAND_EN = [(85, "Very strong"), (70, "Strong"), (55, "Moderate"), (35, "Weak"), (0, "Very weak")]


def band_label(chance: float, lang: str) -> str:
    table = BAND_FA if lang == "fa" else BAND_EN
    for floor, label in table:
        if chance >= floor:
            return label
    return table[-1][1]


def score_visa(dataset: dict, country: dict, visa: dict, profile: Profile) -> dict:
    flags = build_flags(dataset, profile, country["code"])
    salary_usd = annual_salary_usd(dataset, profile)
    settlement = settlement_usd(dataset, visa, profile.familySize)

    scored = []
    achieved = 0.0
    max_points = 0.0
    categories: Dict[str, Dict[str, float]] = {}
    for crit in visa["criteria"]:
        points = evaluate_rule(dataset, crit["rule"], profile, flags, salary_usd, settlement)
        points = round(min(points, crit["max"]), 2)
        achieved += points
        max_points += crit["max"]
        cat = crit["category"]
        bucket = categories.setdefault(cat, {"achieved": 0.0, "max": 0.0})
        bucket["achieved"] += points
        bucket["max"] += crit["max"]
        scored.append({
            "id": crit["id"],
            "labelFa": crit["labelFa"],
            "labelEn": crit["labelEn"],
            "category": cat,
            "max": crit["max"],
            "score": points,
            "actionFa": crit["actionFa"],
            "actionEn": crit["actionEn"],
            "noteFa": crit.get("noteFa"),
            "noteEn": crit.get("noteEn"),
        })

    achieved = round(achieved, 1)
    max_points = round(max_points, 1)
    ratio = achieved / max_points if max_points else 0.0
    gates = evaluate_gates(dataset, visa, profile, flags, achieved, salary_usd, settlement)
    blockers = [g for g in gates if not g["advisory"]]
    warnings = [g for g in gates if g["advisory"]]
    pass_ok = achieved >= visa["passMark"]

    if blockers:
        chance = 5 + 26 * ratio * max(0.35, 1 - 0.12 * min(len(blockers), 4))
    else:
        chance = ratio * 100 * (0.62 + 0.38 * visa["selectivity"])
        if not pass_ok:
            chance *= 0.72
    chance = round(max(3.0, min(96.0, chance)), 1)

    return {
        "visaId": visa["id"],
        "countryCode": country["code"],
        "visaNameFa": visa["nameFa"],
        "visaNameEn": visa["nameEn"],
        "visaType": visa["type"],
        "achieved": achieved,
        "maxPoints": max_points,
        "passMark": visa["passMark"],
        "readiness": round(ratio * 100, 1),
        "chance": chance,
        "bandFa": band_label(chance, "fa"),
        "bandEn": band_label(chance, "en"),
        "blockers": [g for g in blockers],
        "warnings": warnings,
        "eligible": not blockers,
        "criteria": scored,
        "radar": {cat: {"achieved": round(v["achieved"], 1), "max": v["max"],
                        "percent": round(100 * v["achieved"] / v["max"], 1) if v["max"] else 0}
                  for cat, v in categories.items()},
        "settlementRequiredUsd": round(settlement, 0),
        "fees": visa["fees"],
        "processingTimeFa": visa["processingTimeFa"],
        "processingTimeEn": visa["processingTimeEn"],
    }


def roadmap(scored_visa: dict, limit: int = 6) -> List[dict]:
    items = []
    for crit in scored_visa["criteria"]:
        gap = round(crit["max"] - crit["score"], 1)
        if gap < 1:
            continue
        items.append({
            "id": crit["id"],
            "labelFa": crit["labelFa"],
            "labelEn": crit["labelEn"],
            "gain": gap,
            "actionFa": crit["actionFa"],
            "actionEn": crit["actionEn"],
            "effort": EFFORT.get(crit["category"], "medium"),
            "priority": 2,
        })
    for blocker in scored_visa["blockers"]:
        items.append({
            "id": blocker["kind"],
            "labelFa": "شرط ورودی مسیر",
            "labelEn": "Route eligibility condition",
            "gain": 0,
            "actionFa": blocker["messageFa"],
            "actionEn": blocker["messageEn"],
            "effort": "hard",
            "priority": 1,
        })
    items.sort(key=lambda item: (item["priority"], -item["gain"]))
    return items[:limit]


GOAL_TYPES = {
    "work": {"skilled", "work", "talent", "jobseeker"},
    "study": {"study"},
    "startup": {"startup", "business"},
    "investment": {"investment"},
    "selfsponsored": {"talent", "digitalnomad", "jobseeker"},
}


def assess(dataset: dict, profile: Profile) -> dict:
    countries_out = []
    for country in dataset["countries"]:
        results = [score_visa(dataset, country, visa, profile) for visa in country["visas"]]
        results.sort(key=lambda r: (r["eligible"], r["chance"], r["readiness"]), reverse=True)
        best = results[0]
        countries_out.append({
            "code": country["code"],
            "nameFa": country["nameFa"],
            "nameEn": country["nameEn"],
            "flag": country["flag"],
            "summaryFa": country["summaryFa"],
            "summaryEn": country["summaryEn"],
            "lastVerified": country["official"]["lastVerified"],
            "portal": country["official"]["portal"],
            "authorityFa": country["official"]["authorityFa"],
            "authorityEn": country["official"]["authorityEn"],
            "best": best,
            "goalMatch": best["visaType"] in GOAL_TYPES.get(profile.goal, set()),
            "visas": results,
            "radar": best["radar"],
            "roadmap": roadmap(best),
        })
    countries_out.sort(key=lambda c: (c["best"]["eligible"], c["goalMatch"], c["best"]["chance"]), reverse=True)
    eligible_count = sum(1 for c in countries_out if c["best"]["eligible"])
    return {
        "generatedAt": profile.model_dump().get("generatedAt"),
        "datasetVersion": dataset["meta"]["version"],
        "lastVerified": dataset["meta"]["lastVerified"],
        "summary": {
            "countries": len(countries_out),
            "eligibleCountries": eligible_count,
            "bestCountry": countries_out[0]["code"] if countries_out else None,
        },
        "countries": countries_out,
        "topRoadmap": countries_out[0]["roadmap"] if countries_out else [],
        "recommendations": recommend(dataset, countries_out),
    }


def recommend(dataset: dict, countries: List[dict]) -> List[dict]:
    """Deterministic, explainable country recommendations."""
    out = []
    for country in countries[:3]:
        best = country["best"]
        out.append({
            "code": country["code"],
            "nameFa": country["nameFa"],
            "nameEn": country["nameEn"],
            "flag": country["flag"],
            "visaId": best["visaId"],
            "visaNameFa": best["visaNameFa"],
            "visaNameEn": best["visaNameEn"],
            "chance": best["chance"],
            "reasonFa": _reason_fa(best),
            "reasonEn": _reason_en(best),
        })
    return out


def _reason_fa(best: dict) -> str:
    if best["blockers"]:
        return f"نزدیک‌ترین مسیر با {best['readiness']}٪ آمادگی؛ پیش از اقدام باید شرط ورودی برطرف شود."
    return f"با {best['readiness']}٪ آمادگی پرونده و شانس تخمینی {best['chance']}٪، این مسیر آماده اقدام است."


def _reason_en(best: dict) -> str:
    if best["blockers"]:
        return f"The closest route at {best['readiness']}% readiness; eligibility must be resolved before filing."
    return f"At {best['readiness']}% profile readiness and an estimated {best['chance']}% chance, this route is ready to pursue."
