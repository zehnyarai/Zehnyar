"""Zehnyar API.

Public read-only reference data plus the deterministic assessment engine.
The mobile client mirrors this engine so it works fully offline; these
endpoints exist for web clients, partners and auditability.
"""

from __future__ import annotations

import os
import time
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine.engine import (
    Profile,
    assess,
    load_dataset,
    roadmap,
    score_visa,
    settlement_usd,
    to_usd,
)

API_VERSION = "2.0.0"
DISCLAIMER_FA = (
    "این ارزیابی بر پایه قواعد اعلام‌شده مراجع رسمی در تاریخ آخرین استعلام محاسبه شده است و "
    "تخمینی است، نه تصمیم حقوقی یا تضمین پذیرش. پیش از هر اقدام، شرایط را در درگاه رسمی کشور مقصد بررسی کنید."
)
DISCLAIMER_EN = (
    "This assessment is computed from rules published by official authorities on the last verification date. "
    "It is an estimate, not a legal decision or a guarantee of approval. Verify every requirement on the "
    "destination country's official portal before applying."
)

app = FastAPI(title="Zehnyar API", version=API_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict = {}


class AssessRequest(BaseModel):
    profile: Profile


class CompareRequest(BaseModel):
    profile: Profile
    countries: List[str] = Field(default_factory=list)


class AdvisorRequest(BaseModel):
    profile: Profile
    country: Optional[str] = None


@app.get("/")
def root():
    dataset = load_dataset()
    return {
        "name": "Zehnyar API",
        "version": API_VERSION,
        "datasetVersion": dataset["meta"]["version"],
        "lastVerified": dataset["meta"]["lastVerified"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    dataset = load_dataset()
    return {
        "status": "ok",
        "datasetVersion": dataset["meta"]["version"],
        "lastVerified": dataset["meta"]["lastVerified"],
        "countries": len(dataset["countries"]),
        "visas": sum(len(c["visas"]) for c in dataset["countries"]),
        "occupations": len(dataset["occupations"]),
    }


@app.get("/api/meta")
def meta():
    dataset = load_dataset()
    return {
        "version": dataset["meta"]["version"],
        "lastVerified": dataset["meta"]["lastVerified"],
        "disclaimerFa": DISCLAIMER_FA,
        "disclaimerEn": DISCLAIMER_EN,
        "counts": {
            "countries": len(dataset["countries"]),
            "visas": sum(len(c["visas"]) for c in dataset["countries"]),
            "occupations": len(dataset["occupations"]),
            "languages": len(dataset["languageTests"]),
        },
        "educationLevels": dataset["educationLevels"],
        "languageTests": [
            {"id": t["id"], "fa": t["fa"], "en": t["en"], "group": t["group"], "kind": t["kind"],
             "scale": t.get("scale"), "cefr": t.get("cefr"), "overallOnly": t.get("overallOnly", False)}
            for t in dataset["languageTests"]
        ],
        "fx": dataset["fx"],
    }


@app.get("/api/dataset")
def dataset_full():
    """Full dataset for offline mobile sync."""
    return load_dataset()


@app.get("/api/countries")
def countries():
    dataset = load_dataset()
    return {
        "items": [
            {
                "code": c["code"],
                "nameFa": c["nameFa"],
                "nameEn": c["nameEn"],
                "flag": c["flag"],
                "region": c["region"],
                "summaryFa": c["summaryFa"],
                "summaryEn": c["summaryEn"],
                "visaCount": len(c["visas"]),
                "visaTypes": sorted({v["type"] for v in c["visas"]}),
                "authorityFa": c["official"]["authorityFa"],
                "authorityEn": c["official"]["authorityEn"],
                "portal": c["official"]["portal"],
                "lastVerified": c["official"]["lastVerified"],
                "priority": c["priority"],
            }
            for c in dataset["countries"]
        ]
    }


@app.get("/api/countries/{code}")
def country_detail(code: str):
    dataset = load_dataset()
    for country in dataset["countries"]:
        if country["code"].lower() == code.lower():
            return country
    raise HTTPException(status_code=404, detail={"messageFa": "این کشور در بانک اطلاعاتی نیست.", "messageEn": "Country not found."})


@app.get("/api/visas/{visa_id}")
def visa_detail(visa_id: str):
    dataset = load_dataset()
    for country in dataset["countries"]:
        for visa in country["visas"]:
            if visa["id"] == visa_id:
                return {"country": {k: country[k] for k in ("code", "nameFa", "nameEn", "flag", "official")}, "visa": visa}
    raise HTTPException(status_code=404, detail={"messageFa": "این مسیر یافت نشد.", "messageEn": "Visa route not found."})


@app.get("/api/visas/{visa_id}/costs")
def visa_costs(visa_id: str, family_size: int = Query(1, ge=1, le=10), currency: str = "USD"):
    dataset = load_dataset()
    for country in dataset["countries"]:
        for visa in country["visas"]:
            if visa["id"] == visa_id:
                rate = dataset["fx"].get(currency, {"rate": 1.0})["rate"]
                applicant_total = 0.0
                employer_total = 0.0
                lines = []
                for item in visa["fees"]:
                    multiplier = 1
                    if "spouse" in item["labelEn"].lower() or "adult" in item["labelEn"].lower():
                        multiplier = max(1, family_size)
                    elif "child" in item["labelEn"].lower():
                        multiplier = 0
                    usd = to_usd(dataset, item["amount"], item["currency"]) * multiplier
                    if item.get("payer") == "employer":
                        employer_total += usd
                    else:
                        applicant_total += usd
                    lines.append({**item, "count": multiplier, "usd": round(usd, 0)})
                settlement = settlement_usd(dataset, visa, family_size)
                return {
                    "lines": lines,
                    "applicantTotalUsd": round(applicant_total, 0),
                    "employerTotalUsd": round(employer_total, 0),
                    "settlementUsd": round(settlement, 0),
                    "grandTotalUsd": round(applicant_total + settlement, 0),
                    "display": {
                        "currency": currency,
                        "applicantTotal": round((applicant_total + settlement) / rate, 0),
                    },
                }
    raise HTTPException(status_code=404, detail={"messageFa": "این مسیر یافت نشد.", "messageEn": "Visa route not found."})


@app.get("/api/occupations")
def occupations(q: Optional[str] = None, demand: Optional[str] = None):
    dataset = load_dataset()
    items = dataset["occupations"]
    if q:
        needle = q.lower()
        items = [o for o in items if needle in o["titleFa"] or needle in o["titleEn"].lower() or needle in o["noc"]]
    if demand:
        items = [o for o in items if demand.upper() in o["inDemand"]]
    return {"items": items, "count": len(items)}


@app.post("/api/assess")
def assess_endpoint(request: AssessRequest):
    dataset = load_dataset()
    result = assess(dataset, request.profile)
    return {**result, "disclaimerFa": DISCLAIMER_FA, "disclaimerEn": DISCLAIMER_EN}


@app.post("/api/compare")
def compare_endpoint(request: CompareRequest):
    dataset = load_dataset()
    codes = {c.upper() for c in request.countries}
    results = []
    for country in dataset["countries"]:
        if codes and country["code"] not in codes:
            continue
        scored = [score_visa(dataset, country, visa, request.profile) for visa in country["visas"]]
        for item in scored:
            item["roadmap"] = roadmap(item, limit=3)
        scored.sort(key=lambda r: (r["eligible"], r["chance"]), reverse=True)
        results.append({
            "code": country["code"],
            "nameFa": country["nameFa"],
            "nameEn": country["nameEn"],
            "flag": country["flag"],
            "best": scored[0],
            "visas": scored,
        })
    results.sort(key=lambda c: (c["best"]["eligible"], c["best"]["chance"]), reverse=True)
    return {"items": results}


@app.post("/api/advisor")
def advisor_endpoint(request: AdvisorRequest):
    """Deterministic guidance, optionally enriched by a language model.

    The deterministic text is always returned so the client never depends on
    an external provider being available.
    """
    dataset = load_dataset()
    result = assess(dataset, request.profile)
    top = result["recommendations"][0] if result["recommendations"] else None
    steps = []
    if top:
        country = next(c for c in result["countries"] if c["code"] == top["code"])
        for item in country["roadmap"][:4]:
            steps.append({
                "titleFa": item["labelFa"],
                "titleEn": item["labelEn"],
                "detailFa": item["actionFa"],
                "detailEn": item["actionEn"],
                "gain": item["gain"],
                "effort": item["effort"],
            })
    narrative_fa = None
    narrative_en = None
    key = os.environ.get("GROQ_API_KEY")
    if key and top:
        cached = _cache.get("advisor")
        if cached and time.time() - cached[0] < 3600:
            narrative_fa, narrative_en = cached[1], cached[2]
        else:
            try:
                prompt = (
                    "You are a licensed immigration analyst. Write a 90-word assessment in Persian and the same in English. "
                    f"Profile: age {request.profile.age}, education {request.profile.educationId}, "
                    f"work years {request.profile.work.totalYears}, goal {request.profile.goal}. "
                    f"Best route: {top['visaNameEn']} in {top['nameEn']} with estimated chance {top['chance']}%. "
                    "Be factual, never promise an outcome, and mention that figures must be verified on the official portal."
                )
                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": "llama-3.3-70b-versatile",
                          "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
                    timeout=20.0,
                )
                if response.status_code < 400:
                    text = response.json()["choices"][0]["message"]["content"]
                    narrative_en = text.strip()
                    narrative_fa = None
                    _cache["advisor"] = (time.time(), narrative_fa, narrative_en)
            except Exception:
                narrative_en = None
    return {
        "summary": result["summary"],
        "recommendations": result["recommendations"],
        "steps": steps,
        "narrativeFa": narrative_fa,
        "narrativeEn": narrative_en,
        "disclaimerFa": DISCLAIMER_FA,
        "disclaimerEn": DISCLAIMER_EN,
    }


@app.get("/api/checklist/{visa_id}")
def checklist(visa_id: str):
    dataset = load_dataset()
    for country in dataset["countries"]:
        for visa in country["visas"]:
            if visa["id"] != visa_id:
                continue
            base = [
                {"fa": "گذرنامه معتبر با اعتبار دست‌کم شش ماه", "en": "Valid passport with at least six months validity"},
                {"fa": "عکس بیومتریک مطابق استاندارد سفارت", "en": "Biometric photograph to embassy standard"},
                {"fa": "فرم درخواست تکمیل‌شده", "en": "Completed application form"},
                {"fa": "گواهی عدم سوءپیشینه کیفری", "en": "Police clearance certificate"},
                {"fa": "گواهی سلامت و انجام آزمایش‌های پزشکی", "en": "Medical examination and health certificate"},
            ]
            for requirement in visa["requirementsFa"]:
                base.append({"fa": requirement, "en": ""})
            for index, requirement in enumerate(visa["requirementsEn"]):
                if index < len(base):
                    base[5 + index]["en"] = requirement
            return {
                "visaId": visa_id,
                "nameFa": visa["nameFa"],
                "nameEn": visa["nameEn"],
                "items": [{"id": f"doc_{i+1}", **item} for i, item in enumerate(base)],
            }
    raise HTTPException(status_code=404, detail={"messageFa": "این مسیر یافت نشد.", "messageEn": "Visa route not found."})
