"""Build shared/dataset.json from the country packs, with strict validation."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import countries_a
import countries_b
from dataset_lib import EDUCATION_LEVELS, FX, LANGUAGE_TESTS, LAST_VERIFIED
from occupations import OCCUPATIONS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATIN = re.compile(r"[A-Za-z]")
KNOWN_RULE_KINDS = {
    "age_band", "education_rank", "language_skills", "language_best", "experience_band",
    "flag", "salary_band", "funds_ratio", "adaptability", "spouse", "numeric_band",
}
KNOWN_GATE_KINDS = {
    "age_gate", "language_gate", "experience_gate", "points_gate", "funds_gate",
    "education_gate", "flag_gate", "salary_gate", "investment_gate", "remote_income_gate",
    "custom_points",
}
FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_fa_digits(value):
    if isinstance(value, str):
        return value.translate(FA_DIGITS)
    if isinstance(value, list):
        return [to_fa_digits(v) for v in value]
    if isinstance(value, dict):
        return {k: to_fa_digits(v) for k, v in value.items()}
    return value


def walk(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}[{index}]")
    else:
        yield path, node


def localise(node):
    """Convert ASCII digits to Persian digits in every Fa-facing field."""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key.endswith("Fa") or key in {"fa", "titleFa"}:
                out[key] = to_fa_digits(value)
            elif key == "official" and isinstance(value, dict):
                out[key] = localise(value)
            else:
                out[key] = localise(value) if isinstance(value, (dict, list)) else value
        return out
    if isinstance(node, list):
        return [localise(v) for v in node]
    return node


def validate(dataset):
    errors = []
    visa_ids = set()
    for country in dataset["countries"]:
        code = country["code"]
        if code not in FX and country["currency"] not in FX:
            errors.append(f"{code}: currency {country['currency']} missing from FX table")
        for visa in country["visas"]:
            vid = visa["id"]
            if vid in visa_ids:
                errors.append(f"duplicate visa id {vid}")
            visa_ids.add(vid)
            if visa["maxPoints"] < visa["passMark"]:
                errors.append(f"{vid}: passMark {visa['passMark']} exceeds maxPoints {visa['maxPoints']}")
            if not visa["criteria"]:
                errors.append(f"{vid}: no criteria")
            for crit in visa["criteria"]:
                kind = crit["rule"]["kind"]
                if kind not in KNOWN_RULE_KINDS:
                    errors.append(f"{vid}.{crit['id']}: unknown rule kind {kind}")
            for g in visa["gates"]:
                if g["kind"] not in KNOWN_GATE_KINDS:
                    errors.append(f"{vid}: unknown gate kind {g['kind']}")
            for item in visa["fees"]:
                if item["currency"] not in FX:
                    errors.append(f"{vid}: fee currency {item['currency']} missing from FX")
        # language checks
        for path, value in walk(country):
            if path.endswith("Fa") and isinstance(value, str):
                match = LATIN.search(value)
                if match:
                    errors.append(f"{code}.{path}: Latin characters in Persian text -> {value[:80]!r}")
    for occ in dataset["occupations"]:
        for path, value in walk(occ):
            if path.endswith("Fa") and isinstance(value, str) and LATIN.search(value):
                errors.append(f"occupation {occ['noc']}.{path}: Latin characters -> {value!r}")
    return errors


def main():
    countries = countries_a.COUNTRIES + countries_b.COUNTRIES
    countries.sort(key=lambda c: (c["priority"], c["nameEn"]))
    dataset = {
        "meta": {
            "nameFa": "ذهن‌یار",
            "nameEn": "Zehnyar",
            "version": "2.0.0",
            "lastVerified": LAST_VERIFIED,
            "currencyNoteFa": "نرخ‌های ارز مرجع و تقریبی هستند و تنها برای مقایسه یکسان به کار می‌روند.",
            "currencyNoteEn": "Reference exchange rates are indicative and used only for normalisation.",
        },
        "fx": FX,
        "educationLevels": EDUCATION_LEVELS,
        "languageTests": LANGUAGE_TESTS,
        "countries": countries,
        "occupations": OCCUPATIONS,
    }
    dataset = localise(dataset)
    errors = validate({**dataset})
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(" -", err)
        return 1
    out_dir = os.path.join(ROOT, "shared")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dataset.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(dataset, handle, ensure_ascii=False, indent=1)
    total_visas = sum(len(c["visas"]) for c in countries)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"OK  countries={len(countries)}  visas={total_visas}  occupations={len(OCCUPATIONS)}  size={size_kb:.0f}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
