"""Curated research summaries. Not a comprehensive database or validated model."""
import json
from pathlib import Path
DATA = json.loads((Path(__file__).resolve().parent.parent / 'src/data/research.json').read_text())

def evidence_pack(context, limit=6):
    # Selection is based on farmer-reported words/context, not image recognition.
    text = json.dumps(context, ensure_ascii=False).casefold()
    keywords = {'آب و خاک':['آب','شوری','خشکی','water','wilting'], 'تغذیه':['تغذیه','زرد','yellowing','nitrogen'], 'آفات و بیماری‌ها':['آفت','برگ','sticky','spots','حشره'], 'برداشت و پس از برداشت':['برداشت','میوه','fruit'], 'هرس و باردهی':['yield','باردهی','هرس','شاخه'], 'اقلیم و گرده‌افشانی':['گل','جوانه','گرده','bloom'], 'پایه و رقم':['ریشه','طوقه','پایه']}
    ranked = sorted(DATA['records'], key=lambda r: sum(k.casefold() in text for k in keywords.get(r['topic'],[])), reverse=True)
    return [{'id': r['id'], 'finding':r['finding'], 'limitations':r['limitations'], 'region':r['region'], 'kind':r['kind'], 'access':r['access'], 'source':r['url'], 'year':r['year'], 'checked_at':r['checked_at']} for r in ranked[:limit]]
