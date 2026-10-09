from app.catalog import Catalog
from app.scoring import (
    Profile,
    chance_level,
    chance_suggestions,
    combined_score,
    exam_percent,
    field_suggestions,
    interest_variants,
    parse_interests,
    quota_key,
    university_suggestions,
)

catalog = Catalog()
RIAZI = catalog.group_by_slug["riazi"]


def test_combined_score_matches_hand_calculation():
    p = Profile(gpa=18, pct={"math": 80, "physics": 60, "chemistry": 70})
    res = combined_score(RIAZI, p)
    # سوابق: 18/20 = 90٪ (سهم 60٪) ؛ آزمون: (80*12+60*9+70*7)/28 = 71.07٪ (سهم 40٪)
    assert res["score"] == 82.43
    assert res["exam_percent"] == 71.07
    assert res["school_percent"] == 90.0


def test_missing_subjects_produce_warning_and_partial_average():
    pct, used = exam_percent(RIAZI, {"math": 50}, {})
    assert pct == 50 and used == ["math"]
    res = combined_score(RIAZI, Profile(pct={"math": 50}))
    assert res["score"] == 50.0
    assert any("معدل وارد نشده" in w for w in res["warnings"])


def test_no_input_gives_no_score():
    res = combined_score(RIAZI, Profile())
    assert res["score"] is None and res["warnings"]


def test_custom_coefficient_overrides_default():
    pct, _ = exam_percent(RIAZI, {"math": 100, "physics": 0}, {"physics": 0})
    assert pct == 100  # ضریب صفر یعنی درس نادیده گرفته شود


def test_chance_levels():
    assert chance_level(80, 100) == "high"
    assert chance_level(95, 100) == "mid"
    assert chance_level(110, 100) == "close"
    assert chance_level(150, 100) == "low"


def test_quota_keys_accept_labels():
    assert quota_key("شاهد و ایثارگران") == "martyr"
    assert quota_key("local") == "local"
    assert quota_key("ناشناخته") == "other"
    assert quota_key(None) == "none"


def test_interest_synonyms_expand():
    variants = interest_variants("برنامه‌نویسی")
    assert "کامپیوتر" in variants and "برنامه نویسی" in variants
    assert parse_interests("پزشکی، طراحی ; زبان\nحقوق") == ["پزشکی", "طراحی", "زبان", "حقوق"]


def test_field_suggestions_rank_interest_first_and_filter_degree():
    p = Profile(interests=["کامپیوتر"], degree="کارشناسی")
    out = field_suggestions("ریاضی", catalog.fields, p)
    assert out, "باید حداقل یک رشته‌ی کامپیوتری پیدا شود"
    assert out[0]["score"] > 0
    assert all(any(d.startswith("کارشناسی") for d in x["field"]["degrees"]) for x in out)


def test_university_suggestions_prefers_province_and_specialized():
    p = Profile(province="تهران")
    out = university_suggestions("تجربی", catalog.universities, p)
    assert out[0]["university"]["focus"] or out[0]["university"]["province"] == "تهران"
    assert all(not x["university"]["focus"] or "تجربی" in x["university"]["focus"] for x in out)


def test_chance_suggestions_use_latest_year_and_matching_quota():
    cutoffs = [
        {"group": "ریاضی", "university": "دانشگاه الف", "field": "برق", "quota": "none", "last_rank": 1000, "year": 1403},
        {"group": "ریاضی", "university": "دانشگاه الف", "field": "برق", "quota": "none", "last_rank": 5000, "year": 1404},
        {"group": "ریاضی", "university": "دانشگاه ب", "field": "برق", "quota": "martyr", "last_rank": 9000, "year": 1404},
    ]
    p = Profile(rank_no_quota=4000, rank_quota=None)
    out = chance_suggestions("ریاضی", cutoffs, p)
    assert len(out) == 1 and out[0]["last_rank"] == 5000 and out[0]["level"] == "high"
    p2 = Profile(rank_no_quota=4000, rank_quota=8000, quota="martyr")
    out2 = chance_suggestions("ریاضی", cutoffs, p2)
    assert {x["university"] for x in out2} == {"دانشگاه الف", "دانشگاه ب"}


def test_name_match_outranks_category_match():
    out = field_suggestions("تجربی", catalog.fields, Profile(interests=["پزشکی"]))
    assert out and "پزشکی" in out[0]["field"]["name"]
