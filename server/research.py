"""Dated, selective evidence context. Selection is not a diagnosis or live literature search."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'src/data'
DATA = json.loads((ROOT / 'research.json').read_text())
RULES = json.loads((ROOT / 'evidence-rules.json').read_text())
MEASURED = {'ec', 'sar', 'rsc', 'boron', 'sodium', 'chloride', 'nitrogen', 'nitrate', 'phosphorus', 'potassium', 'iron', 'zinc', 'organic'}


def normal(text):
    return re.sub(r'\s+', ' ', re.sub(r'[\u200c\u200e\u200f-]', ' ', text.replace('ي', 'ی').replace('ك', 'ک'))).lower().strip()


def values_text(value, depth=0):
    if depth > 8:
        return ''
    if isinstance(value, str):
        return value[:12000]
    if isinstance(value, list):
        return ' '.join(values_text(v, depth + 1) for v in value[:100])
    if not isinstance(value, dict):
        return ''
    return ' '.join(k if k in MEASURED and isinstance(v, (int, float)) and not isinstance(v, bool) else values_text(v, depth + 1) for k, v in list(value.items())[:100])


def contains(text, word):
    return re.search(r'(?<!\w)' + re.escape(normal(word)) + r'(?!\w)', text) is not None


def evidence_pack(context, limit=6):
    text = normal(values_text(context))
    ranked = []
    for index, record in enumerate(DATA['records']):
        tags = sum(contains(text, word) for word in record.get('tags', []))
        score = 0 if record.get('tags') and not tags else sum(contains(text, word) for word in RULES['topics'].get(record['topic'], [])) + 3 * tags
        if score:
            ranked.append((score, RULES['kind_tiebreak'].get(record['kind'], 0), record['year'] or 0, index, record))
    ranked.sort(key=lambda r: (-r[0], -r[1], -r[2], r[3]))
    chosen, seen_topics = set(), set()
    for *_, r in ranked:
        if r['topic'] in seen_topics:
            continue
        seen_topics.add(r['topic'])
        chosen.add(r['id'])
        rest = [entry[-1] for entry in ranked if entry[-1]['topic'] == r['topic'] and entry[-1]['id'] != r['id']]
        second = next((item for item in rest if (item['kind'] in ('review', 'extension')) != (r['kind'] in ('review', 'extension'))), rest[0] if rest else None)
        if second:
            chosen.add(second['id'])
    selected = [{**entry[-1], 'source': entry[-1]['url']} for entry in ranked if entry[-1]['id'] in chosen]
    return selected[:max(0, min(8, limit))]
