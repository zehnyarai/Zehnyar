# -*- coding: utf-8 -*-
"""اسکنِ کیفیتِ یک سوره: python3 quran/tools/_scan_surah.py <surah> <last> [N]

نام مفسر، متنِ کوتاه (<۱۴ واژه)، تکرار، نبودِ برچسبِ «منابعِ مرتبط»، شکافِ دستوری و
(برای خوانش انتقادی) نسبتِ مدخل‌هایی که پرسش‌اند را گزارش می‌دهد."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LET = r'[\u0621-\u064A\u066E-\u06D3\u200C]'
NAMES = ['طبری','قرطبی','طبرسی','طوسی','رازی','زمخشری','بیضاوی','سیوطی','ابن کثیر','ابن‌کثیر','ابن عاشور','ابن‌عاشور','ابن العربی','ابن‌عربی','طباطبایی','شیرازی','بغوی','جزائری','المیزان','المیسر','راهن','صافی','ثعلبی','ماوردی','سعدی','تفسیر نمونه','تفسیر نور','آلوسی','فخر رازی','کاشانی','قمی','کشاف']
F = ('notes','context','classical','modern','critical','research')
W = r'(?![\u0621-\u06D3\u200c])'
GAPS = [r'(?:^|\s)از\s+(?:با|در|نیز|را|که|و|نقل شده|آورده|تنها|،)'+W, r'(?:^|\s)در\s+(?:گفته|نقل|است|را|می|نمی|نوشته)'+W,
 r'خودِ\s+هم\s', r'ِ\s+(?:خواند|دانست|گفت)'+W, r'گزارش\u200cهای\s+در\s', r'،\s*،|\(\s*[،؛]|\(\s*\)|«\s',
 r'(?:تفسیرِ|روایتِ|قولِ|نقلِ|گزارشِ|نظرِ|سندِ)\s+(?:را|است|که|می)'+W, r'(?:^|\s)از\s*(?:؛|\.|$)', r'\[analysis\]|پیش‌نویس|یادداشتِ تحریری',
 r'شده\s+است(?:ند|یم|ید|ی|م)\b']
def groups(r):
    for f in F:
        for e in r.get(f, []): yield f, e
    for fid, fld in r.get('extendedFields', {}).items():
        if fid == 'qiraat': continue
        for e in fld.get('entries', []): yield fid, e
def main(s, last, show):
    S = ROOT / 'static'
    srcs = [json.load(open(S / n))['verses'] for n in ('verse-dossiers.json', 'verse-dossier-extended-fields.json', 'verse-dossier-extended-fields-2.json')]
    c = dict(names=0, short=0, gap=0, dups=0, nolabel=0, missing=0, crit_entries=0, crit_questions=0); seen = set(); out = []
    for i in range(1, last + 1):
        v = f'{s}:{i}'
        recs = [x[v] for x in srcs if v in x]
        if not recs: c['missing'] += 1; continue
        for k, r in enumerate(recs):
            for f, e in groups(r):
                t = e['text']; pr = re.sub(r'«[^»]*»', '', t)
                if any(re.search(rf'(?<!{LET}){re.escape(n)}(?!{LET})', pr) for n in NAMES): c['names'] += 1; out.append(('N', v, f, t[:100]))
                if len(t.split()) < 14: c['short'] += 1; out.append(('S', v, f, t))
                if any(re.search(g, pr) for g in GAPS): c['gap'] += 1; out.append(('G', v, f, t[:200]))
                key = (k, ' '.join(t.split()))
                if key in seen: c['dups'] += 1; out.append(('D', v, f, t[:80]))
                seen.add(key)
            for e in r.get('critical', []):
                c['crit_entries'] += 1; c['crit_questions'] += '؟' in e['text']
                if 'منابعِ مرتبط با این پرسش' not in e['cite']: c['nolabel'] += 1
    print(s, c)
    for x in out[:show]: print('  ', *x)
if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 12)
