"""بارگذاری داده‌های JSON و جستجو/صفحه‌بندی فهرست‌ها و داده‌ی اختیاری رتبه‌های قبولی."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .config import DATA_DIR, settings
from .scoring import UNI_TYPES_ORDER, quota_key
from .textutil import norm

DEGREE_CHOICES = ["کاردانی", "کارشناسی", "دکتری"]
CUTOFF_REQUIRED = ("group", "university", "field", "last_rank")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Catalog:
    def __init__(self, data_dir: Path = DATA_DIR, cutoffs_path: Path | None = None) -> None:
        self.data_dir = data_dir
        self.groups: list[dict] = _load(data_dir / "groups.json")
        self.group_by_slug = {g["slug"]: g for g in self.groups}
        self.group_by_key = {g["data_key"]: g for g in self.groups}
        self.fields: list[dict] = _load(data_dir / "fields.json")
        self.universities: list[dict] = _load(data_dir / "universities.json")
        self.factors: list[dict] = _load(data_dir / "factors.json")
        self.plans: list[dict] = _load(data_dir / "plans.json")
        self.meta: dict = _load(data_dir / "meta.json")

        self._field_index = [(f, norm(f["name"]), norm(f["category"])) for f in self.fields]
        self._uni_index = [(u, norm(u["name"]), norm(u["city"])) for u in self.universities]

        provinces = {u["province"] for u in self.universities if u["province"] != "نامشخص"}
        self.provinces = sorted(provinces)
        present_types = {u["type"] for u in self.universities}
        self.uni_types = [t for t in UNI_TYPES_ORDER if t in present_types]
        self.uni_types += sorted(present_types - set(self.uni_types))

        self.cutoffs_path = cutoffs_path or settings.cutoffs_path
        self.cutoffs: list[dict] = []
        self.cutoff_errors: list[str] = []
        self.reload_cutoffs()

    # ------------------------------------------------------------ helpers
    def group_key_from_any(self, value: str | None) -> str | None:
        """ورودی می‌تواند slug، نام داده (مثل ریاضی)، عنوان یا نام کنکوری گروه باشد."""
        if not value:
            return None
        v = norm(value)
        for g in self.groups:
            if v in {norm(g["slug"]), norm(g["data_key"]), norm(g["title"]), norm(g["konkur_name"])}:
                return g["data_key"]
        return None

    def group_refs(self, keys: list[str]) -> list[dict]:
        return [
            {"slug": self.group_by_key[k]["slug"], "title": self.group_by_key[k]["title"], "key": k}
            for k in keys if k in self.group_by_key
        ]

    def field_view(self, f: dict) -> dict:
        return {
            "id": f["id"],
            "name": f["name"],
            "category": f["category"],
            "degrees": f["degrees"],
            "groups": self.group_refs(f["groups"]),
            "source": f["source"],
        }

    def uni_view(self, u: dict) -> dict:
        return {
            "id": u["id"],
            "name": u["name"],
            "type": u["type"],
            "province": u["province"],
            "city": u["city"],
            "focus": self.group_refs(u["focus"]),
            "specialized": bool(u["focus"]),
        }

    # ------------------------------------------------------------ search
    def search_fields(self, q: str = "", group_key: str | None = None, degree: str | None = None,
                      offset: int = 0, limit: int = 40) -> dict:
        qn = norm(q)
        items = []
        for f, name_n, cat_n in self._field_index:
            if group_key and group_key not in f["groups"]:
                continue
            if degree and not any(d.startswith(degree) for d in f["degrees"]):
                continue
            if qn and qn not in name_n and qn not in cat_n:
                continue
            items.append(f)
        page = items[offset:offset + limit]
        return {"total": len(items), "offset": offset, "limit": limit,
                "items": [self.field_view(f) for f in page]}

    def search_universities(self, q: str = "", utype: str | None = None, province: str | None = None,
                            group_key: str | None = None, mode: str = "all",
                            offset: int = 0, limit: int = 40) -> dict:
        """
        mode (فقط وقتی گروه داده شود):
          related     : دانشگاه‌های تخصصی همان گروه + دانشگاه‌های عمومی (بدون تخصص مشخص)
          specialized : فقط دانشگاه‌های تخصصی همان گروه
          all         : همه؛ دانشگاه‌های تخصصی همان گروه بالاتر می‌آیند
        """
        qn = norm(q)
        matched: list[tuple[int, dict]] = []
        for u, name_n, city_n in self._uni_index:
            if utype and u["type"] != utype:
                continue
            if province and u["province"] != province:
                continue
            rank = 0
            if group_key:
                in_focus = group_key in u["focus"]
                generic = not u["focus"]
                if mode == "specialized" and not in_focus:
                    continue
                if mode == "related" and not (in_focus or generic):
                    continue
                rank = 0 if in_focus else (1 if generic else 2)
            if qn and qn not in name_n and qn not in city_n:
                continue
            matched.append((rank, u))
        matched.sort(key=lambda x: (x[0], x[1]["name"]))
        items = [u for _, u in matched]
        page = items[offset:offset + limit]
        return {"total": len(items), "offset": offset, "limit": limit,
                "items": [self.uni_view(u) for u in page]}

    def group_stats(self, group_key: str) -> dict:
        fields = sum(1 for f in self.fields if group_key in f["groups"])
        specialized = sum(1 for u in self.universities if group_key in u["focus"])
        generic = sum(1 for u in self.universities if not u["focus"])
        return {"fields": fields, "universities_specialized": specialized, "universities_generic": generic}

    # ------------------------------------------------------------ cutoffs (optional)
    def reload_cutoffs(self) -> None:
        text = self.cutoffs_path.read_text(encoding="utf-8-sig") if self.cutoffs_path.exists() else ""
        self.cutoffs, self.cutoff_errors = parse_cutoffs(text, self)


def parse_cutoffs(text: str, catalog: Catalog) -> tuple[list[dict], list[str]]:
    """
    ستون‌ها: year,group,university,field,quota,last_rank[,capacity]
    group: slug یا نام داده‌ی گروه (ریاضی/تجربی/انسانی/هنر/زبان/معارف)
    quota: کلید سهمیه (none/martyr/basij/local/disabled/needy/other) یا عنوان فارسی آن؛ پیش‌فرض none
    """
    rows: list[dict] = []
    errors: list[str] = []
    if not text.strip():
        return rows, errors
    reader = csv.DictReader(io.StringIO(text))
    headers = {(h or "").strip().lower(): h for h in (reader.fieldnames or [])}
    missing = [c for c in CUTOFF_REQUIRED if c not in headers]
    if missing:
        return rows, [f"ستون‌های لازم در فایل نیست: {', '.join(missing)}"]

    def cell(row: dict, name: str) -> str:
        return (row.get(headers[name]) or "").strip() if name in headers else ""

    for line_no, row in enumerate(reader, start=2):
        group_key = catalog.group_key_from_any(cell(row, "group"))
        if group_key is None:
            errors.append(f"سطر {line_no}: گروه نامعتبر است")
            continue
        university = cell(row, "university")
        field = cell(row, "field")
        if not university or not field:
            errors.append(f"سطر {line_no}: نام دانشگاه یا رشته خالی است")
            continue
        try:
            last_rank = int(cell(row, "last_rank").replace(",", ""))
            if last_rank <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"سطر {line_no}: آخرین رتبه‌ی قبولی باید عدد مثبت باشد")
            continue
        try:
            year = int(cell(row, "year") or 0)
        except ValueError:
            errors.append(f"سطر {line_no}: سال نامعتبر است")
            continue
        rows.append({
            "group": group_key,
            "university": university,
            "field": field,
            "quota": quota_key(cell(row, "quota")),
            "last_rank": last_rank,
            "year": year,
        })
    return rows, errors
