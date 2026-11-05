import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from translation_source import (  # noqa: E402
    TANZIL_TRANSLATION_COMMIT,
    TANZIL_TRANSLATION_ID,
    TANZIL_TRANSLATION_SHA256,
    load_tanzil_translation,
)


def test_pinned_tanzil_snapshot_has_complete_unique_verse_map():
    source_path = ROOT / "data" / "quran-fa-fooladvand.txt"
    translations = load_tanzil_translation(source_path)

    assert len(translations) == 6236
    assert len(set(translations)) == 6236
    assert translations[(1, 1)] == "به نام خداوند رحمتگر مهربان"
    assert translations[(114, 6)] == "چه از جنّ و [چه از] انس.»"
    assert TANZIL_TRANSLATION_SHA256 == "4d8cead0c9c7397e59adc4e773dd56b2da4c5700cda82d9ed648660fb190aa45"


def test_generated_offline_corpus_uses_tanzil_fooladvand_verbatim():
    source = load_tanzil_translation(ROOT / "data" / "quran-fa-fooladvand.txt")
    payload = json.loads((ROOT / "static" / "offline-corpus.json").read_text(encoding="utf-8"))
    verses = payload["verses"]
    generated = {(row[0], row[1]): row[3] for row in verses}

    assert len(verses) == 6236
    assert generated == source
    assert payload["translation"]["id"] == TANZIL_TRANSLATION_ID == "fa.fooladvand"
    assert payload["translation"]["sourceUrl"] == "https://tanzil.net/trans/fa.fooladvand"
    assert payload["translation"]["termsUrl"] == "https://tanzil.net/trans/"
    assert payload["translation"]["sourceFileSha256"] == TANZIL_TRANSLATION_SHA256
    assert payload["translation"]["snapshot"]["commit"] == TANZIL_TRANSLATION_COMMIT
    assert "non-commercial" in payload["translation"]["license"].lower()
    assert not (ROOT / "data" / "quran-fa-ih.json").exists()


def test_translation_attribution_and_noncommercial_terms_are_visible():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    attribution = (ROOT / "data" / "ATTRIBUTION.md").read_text(encoding="utf-8")

    assert "translation-credit-link" in html
    assert "translation-terms-link" in html
    assert "detail-translation-link" in html
    assert "state.translationMeta = corpus.translation" in app
    assert "fa.fooladvand" in attribution
    assert "غیرتجاری" in attribution
