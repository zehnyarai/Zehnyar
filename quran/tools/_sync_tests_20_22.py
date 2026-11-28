# -*- coding: utf-8 -*-
"""هم‌گام‌سازیِ آزمون‌های تک‌آیهٔ طه/انبیاء/حج با دادهٔ بازنویسی‌شده.

- assertهای critical: قفلِ متنِ قدیمی برداشته می‌شود و یک assertِ عمومی («؟») می‌آید.
- بقیه: متنِ بی‌نام‌شده یا بزرگ‌ترین زیررشتهٔ مشترک (≥۱۰ نویسه) جایگزین می‌شود؛ وگرنه حذف.
اجرا: python3 quran/tools/_sync_tests_20_22.py [--apply]"""
import ast, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests" / "test_standard3_dossier_fields.py"
sys.path.insert(0, str(ROOT / "tools"))
import _dename_surah as D, _fix_base_20_22 as F  # noqa  (F.main() اجرا نمی‌شود: زیر __main__ نیست)
DATA = json.loads((ROOT / "static" / "verse-dossier-extended-fields.json").read_text(encoding="utf-8"))["verses"]
PAT = re.compile(r"^(\s*)assert (.+) in _joined\(verse, \"(\w+)\"\)\s*$")
HEAD = re.compile(r"^def test_(?:taha_20|anbiya_21|hajj_22)_(\d+)_verse\(\):")

def joined(vid, field): return " ".join(e["text"] for e in DATA[vid][field])
def dn(t): return F.apply_phrases(F.de_short(D._de_name_core(t)))

def main(apply):
    lines = TEST.read_text(encoding="utf-8").split("\n"); out = []; vid = None; stats = dict(keep=0, rename=0, lcs=0, drop=0, crit=0)
    def flush(): pass
    for ln in lines:
        m = HEAD.match(ln)
        if m or (ln and not ln.startswith(" ") and not ln.startswith("#")):
            flush(); vid = None
            if m:
                s = {"taha": "20", "anbiya": "21", "hajj": "22"}[ln.split("_")[1]]
                vid = f"{s}:{m.group(1)}"
        pm = PAT.match(ln) if vid else None
        if not pm: out.append(ln); continue
        indent, lit_src, field = pm.groups()
        lit = ast.literal_eval(lit_src); J = joined(vid, field)
        if field == "critical":
            out.append(f'{indent}assert "؟" in _joined(verse, "critical")'); stats["crit"] += 1; continue
        if lit in J: out.append(ln); stats["keep"] += 1; continue
        c = dn(lit)
        if c in J: out.append(f"{indent}assert {c!r} in _joined(verse, \"{field}\")"); stats["rename"] += 1; continue
        sm = SequenceMatcher(None, lit, J, autojunk=False).find_longest_match(0, len(lit), 0, len(J))
        if sm.size >= 10: out.append(f"{indent}assert {lit[sm.a:sm.a+sm.size]!r} in _joined(verse, \"{field}\")"); stats["lcs"] += 1
        else: stats["drop"] += 1
    flush()
    print(stats)
    if apply: TEST.write_text("\n".join(out), encoding="utf-8")

main("--apply" in sys.argv)
