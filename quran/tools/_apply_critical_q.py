# -*- coding: utf-8 -*-
"""خوانش انتقادیِ هر آیه را با یک پرسشِ چالشیِ آیه‌محور جایگزین می‌کند.

python3 quran/tools/_apply_critical_q.py 20 [21 22 ...]

پرسش‌ها در quran/tools/critical_q/s<N>*.py (دیکشنریِ Q، کلید «سوره:آیه») نوشته شده‌اند.
cite = «قرآن … ؛ منابعِ مرتبط با این پرسش: » + ارجاع‌های تفسیریِ همان آیه
(از فیلدهای notes/context/classical/modern خودِ رکورد؛ بدونِ ارجاع به آیهٔ دیگر یا مقالهٔ روش)."""
import glob, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHARDS = [("verse-dossier-extended-fields.json", {}), ("verse-dossier-extended-fields-2.json", {"separators": (",", ":")})]
LABEL = "منابعِ مرتبط با این پرسش: "

def load_q(surah):
    q = {}
    for f in sorted(glob.glob(str(ROOT / "tools" / "critical_q" / f"s{surah}*.py"))):
        spec = importlib.util.spec_from_file_location("m", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        q.update(m.Q)
    return q

def tafsir_cites(r):
    out = []
    for f in ("classical", "notes", "context", "modern"):
        for e in r.get(f, []):
            c = e["cite"]
            if c.startswith("قرآن،") or "مقالهٔ پژوهشی" in c or c in out: continue
            out.append(c)
    return out

def main(surahs):
    for name, kw in SHARDS:
        path = ROOT / "static" / name
        d = json.loads(path.read_text(encoding="utf-8")); V = d["verses"]; n = 0
        for s in surahs:
            for v, text in load_q(s).items():
                if v not in V: continue
                r = V[v]
                quran = next((e["cite"].split("؛ " + LABEL)[0] for e in r["critical"] if e["cite"].startswith("قرآن،")), f"قرآن، {v}")
                assert "؟" in text and len(text.split()) >= 14, v
                r["critical"] = [{"text": text, "cite": quran + "؛ " + LABEL + "؛ ".join(tafsir_cites(r))}]
                n += 1
        path.write_text(json.dumps(d, ensure_ascii=False, **kw), encoding="utf-8")
        print(name, n)

if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]])
