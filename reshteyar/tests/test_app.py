import base64
from urllib.parse import unquote_plus

from fastapi.testclient import TestClient

from app import main
from app.catalog import parse_cutoffs
from app.config import settings
from app.licensing import COOKIE_NAME

client = TestClient(main.app)

PROFILE = {"gpa": 18, "pct": {"math": 80, "physics": 60, "chemistry": 70}, "rank_no_quota": 20000,
           "interests": "کامپیوتر", "univ_types": []}


def _admin_headers():
    token = base64.b64encode(f"{settings.admin_user}:{settings.admin_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_pages_render_with_persian_rtl_and_theme():
    for path in ["/", "/groups/riazi", "/groups/tajrobi", "/groups/ensani", "/groups/honar", "/groups/zaban",
                 "/groups/maaref", "/fields", "/universities", "/factors", "/about", "/premium", "/account"]:
        r = client.get(path)
        assert r.status_code == 200, path
        assert 'dir="rtl"' in r.text and 'lang="fa"' in r.text
        assert "style.css" in r.text


def test_group_page_shows_required_konkur_factors():
    html = client.get("/groups/riazi").text
    for needle in ["معدل کل سوابق", "درصد", "ضریب", "رتبه‌ی کل (بدون سهمیه)", "رتبه‌ی با سهمیه", "سهمیه‌ی شما"]:
        assert needle in html, needle


def test_unknown_group_is_404_and_api_400_on_bad_input():
    assert client.get("/groups/nope").status_code == 404
    r = client.post("/api/groups/riazi/analyze", json={"pct": {"math": 150}})
    assert r.status_code == 422


def test_analyze_free_tier_limits_and_locks():
    r = client.post("/api/groups/riazi/analyze", json=PROFILE)
    assert r.status_code == 200
    body = r.json()
    assert body["premium"] is False
    assert body["score"]["score"] == 82.43
    assert len(body["fields"]["items"]) == 5 and body["fields"]["locked"] is True
    assert len(body["universities"]["items"]) == 5 and body["universities"]["locked"] is True
    assert body["chances"]["available"] is False and "داده" in body["chances"]["message"]
    assert body["fields"]["interest_matched"] is True
    assert body["fields"]["items"][0]["score"] > 0


def test_lists_api_filters():
    fields = client.get("/api/fields", params={"group": "tajrobi", "degree": "کارشناسی", "limit": 100}).json()
    assert fields["total"] > 0
    assert all("تجربی" in [g["key"] for g in f["groups"]] for f in fields["items"])
    spec = client.get("/api/universities", params={"group": "tajrobi", "mode": "specialized", "limit": 100}).json()
    assert spec["total"] > 0
    assert all(any(g["key"] == "تجربی" for g in u["focus"]) for u in spec["items"])
    all_unis = client.get("/api/universities", params={"limit": 1}).json()
    assert all_unis["total"] >= spec["total"]


def test_mock_purchase_flow_activates_license_and_account():
    r = client.post("/premium/checkout", data={"plan": "month", "mobile": "۰۹۱۲۳۴۵۶۷۸۹", "email": ""},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/premium/mock/MOCK")
    mock_path = r.headers["location"]
    page = client.get(mock_path)
    assert page.status_code == 200 and "شبیه‌سازی پرداخت" in page.text
    r2 = client.post(mock_path, data={"outcome": "OK"}, follow_redirects=False)
    assert r2.status_code == 303 and "Status=OK" in r2.headers["location"]
    r3 = client.get(r2.headers["location"], follow_redirects=False)
    assert r3.status_code == 303 and r3.headers["location"].startswith("/premium/result?t=")
    result = client.get(r3.headers["location"])
    assert result.status_code == 200 and "پرداخت انجام شد" in result.text
    assert "RZ-" in result.text
    cookie = client.cookies.get(COOKIE_NAME)
    assert cookie and cookie.startswith("RZ-")
    acc = client.get("/account")
    assert "اشتراک فعال" in acc.text
    # بعد از فعال شدن، نتیجه‌ی تحلیل کامل است
    full = client.post("/api/groups/riazi/analyze", json=PROFILE).json()
    assert full["premium"] is True and full["fields"]["locked"] is False and len(full["fields"]["items"]) > 5
    # خروج از حساب
    client.post("/account/logout", follow_redirects=False)
    assert client.get("/api/groups/riazi/analyze", params={}).status_code in (404, 405)
    client.cookies.clear()


def test_activation_with_code_and_invalid_code():
    r = client.post("/account/activate", data={"code": "RZ-0000-0000-0000-0000"})
    assert r.status_code == 400 and "معتبر نیست" in r.text


def test_admin_requires_auth_and_cutoff_upload_reloads(tmp_path):
    assert client.get("/admin").status_code == 401
    assert client.get("/admin", headers=_admin_headers()).status_code == 200
    csv_text = ("year,group,university,field,quota,last_rank\n"
                "1404,ریاضی,دانشگاه تهران,مهندسی برق,none,1500\n"
                "1404,riazi,دانشگاه تهران,مهندسی برق,martyr,9000\n"
                "1404,ریاضی,دانشگاه نامعتبر,مهندسی,none,abc\n")
    files = {"file": ("cutoffs.csv", csv_text.encode("utf-8"), "text/csv")}
    r = client.post("/admin/cutoffs", files=files, headers=_admin_headers(), follow_redirects=False)
    assert r.status_code == 303 and "ردیف ثبت شد" in unquote_plus(r.headers["location"])
    assert len(main.catalog.cutoffs) == 2
    assert len(main.catalog.cutoff_errors) == 1
    assert main.catalog.cutoffs[0]["group"] == "ریاضی"


def test_parse_cutoffs_errors_are_reported():
    rows, errors = parse_cutoffs("year,group,university\n1404,ریاضی,x\n", main.catalog)
    assert rows == [] and "ستون‌های لازم" in errors[0]
    rows, errors = parse_cutoffs("group,university,field,last_rank\nنامعتبر,x,y,10\n", main.catalog)
    assert rows == [] and "گروه نامعتبر" in errors[0]
