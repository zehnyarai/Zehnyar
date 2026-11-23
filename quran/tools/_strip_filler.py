# -*- coding: utf-8 -*-
"""حذفِ دُمِ پرکنندهٔ قالبی از رکوردهای شاردِ extended.

برخی بندها پس از یک آغازِ مستند با دنباله‌ای مانند
«…و باید آن را گرفت و نگه داشت و دانست و آموخت و دید» پایان می‌یابند که
هیچ ادعای مربوط به آیه ندارد. این ابزار فقط همان دُم را می‌برد (تا آخرین
مرزِ جمله یا «و باید»ِ پیش از آن) و بندِ مستندِ آغاز را نگه می‌دارد.
اگر پس از بریدن بند کوتاه‌تر از حدّ آزمون شود، مدخل گزارش می‌شود و
دست‌کاری نمی‌شود تا بازنویسیِ تحریری شود.

    python3 _strip_filler.py --surah 12 [--surah 13 ...] [--dry]
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PATHS = [ROOT / "static" / "verse-dossier-extended-fields.json",
             ROOT / "static" / "verse-dossier-extended-fields-2.json"]
MIN_WORDS = 14
HOLLOW_MIN = 18  # حاشیهٔ امن: بی‌نام‌سازیِ بعدی چند واژه می‌کاهد

VERBS = (r"(?:دانست|دید|گرفت|آموخت|نگه داشت|خواند|جست|شناخت|حس کرد|شاد شد|"
         r"پرهیز کرد|به کار بست|ساخت|کرد|پرداخت|نوشت|فهمید|ماند|بست)")
FILL = re.compile(rf"(?:و\s+{VERBS}\s*){{3,}}")
LEAD = re.compile(r"\s+و\s+(?:باید|می‌توان|شاید|بهتر است)\b")
FOREIGN = re.compile(r"[\uac00-\ud7af\u3040-\u30ff\u4e00-\u9fff]+\s*")


TAIL2 = re.compile(r"(?:نگه داشت|دانست)\s+و\s+(?:دانست|آموخت)\b|و\s+دانست\s+و\s+آموخت")


def _cut_tail2(t):
    """دُمِ «…باید … نگه داشت و دانست و آموخت …» در جملهٔ پایانی را می‌برد."""
    body = t.rstrip()
    ends = body.endswith((".", "؟", "!"))
    core = body[:-1] if ends else body
    start = max(core.rfind("."), core.rfind("؟"), core.rfind("!"), core.rfind("؛")) + 1
    last = core[start:]
    if not TAIL2.search(last) or "باید" not in last:
        return t
    m2 = TAIL2.search(last)
    k = last.rfind("باید", 0, m2.start() + 1)
    if k == -1:
        return t
    j = last.rfind(" و ", 0, k)
    cut = j if j != -1 else k
    head = (core[:start] + last[:cut]).rstrip(" ،؛:")
    if len(head.split()) < MIN_WORDS:
        return t
    return head + "."


# بندهای پایانیِ قالبی («و خواننده از او آن را می‌آموزد و این آیه نمونهٔ آن است»…)
# که هیچ ادعای مربوط به همان آیه ندارند؛ فقط وقتی بریده می‌شوند که بندِ مستندِ
# پیش از آن دست‌کم MIN_WORDS واژه بماند.
_ST = r"[^.؛؟!]"
HOLLOW = [
    re.compile(rf"\s+و\s+(?:مفسر\s+آن\s+را\s+نگه\s+می‌دارد\s+و\s+)?خواننده\s+از\s+(?:او|آن)\s+{_ST}{{0,40}}?می‌آموزد(?:\s+که\s+{_ST}{{0,60}})?(?:\s+و\s+این\s+آیه\s+(?:نمونهٔ\s+آن\s+است|آن\s+را\s+(?:چنین\s+دارد|نشان\s+می‌دهد)))?(?=[.؛؟!]|$)"),
    re.compile(rf"\s+و\s+مفسر\s+آن\s+را\s+نگه\s+می‌دارد(?:\s+و\s+خواننده\s+{_ST}{{0,80}})?(?=[.؛؟!]|$)"),
    re.compile(rf"\s+و\s+خواننده\s+(?:آن\s+)?(?:را\s+)?(?:گرفته\s+شده\s+است|می‌گیرد|نگه\s+می‌دارد)(?:\s+و\s+(?:نگه\s+می‌دارد|می‌داند))?(?=[.؛؟!]|$)"),
    re.compile(rf"\s+و\s+شنونده\s+{_ST}{{0,40}}?می‌شنود\s+و\s+این\s+شنیدن\s+{_ST}{{0,50}}(?=[.؛؟!]|$)"),
    re.compile(rf"\s+و\s+مفسر\s+(?:آن\s+)?(?:نشان\s+داده\s+شده\s+است|را\s+نگه\s+می‌دارد)\s+و\s+خواننده\s+از\s+او\s+{_ST}{{0,80}}(?=[.؛؟!]|$)"),
]


HOLLOW_SENT = re.compile(
    rf"\s+و\s+(?:(?:سنت|مفسر)\s+{_ST}{{0,45}}?(?:نگه\s+داشته\s+است|نگه\s+می‌دارد)\s+و\s+)?"
    rf"(?:خواننده|شنونده|ما)\s+(?:از\s+\S+\s+)?{_ST}{{0,70}}?"
    rf"(?:می‌آموز(?:د|یم)|گرفته\s+شده\s+است|می‌گیرد|می‌شنود|نگه\s+می‌دارد|فراموش\s+نمی‌کند|می‌بیند)"
    rf"{_ST}*"
)


def _cut_hollow_sentences(t):
    parts = re.split(r"(?<=[.؛])", t)
    done = []
    for i, seg in enumerate(parts):
        m = HOLLOW_SENT.search(seg)
        if m:
            cand = seg[:m.start()]
            tail = seg[m.end():]
            rest = "".join(done) + cand + "".join(parts[i + 1:])
            if len((rest).split()) >= HOLLOW_MIN and len((("".join(done)) + cand).split()) >= 8:
                seg = cand.rstrip(" ،؛:") + ("." if not seg.rstrip().endswith("؛") else "؛") + tail
        done.append(seg)
    return "".join(done)


def _cut_hollow(t):
    out = _cut_hollow_sentences(t)
    out = out.replace(".؛", ".").replace("..", ".")
    for rx in HOLLOW:
        cand = rx.sub("", out)
        if cand != out and len(cand.split()) >= HOLLOW_MIN:
            out = cand
    out = re.sub(r"\s+(?:و|که|تا|را|با|از|در|به|این|آن)\s*([.؛؟!])", r"\1", out)
    out = re.sub(r"\s+(?:و|که|تا|را|با|از|در|به|این|آن)\s*$", "", out)
    out = out.rstrip(" ،؛:")
    if out != t and not out.endswith((".", "؟", "!", "»", ")")):
        out += "."
    return out


def strip_text(text):
    """بازمی‌گرداند (متنِ تازه، آیا تغییر کرد)."""
    t, ch = _strip_text1(text)
    t2 = _cut_tail2(t)
    t3 = _cut_hollow(t2)
    return t3, ch or t3 != t


def _strip_text1(text):
    t = FOREIGN.sub("", text)
    m = FILL.search(t)
    if not m:
        return t, t != text
    head = t[:m.start()]
    # آخرین «و باید/می‌توان» پیش از دُم؛ وگرنه آخرین مرزِ جمله.
    leads = list(LEAD.finditer(head))
    cut = None
    if leads:
        cut = leads[-1].start()
    else:
        for sep in ("؛", ".", "؟", "!"):
            i = head.rfind(sep)
            if i != -1 and (cut is None or i + 1 > cut):
                cut = i + 1
        if cut is None:
            cut = len(head)
    base = head[:cut].rstrip(" ،؛:")
    # اگر مرزِ جمله بریدنِ بسیار بزرگی کرده، به‌جای آن واژه‌های آخرِ سرِ بند را نگه دار
    if len(base.split()) < MIN_WORDS and len(head.split()) >= MIN_WORDS:
        base = head.rstrip(" ،؛:")
        base = re.sub(r"\s+(?:و|که|تا|را|با|از|در|به|این|آن|آنچه)$", "", base)
    if not base.endswith((".", "؟", "!", "»", ")")):
        base += "."
    return base, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surah", action="append", required=True)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    wanted = {f"{s}:" for s in args.surah}
    changed = short = 0
    shorts = []
    for path in EXT_PATHS:
        data = json.loads(path.read_text(encoding="utf-8"))
        dirty = False
        for vid, rec in data["verses"].items():
            if not any(vid.startswith(w) for w in wanted):
                continue
            groups = []
            for f in ("notes", "context", "classical", "modern", "critical", "research"):
                groups.append((f, rec.get(f, [])))
            for fid, fld in rec.get("extendedFields", {}).items():
                groups.append((fid, fld.get("entries", [])))
            for field, entries in groups:
                for j, e in enumerate(entries):
                    new, did = strip_text(e["text"])
                    if not did:
                        continue
                    if len(new.split()) < MIN_WORDS:
                        short += 1
                        shorts.append((vid, field, j, new))
                        continue
                    e["text"] = new
                    changed += 1
                    dirty = True
        if dirty and not args.dry:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"stripped={changed} too-short-left-untouched={short}")
    for s in shorts[:40]:
        print("  SHORT", *s)


if __name__ == "__main__":
    main()
