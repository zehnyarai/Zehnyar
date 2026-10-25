"""Generate engine fixtures from the Python reference implementation."""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.app.engine.engine import (  # noqa: E402
    Adaptability, Funds, LanguageResult, Profile, Spouse, Work, assess, load_dataset,
)

PROFILES = {
    "skilled_en": Profile(
        age=31, educationId="master",
        languages=[LanguageResult(testId="ielts", skills={"listening": 8.0, "reading": 7.5, "writing": 7.0, "speaking": 7.5})],
        work=Work(totalYears=6, overseasYears=6, occupationCode="21231", jobOffer=False),
        funds=Funds(availableUsd=40000), adaptability=Adaptability(eca=True),
        familySize=2, goal="work",
    ),
    "student_young": Profile(
        age=23, educationId="bachelor", studyOffer=True, goal="study",
        languages=[LanguageResult(testId="toefl", skills={"listening": 24, "reading": 22, "writing": 25, "speaking": 23})],
        work=Work(totalYears=1, overseasYears=1, occupationCode="21232"),
        funds=Funds(availableUsd=52000), familySize=1,
    ),
    "family_de": Profile(
        age=38, maritalStatus="married", spouse=Spouse(educationId="bachelor", languageClb=7, workYears=5),
        educationId="bachelor", goal="work",
        languages=[LanguageResult(testId="goethe", cefr="B2"), LanguageResult(testId="ielts", skills={"listening": 6.5, "reading": 6.0, "writing": 6.0, "speaking": 6.5})],
        work=Work(totalYears=11, overseasYears=11, occupationCode="31301", salaryAnnualLocal=52000, salaryCurrency="EUR"),
        funds=Funds(availableUsd=18000), adaptability=Adaptability(relativeInCountry=True), familySize=4,
    ),
    "investor": Profile(
        age=45, educationId="bachelor", goal="investment", investmentUsd=900000,
        work=Work(totalYears=15, overseasYears=15, occupationCode="10010"),
        funds=Funds(availableUsd=1200000, cashUsd=900000, assetsUsd=300000), familySize=3,
        startupBacking=True,
    ),
    "bare": Profile(age=52, educationId="highschool", work=Work(totalYears=0), funds=Funds(availableUsd=2000), familySize=1),
    "digital_nomad": Profile(
        age=29, educationId="bachelor", goal="selfsponsored", remoteIncomeUsd=4200,
        languages=[LanguageResult(testId="duolingo", skills={"overall": 125})],
        work=Work(totalYears=5, overseasYears=5, occupationCode="21234"),
        funds=Funds(availableUsd=25000), familySize=1,
    ),
}


def main():
    dataset = load_dataset()
    out = {}
    for name, profile in PROFILES.items():
        result = assess(dataset, profile)
        out[name] = {
            "profile": profile.model_dump(),
            "countries": {
                country["code"]: {
                    "goalMatch": country["goalMatch"],
                    "visas": {
                        visa["visaId"]: {
                            "chance": visa["chance"],
                            "readiness": visa["readiness"],
                            "achieved": visa["achieved"],
                            "eligible": visa["eligible"],
                            "blockers": [b["kind"] for b in visa["blockers"]],
                        }
                        for visa in country["visas"]
                    },
                    "best": country["best"]["visaId"],
                }
                for country in result["countries"]
            },
            "summary": result["summary"],
        }
    target = os.path.join(ROOT, "shared", "engine-fixtures.json")
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
    print(f"fixtures written: {len(out)} profiles")


if __name__ == "__main__":
    main()
