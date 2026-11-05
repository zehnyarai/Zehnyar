"""Shared, range-aware builder for al-A'raf 7:101–206 batches."""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from araf_7_later_data_common import QURTUBI_GAPS

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"

# These are the actual OpenITI verse-marker spans, including groups that cross
# one of the dossier-batch boundaries. They are not page references.
TUSI_SPANS = (
    (101, 101), (102, 102), (103, 103), (104, 104), (105, 105), (106, 106),
    (107, 108), (109, 110), (111, 112), (113, 114), (115, 116), (117, 118),
    (119, 122), (123, 124), (125, 125), (126, 126), (127, 127), (128, 128),
    (129, 129), (130, 130), (131, 131), (132, 132), (133, 133), (134, 135),
    (136, 136), (137, 137), (138, 138), (139, 139), (140, 140), (141, 141),
    (142, 142), (143, 143), (144, 144), (145, 145), (146, 146), (147, 147),
    (148, 148), (149, 149), (150, 150), (151, 151), (152, 152), (153, 153),
    (154, 154), (155, 155), (156, 156), (157, 157), (158, 158), (159, 159),
    (160, 160), (161, 161), (162, 162), (163, 163), (164, 164), (165, 165),
    (166, 166), (167, 167), (168, 168), (169, 169), (170, 170), (171, 171),
    (172, 173), (174, 174), (175, 175), (176, 176), (177, 177), (178, 178),
    (179, 179), (180, 180), (181, 181), (182, 183), (184, 185), (186, 186),
    (187, 187), (188, 188), (189, 190), (191, 193), (194, 194), (195, 195),
    (196, 196), (197, 197), (198, 198), (199, 199), (200, 200), (201, 201),
    (202, 202), (203, 203), (204, 204), (205, 205), (206, 206),
)
FAYD_SPANS = (
    (100, 103), (104, 116), (117, 128), (129, 134), (135, 138), (139, 143),
    (144, 145), (146, 150), (151, 156), (157, 158), (159, 169), (170, 174),
    (175, 176), (177, 181), (182, 187), (188, 193), (194, 202), (203, 205),
    (206, 206),
)
WASIT_SPANS = ((111, 112),)

SECTIONS = (
    (101, 102, "خبرِ آبادی‌هایِ پیشین و پیمانِ شکسته"),
    (103, 126, "موسی، فرعون و ایمانِ ساحران"),
    (127, 137, "سرکوب، بلاها و رهاییِ بنی‌اسرائیل"),
    (138, 141, "درخواستِ بت و یادآوریِ نعمت"),
    (142, 154, "میقاتِ موسی، الواح و فتنهٔ گوساله"),
    (155, 160, "دعا، پیامبرِ امی و نشانه‌هایِ قوم"),
    (161, 171, "سبت، میثاق و آزمونِ بنی‌اسرائیل"),
    (172, 174, "میثاقِ فطری و تفصیلِ آیات"),
    (175, 179, "مثلِ جداشدن از آیات و غفلت"),
    (180, 186, "نام‌هایِ نیکو و سنجشِ نشانه‌ها"),
    (187, 188, "پرسش از ساعت و محدودیتِ علمِ غیب"),
    (189, 198, "آدم، پرستش و ناتوانیِ معبودهایِ ساختگی"),
    (199, 206, "اخلاق، استعاذه و یادِ پروردگار"),
)


def _map_spans(spans: tuple[tuple[int, int], ...], first: int, last: int) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for start, end in spans:
        for ayah in range(max(start, first), min(end, last) + 1):
            result[f"7:{ayah}"] = (start, end)
    return result


def _fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def _scope(span: tuple[int, int]) -> str:
    start, end = span
    if start == end:
        return f"اعراف ۷:{_fa_num(start)}"
    return f"اعراف ۷:{_fa_num(start)}–{_fa_num(end)}"


def _unique_spans(mapping: dict[str, tuple[int, int]]) -> list[tuple[int, int]]:
    return list(dict.fromkeys(mapping.values()))


def _span_text(spans: list[tuple[int, int]]) -> str:
    return "، ".join(
        f"۷:{_fa_num(start)}" if start == end else f"۷:{_fa_num(start)}–{_fa_num(end)}"
        for start, end in spans
    )


class ArafLaterBuilder:
    def __init__(
        self,
        previous_builder,
        curated,
        *,
        start: int,
        end: int,
        batch_number: int,
        collection_id: str,
        collection_title: str,
        batch_title: str,
        section_number: int,
        later_section_number: int | None,
        method_addition: str,
        batch_status: str,
        source_snapshot_key: str,
        next_title: str | None,
        catalog_version: int,
    ):
        self.previous_builder = previous_builder
        self.curated = curated
        self.start, self.end = start, end
        self.BATCH_ID = f"dossier-{batch_number}"
        self.COLLECTION_ID = collection_id
        self.COLLECTION_TITLE = collection_title
        self.BATCH_TITLE = batch_title
        self.SECTION_NUMBER = section_number
        self.LATER_SECTION_NUMBER = later_section_number
        self.METHOD_ADDITION = method_addition
        self.BATCH_STATUS = batch_status
        self.SOURCE_SNAPSHOT_KEY = source_snapshot_key
        self.NEXT_TITLE = next_title
        self.CATALOG_VERSION = catalog_version
        self.VERSES = tuple(curated.DATA)
        self.expected = tuple(f"7:{ayah}" for ayah in range(start, end + 1))
        self.renderer = previous_builder.renderer
        self.base_builder = getattr(previous_builder, "BASE_BUILDER", getattr(previous_builder, "previous_builder", None))
        if self.base_builder is None:
            raise AttributeError("The earlier al-A'raf builder must expose its base_builder")
        self.source_builder = getattr(previous_builder, "source_builder", self.base_builder.source_builder)
        self.shared = previous_builder.shared
        self.TABARI, self.IBN, self.QURTUBI = self.renderer.TABARI, self.renderer.IBN, self.renderer.QURTUBI
        self.TUSI, self.FAYD = self.renderer.TUSI, self.renderer.FAYD
        self.QURANENC, self.WASIT = self.renderer.QURANENC, self.renderer.WASIT
        self.CLASSICAL_ORDER = self.renderer.CLASSICAL_ORDER
        self.SOURCE_ORDER = self.renderer.SOURCE_ORDER
        self.MODELS, self.FIELDS = self.renderer.MODELS, self.renderer.FIELDS
        self.TUSI_GROUPS = _map_spans(TUSI_SPANS, start, end)
        self.FAYD_GROUPS = _map_spans(FAYD_SPANS, start, end)
        self.WASIT_GROUPS = _map_spans(WASIT_SPANS, start, end)
        self.SECTIONS = SECTIONS
        self.QURTUBI_GAPS = {key for key in QURTUBI_GAPS if start <= int(key.split(":")[1]) <= end}
        self.START_MARKER = f"در بستهٔ اعراف ۷:{_fa_num(start)}–{_fa_num(end)}"
        self.NEXT_MARKER = (
            f"در بستهٔ اعراف ۷:{_fa_num(end + 1)}–{_fa_num(min(end + 50, 206))}"
            if end < 206 else None
        )
        self.ATTRIBUTION_MARKER = f"## {_fa_num(section_number)}. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:{_fa_num(start)}–{_fa_num(end)}"
        self.NEXT_ATTRIBUTION_MARKER = (
            f"## {_fa_num(later_section_number)}. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:{_fa_num(end + 1)}–{_fa_num(min(end + 50, 206))}"
            if end < 206 and later_section_number is not None else None
        )
        self.DATA = curated.DATA

    @property
    def BATCH_RANGE(self) -> str:
        return f"7:{self.start}–{self.end}"

    @contextmanager
    def renderer_batch_context(self):
        names = ("TUSI_GROUPS", "FAYD_GROUPS", "WASIT_GROUPS", "SECTIONS", "VERSES")
        missing = object()
        previous = {name: getattr(self.previous_builder, name, missing) for name in names}
        for name in names:
            setattr(self.previous_builder, name, getattr(self, name))
        try:
            with self.previous_builder.renderer_batch_context():
                self.renderer.source_evidence = self.source_evidence
                yield
        finally:
            for name, value in previous.items():
                if value is missing:
                    delattr(self.previous_builder, name)
                else:
                    setattr(self.previous_builder, name, value)

    def source_evidence(self, source_id: str, key: str) -> str:
        if source_id == self.QURTUBI and key in self.QURTUBI_GAPS:
            ayah = int(key.split(":")[1])
            return (
                f"شاهدِ پوشش: بدنهٔ آرشیوشدهٔ قرطبی زیرِ اعراف ۷:{_fa_num(ayah)} صریحاً "
                "«لا يوجد تفسير لهذه الأية» دارد؛ این خلأ به کلِ اثر یا نسخه‌هایِ دیگر تعمیم‌پذیر نیست."
            )
        return self.previous_builder.source_evidence(source_id, key)

    def validate_data(self, registry: dict | None = None) -> None:
        assert self.VERSES == self.expected
        assert set(self.DATA) == set(self.expected)
        assert set(self.TUSI_GROUPS) == set(self.expected)
        assert set(self.FAYD_GROUPS) == set(self.expected)
        assert set(self.WASIT_GROUPS) == set(self.expected)
        assert set(self.CLASSICAL_ORDER) == set(self.CLASSICAL_ORDER)
        assert {source["id"] for source in registry["sources"]} >= set(self.SOURCE_ORDER) if registry else True
        with self.renderer_batch_context():
            for key, record in self.DATA.items():
                assert record["title"].strip(), key
                assert len(record["notes"]) == len(record["critical"]) == len(record["research"]) == 5, key
                assert set(record["classical"]) == set(self.CLASSICAL_ORDER), key
                assert set(record["modern_sources"]) == {self.QURANENC, self.WASIT}, key
                assert len(record["model_terms"]) == 3 and all(record["model_terms"]), key
                for field in ("notes", "critical", "research"):
                    for text, source_ids in record[field]:
                        assert text.strip() and source_ids and set(source_ids) <= set(self.SOURCE_ORDER), (key, field, source_ids)
                        expanded = self.renderer.expand_item_text(text, key, field, source_ids)
                        assert len(expanded.split()) >= 14, (key, field, expanded)
                for source_id, text in record["classical"].items():
                    assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
                for source_id, text in record["modern_sources"].items():
                    assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
                if key in self.QURTUBI_GAPS:
                    assert "لا يوجد تفسير لهذه الأية" in record["classical"][self.QURTUBI], key
                assert self.TUSI_GROUPS[key][0] <= int(key.split(":")[1]) <= self.TUSI_GROUPS[key][1]
                assert self.FAYD_GROUPS[key][0] <= int(key.split(":")[1]) <= self.FAYD_GROUPS[key][1]

    def build_entry(self, key: str, record: dict, previous_key: str, next_key: str, dossier: dict) -> dict:
        # Use the stable base entry assembler, bypassing the 7:51–100 validator
        # so later Qurtubi coverage notes can be converted to the proper type.
        entry = self.base_builder.build_entry(key, record, previous_key, next_key, dossier)
        if key in self.QURTUBI_GAPS:
            qurtubi = next(item for item in entry["classical"] if item.get("sourceId") == self.QURTUBI)
            ayah = int(key.split(":")[1])
            qurtubi["kind"] = "source-coverage-note"
            qurtubi["text"] = (
                f"بدنهٔ آرشیوشدهٔ قرطبی برایِ اعراف ۷:{_fa_num(ayah)} صریحاً "
                "عبارتِ «لا يوجد تفسير لهذه الأية» را دارد؛ این خلأِ نسخهٔ بررسی‌شده است، "
                "نه شاهدی بر نبودِ شرح در کلِ اثر."
            )
            qurtubi["evidence"] = self.source_evidence(self.QURTUBI, key)
            qurtubi["limit"] = (
                "این کارت یادداشتِ پوشش است، نه تفسیر؛ بدنهٔ غایب در این آرشیو را به کلِ اثر "
                "یا نسخه‌هایِ دیگر تعمیم ندهید."
            )
        self.renderer.validate_generated_entry(key, entry)
        self.validate_generated_entry(key, entry)
        return entry

    def validate_generated_entry(self, key: str, entry: dict) -> None:
        assert entry["standard"] == 2 and entry["status"] == self.shared.STATUS, key
        texts = [
            re.sub(r"\s+", " ", item["text"]).strip()
            for field in self.FIELDS for item in entry[field]
        ]
        assert len(texts) == len(set(texts)), f"Repeated prose within {key}"
        classical = {item["sourceId"]: item for item in entry["classical"]}
        assert set(classical) == set(self.CLASSICAL_ORDER), key
        if key in self.QURTUBI_GAPS:
            assert classical[self.QURTUBI]["kind"] == "source-coverage-note"
            assert "نه تفسیر" in classical[self.QURTUBI]["limit"]
            assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
        else:
            assert all(item["kind"] == "source-summary" for item in entry["classical"])
        modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert modern_sources == {self.QURANENC, self.WASIT}
        assert models == set(self.MODELS)
        assert all(len(item["text"].split()) >= 14 for field in self.FIELDS for item in entry[field])

    def update_registry(self, registry: dict) -> dict:
        registry = self.previous_builder.update_registry(registry)
        registry["version"] = max(int(registry.get("version", 0)), 12 + int(self.BATCH_ID.split("-")[1]) - 63)
        by_id = {source["id"]: source for source in registry["sources"]}
        scope = f"اعراف ۷:۱–{_fa_num(self.end)}"
        for source_id in self.SOURCE_ORDER:
            source = by_id[source_id]
            source["availabilityNote"] = (
                f"در بستهٔ {scope} با دامنهٔ واقعیِ مدخل یا نشان بررسی شده؛ "
                "این ثبتِ دسترسی و حدودِ متن است، نه احرازِ حقوقِ اقتباس."
            )
            if source_id in {self.TUSI, self.FAYD}:
                snapshot = source.get("researchSnapshot", {})
                covered = set(snapshot.get("coveredBatches", [])) | {self.BATCH_ID}
                snapshot["coveredBatches"] = sorted(covered, key=lambda value: int(value.split("-")[1]))
                snapshot["edition"] = "not identified"
                snapshot["pagination"] = "not specified"
                snapshot["licenseStatus"] = "unresolved"
                source["researchSnapshot"] = snapshot
            elif source_id in {self.TABARI, self.IBN, self.QURTUBI, self.WASIT}:
                source["archiveSnapshot"] = self.source_builder.QURAN_EBOOK_ARCHIVES[source_id]
                source["licenseStatus"] = "review-needed"
        return registry

    def source_snapshot_metadata(self) -> dict:
        snapshot = self.base_builder.source_snapshot_metadata()
        snapshot["batchId"] = self.BATCH_ID
        snapshot["range"] = self.BATCH_RANGE
        tusi_groups = [span for span in _unique_spans(self.TUSI_GROUPS) if span[0] != span[1]]
        fayd_spans = _unique_spans(self.FAYD_GROUPS)
        wasit_groups = [span for span in _unique_spans(self.WASIT_GROUPS) if span[0] != span[1]]
        gap_text = ", ".join(f"7:{int(key.split(':')[1])}" for key in sorted(self.QURTUBI_GAPS, key=lambda item: int(item.split(":")[1]))) or "none"
        snapshot["scopeNotes"] = {
            "qurancom": (
                f"All target keys {self.BATCH_RANGE} are present in the pinned Tabari, Ibn Kathir, and Qurtubi v1.1 archives; "
                f"Qurtubi stored bodies explicitly marked no tafsir at {gap_text}."
            ),
            "wasit": (
                f"Wasit has ayah-keyed entries for all target keys {self.BATCH_RANGE}; "
                f"grouped duplicate body spans: {_span_text(wasit_groups) if wasit_groups else 'none'}."
            ),
            "tusi": (
                f"OpenITI grouped marker spans within/crossing this batch: {_span_text(tusi_groups) if tusi_groups else 'none'}; "
                "other target ayas have direct markers."
            ),
            "fayd": (
                f"OpenITI marker spans covering the target keys: {_span_text(fayd_spans)}; "
                "any span extending across a batch boundary is retained as a group, not a page reference."
            ),
            "quranenc": f"Local QuranEnc Arabic Muyassar v1.0.0 contains verse-keyed entries for all target ayat {self.BATCH_RANGE}.",
        }
        snapshot["rawWorkBench"] = {
            "path": "/tmp/araf/sources.json",
            "sha256": "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66",
            "quranEbookCommit": self.source_builder.QURAN_EBOOK_COMMIT,
            "quranEbookZipSha256": "1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842",
            "status": "temporary source extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
        }
        snapshot["quranEncSnapshot"] = {
            "sourceId": self.QURANENC,
            "file": "static/tafsir/arabic-moyassar-quranenc-1.0.0.json",
            "version": "1.0.0",
            "sha256": "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae",
        }
        return snapshot

    def update_source_snapshots(self, dossier: dict) -> None:
        self.renderer.update_source_snapshots(dossier)
        dossier.setdefault("sourceSnapshots", {})[self.SOURCE_SNAPSHOT_KEY] = self.source_snapshot_metadata()

    def canonical_notice(self, dossier: dict) -> str:
        return self.previous_builder.canonical_notice(dossier)

    def update_method(self, method: str) -> str:
        later_section = ""
        if self.NEXT_MARKER and self.NEXT_MARKER in method:
            later_section = method[method.index(self.NEXT_MARKER):].strip()
        method = self.previous_builder.update_method(method)
        if self.START_MARKER in method:
            method = method.split(self.START_MARKER, 1)[0].rstrip()
        result = method.rstrip() + self.METHOD_ADDITION
        return result + ((" " + later_section) if later_section else "")

    def _source_scope_text(self, source_id: str) -> str:
        if source_id in {self.TUSI, self.FAYD, self.WASIT}:
            mapping = self.TUSI_GROUPS if source_id == self.TUSI else self.FAYD_GROUPS if source_id == self.FAYD else self.WASIT_GROUPS
            spans = _unique_spans(mapping)
            groups = [span for span in spans if span[0] != span[1]]
            direct = len([span for span in spans if span[0] == span[1]])
            if source_id == self.TUSI:
                return (
                    f"دامنهٔ مستقیم یا گروهیِ واقعی: {_span_text(spans)}؛ "
                    "نشانِ گروهی مرزِ متن است، نه شمارهٔ صفحه."
                )
            if source_id == self.FAYD:
                return (
                    f"نشان‌هایِ گروهیِ فیض در این بازه: {_span_text(spans)}؛ "
                    "چاپ و صفحهٔ کتاب در metadata مشخص نشده است."
                )
            return (
                f"طنطاوی در این بازه {direct} موضعِ مستقیم و "
                f"گروهِ {_span_text(groups) if groups else 'بدونِ نشانِ گروهی'} دارد؛ "
                "مدخلِ گروهی به‌عنوانِ شرحِ مستقلِ دو آیه شمرده نمی‌شود."
            )
        return f"مدخل‌هایِ آیه‌محورِ آرشیوشده برایِ {self.BATCH_RANGE} بررسی شدند؛ چاپ و صفحهٔ متنِ تفسیری احراز نشده است."

    def build_catalog(self, registry: dict) -> dict:
        collection = self.base_builder.build_catalog(registry)
        by_id = {item["id"]: item for item in collection["items"]}
        collection["id"] = self.COLLECTION_ID
        collection["title"] = self.COLLECTION_TITLE
        collection["comparativeCore"]["scope"] = (
            f"اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)}؛ "
            "پیش‌نویسِ آیه‌محور در ادامهٔ روایتِ سوره"
        )
        qurtubi_gaps = "، ".join(f"۷:{_fa_num(int(key.split(':')[1]))}" for key in sorted(self.QURTUBI_GAPS, key=lambda item: int(item.split(":")[1]))) or "ندارد"
        tusi_groups = [span for span in _unique_spans(self.TUSI_GROUPS) if span[0] != span[1]]
        fayd_spans = _unique_spans(self.FAYD_GROUPS)
        wasit_groups = [span for span in _unique_spans(self.WASIT_GROUPS) if span[0] != span[1]]
        bases = {
            self.TABARI: f"مدخل‌هایِ آیه‌محورِ طبری برایِ اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)} در آرشیوِ Quran.com API v4 نسخهٔ 1.1 بررسی شدند؛ خلاصه‌ها نقلِ لفظی نیستند.",
            self.IBN: f"مدخل‌هایِ آیه‌محورِ ابن‌کثیر برایِ اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)} بررسی شدند؛ نقل‌هایِ روایی به خودِ مفسر منسوب‌اند.",
            self.QURTUBI: (
                f"مدخل‌هایِ قرطبی بررسی شدند؛ بدنهٔ ذخیره‌شده برایِ {qurtubi_gaps} صریحاً فاقدِ تفسیر است و این یادداشتِ پوشش به کلِ اثر تعمیم داده نمی‌شود."
                if self.QURTUBI_GAPS else
                f"مدخل‌هایِ آیه‌محورِ قرطبی برایِ اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)} بررسی شدند؛ خلاصه‌ها به بدنهٔ آرشیوشده محدودند."
            ),
            self.TUSI: f"متنِ ناقصِ *التبيان* از OpenITI بررسی شد؛ دامنه‌هایِ نشان‌دارِ گروهی {_span_text(tusi_groups) if tusi_groups else 'در این بازه ندارد'} و دیگر مواضعِ هدف مستقیم‌اند.",
            self.FAYD: f"متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ دامنه‌هایِ واقعیِ گروهی {_span_text(fayd_spans)} آشکارند و به صفحهٔ چاپی تبدیل نشده‌اند.",
            self.QURANENC: f"متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ تمامِ {self.end - self.start + 1} آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
            self.WASIT: f"مدخل‌هایِ طنطاوی برایِ کلیدهایِ هدف بررسی شدند؛ دامنهٔ گروهیِ آرشیو: {_span_text(wasit_groups) if wasit_groups else 'ندارد'}.",
        }
        scopes = {
            source_id: f"اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)}؛ {self._source_scope_text(source_id)}"
            for source_id in self.SOURCE_ORDER
        }
        for source_id in self.SOURCE_ORDER:
            by_id[source_id]["basis"] = bases[source_id]
            by_id[source_id]["scope"] = scopes[source_id]
            by_id[source_id]["version"] = by_id[source_id].get("version") or "مدخل یا نشانِ مستقیم/گروهی؛ چاپ و صفحهٔ کتاب احراز نشده"
        collection["comparativeCore"]["note"] = (
            f"در هر یک از {self.end - self.start + 1} پرونده، شش فیلد پنج‌بندی‌اند؛ پنج خوانشِ کهن، "
            "دو خلاصهٔ معاصر و سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی از هم جدا هستند. "
            f"خلأهایِ صریحِ بدنهٔ قرطبی در این بازه: {qurtubi_gaps}. "
            f"دامنه‌هایِ گروهیِ طوسی: {_span_text(tusi_groups) if tusi_groups else 'ندارد'}؛ "
            f"نشان‌هایِ فیض: {_span_text(fayd_spans)}؛ "
            f"گروه‌هایِ طنطاوی: {_span_text(wasit_groups) if wasit_groups else 'ندارد'}. "
            "گزارش‌هایِ روایی، اختلافِ قرائت و تحلیلِ تحریری به منبعِ خود نسبت دارند؛ خلاصه‌ها نقلِ لفظی نیستند. "
            "نسخه‌هایِ آرشیوی و OpenITI ناقص‌اند، چاپ یا صفحهٔ احرازنشده ساخته نشده، حقوقِ اقتباس/بازنشر حل نشده "
            "و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
        )
        collection["notice"] = (
            "این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است؛ خلاصه‌ها نقلِ لفظی نیستند و پینِ نسخه مجوزِ اقتباس یا بازنشر را احراز نمی‌کند. "
            + (
                f"بدنهٔ آرشیوشدهٔ قرطبی در {qurtubi_gaps} فاقدِ تفسیر است و به‌صورتِ یادداشتِ پوشش ثبت شده."
                if self.QURTUBI_GAPS else ""
            )
        )
        return collection

    def source_snapshot_metadata(self) -> dict:
        with self.renderer_batch_context():
            return self._source_snapshot_metadata()

    def _source_snapshot_metadata(self) -> dict:
        snapshot = self.base_builder.source_snapshot_metadata()
        snapshot["batchId"] = self.BATCH_ID
        snapshot["range"] = self.BATCH_RANGE
        tusi_groups = [span for span in _unique_spans(self.TUSI_GROUPS) if span[0] != span[1]]
        fayd_spans = _unique_spans(self.FAYD_GROUPS)
        wasit_groups = [span for span in _unique_spans(self.WASIT_GROUPS) if span[0] != span[1]]
        gap_text = ", ".join(f"7:{int(key.split(':')[1])}" for key in sorted(self.QURTUBI_GAPS, key=lambda item: int(item.split(":")[1]))) or "none"
        snapshot["scopeNotes"] = {
            "qurancom": f"All target keys {self.BATCH_RANGE} have verse-keyed entries; stored Qurtubi bodies explicitly marked no tafsir at {gap_text}.",
            "wasit": f"Verse-keyed entries cover the range; grouped body spans: {_span_text(wasit_groups) if wasit_groups else 'none'}.",
            "tusi": f"OpenITI grouped marker spans: {_span_text(tusi_groups) if tusi_groups else 'none'}; other target keys have direct markers.",
            "fayd": f"OpenITI marker spans covering the range: {_span_text(fayd_spans)}; markers denote text boundaries, not printed pages.",
            "quranenc": f"Local QuranEnc Arabic Muyassar v1.0.0 has verse-keyed entries for all keys {self.BATCH_RANGE}.",
        }
        snapshot["rawWorkBench"] = {
            "path": "/tmp/araf/sources.json",
            "sha256": "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66",
            "quranEbookCommit": self.source_builder.QURAN_EBOOK_COMMIT,
            "quranEbookZipSha256": "1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842",
            "status": "temporary source extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
        }
        snapshot["quranEncSnapshot"] = {
            "sourceId": self.QURANENC,
            "file": "static/tafsir/arabic-moyassar-quranenc-1.0.0.json",
            "version": "1.0.0",
            "sha256": "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae",
        }
        return snapshot

    def update_attribution_doc(self) -> None:
        later_section = ""
        if self.ATTRIBUTION_PATH.exists() and self.NEXT_ATTRIBUTION_MARKER:
            current = self.ATTRIBUTION_PATH.read_text(encoding="utf-8")
            if self.NEXT_ATTRIBUTION_MARKER in current:
                later_section = "\n\n" + current[current.index(self.NEXT_ATTRIBUTION_MARKER):].strip()
        self.previous_builder.update_attribution_doc()
        if not self.ATTRIBUTION_PATH.exists():
            return
        text = self.ATTRIBUTION_PATH.read_text(encoding="utf-8")
        if self.ATTRIBUTION_MARKER in text:
            text = text.split(self.ATTRIBUTION_MARKER, 1)[0].rstrip()
        addition = self._attribution_section()
        self.ATTRIBUTION_PATH.write_text(text.rstrip() + addition + later_section, encoding="utf-8")

    @property
    def ATTRIBUTION_PATH(self) -> Path:
        return Path(self.previous_builder.ATTRIBUTION_PATH)

    def _attribution_section(self) -> str:
        archives = self.source_builder.QURAN_EBOOK_ARCHIVES
        tusi = self.source_builder.OPENITI_SNAPSHOTS[self.TUSI]
        fayd = self.source_builder.OPENITI_SNAPSHOTS[self.FAYD]
        qurtubi_gaps = "، ".join(f"۷:{_fa_num(int(key.split(':')[1]))}" for key in sorted(self.QURTUBI_GAPS, key=lambda item: int(item.split(":")[1]))) or "ندارد"
        tusi_groups = [span for span in _unique_spans(self.TUSI_GROUPS) if span[0] != span[1]]
        fayd_spans = _unique_spans(self.FAYD_GROUPS)
        wasit_groups = [span for span in _unique_spans(self.WASIT_GROUPS) if span[0] != span[1]]
        return f"""

{self.ATTRIBUTION_MARKER}

این بسته اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)} را در {self.end - self.start + 1} پروندهٔ تحریری می‌افزاید. متنِ خامِ تفسیری در برنامه بازنشر نشده؛ خلاصه‌ها به نسخه و دامنهٔ واقعیِ مدخل یا نشان ارجاع دارند. پینِ نسخه برایِ بازبینی است و به‌تنهایی حقِ اقتباس یا بازنشر را ثابت نمی‌کند.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- commitِ مخزن: `{self.source_builder.QURAN_EBOOK_COMMIT}`؛ فایلِ مخزن GPL-3.0 است، اما دامنهٔ آن بر متنِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این بررسی احراز نشده است.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، Git blob `{archives[self.TABARI]['gitBlobSha']}`، SHA-256 `{archives[self.TABARI]['sha256']}`؛ کلیدهایِ هدف آیه‌محورند.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، Git blob `{archives[self.IBN]['gitBlobSha']}`، SHA-256 `{archives[self.IBN]['sha256']}`؛ کلیدهایِ هدف آیه‌محورند.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، Git blob `{archives[self.QURTUBI]['gitBlobSha']}`، SHA-256 `{archives[self.QURTUBI]['sha256']}`؛ بدنهٔ کلیدهایِ {qurtubi_gaps} صریحاً `لا يوجد تفسير لهذه الأية` دارد. این خلأِ آرشیوی به کلِ اثر تعمیم داده نشده است.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، Git blob `{archives[self.WASIT]['gitBlobSha']}`، SHA-256 `{archives[self.WASIT]['sha256']}`؛ دامنهٔ گروهیِ مشترک در این بازه: `{_span_text(wasit_groups) if wasit_groups else 'ندارد'}`.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{self.source_builder.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{self.source_builder.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`. دامنه‌هایِ گروهی: `{_span_text(tusi_groups) if tusi_groups else 'ندارد'}`؛ چاپ و صفحه احراز نشده.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{self.source_builder.OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{self.source_builder.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`. نشان‌هایِ دامنه: `{_span_text(fayd_spans)}`؛ صفحهٔ چاپی یا اطلاعاتِ نشرِ نامشخص ساخته نشده است.
- metadata متن‌هایِ OpenITI آنها را نسخه‌هایِ ناقص و برگرفته از altafsir.com معرفی می‌کند؛ مجوزِ اقتباس/بازنشر در این کار احراز نشده است.

### منبعِ معاصرِ محلی و استخراجِ موقت

- التفسير الميسر، QuranEnc، نسخهٔ 1.0.0، فایلِ `quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json`، SHA-256 `b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae`؛ مدخل‌هایِ آیه‌به‌آیهٔ اعراف ۷:{_fa_num(self.start)}–{_fa_num(self.end)} بررسی شدند.
- استخراجِ کاریِ آرشیوها و نشان‌هایِ OpenITI در `/tmp/araf/sources.json` با SHA-256 `d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66` موقت بود و واردِ مخزن نشده است.

در فایلِ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده، ارجاع و metadata ذخیره شده‌اند. همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند.
"""

    def _normalized_texts(self, entry: dict) -> list[str]:
        return [
            re.sub(r"\s+", " ", item.get("text", "")).strip()
            for field in self.FIELDS for item in entry.get(field, [])
        ]

    def _existing_texts(self, dossier: dict, excluded: set[str]) -> set[str]:
        return {
            re.sub(r"\s+", " ", item.get("text", "")).strip()
            for key, entry in dossier["verses"].items() if key not in excluded
            for field in self.FIELDS for item in entry.get(field, [])
            if item.get("text", "").strip()
        }

    def main(self) -> None:
        registry = self.update_registry(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))
        dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
        assert all(f"7:{ayah}" in dossier["verses"] for ayah in range(1, self.start))
        present = set(self.expected) & set(dossier["verses"])
        assert len(present) in {0, len(self.expected)}, f"Partial existing batch: {sorted(present)[:5]}"
        self.validate_data(registry)

        context_dossier = json.loads(json.dumps(dossier, ensure_ascii=False))
        for key, record in self.DATA.items():
            context_dossier["verses"].setdefault(key, {"title": record["title"]})
        if self.end < 206:
            next_key = f"7:{self.end + 1}"
            context_dossier["verses"].setdefault(next_key, {"title": self.NEXT_TITLE or "ادامهٔ روایتِ اعراف"})

        with self.renderer_batch_context():
            previous_texts = self._existing_texts(dossier, set(self.expected))
            for index, key in enumerate(self.expected):
                previous_key = self.expected[index - 1] if index else f"7:{self.start - 1}"
                next_key = self.expected[index + 1] if index + 1 < len(self.expected) else (
                    f"7:{self.end + 1}" if self.end < 206 else None
                )
                entry = self.build_entry(key, self.DATA[key], previous_key, next_key, context_dossier)
                for text in self._normalized_texts(entry):
                    assert text not in previous_texts, f"Repeated prose against an earlier verse/batch: {key}: {text}"
                    previous_texts.add(text)
                dossier["verses"][key] = entry
            self.update_source_snapshots(dossier)

        dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != self.BATCH_ID]
        dossier["batches"].append({
            "id": self.BATCH_ID,
            "title": self.BATCH_TITLE,
            "range": self.BATCH_RANGE,
            "count": len(self.expected),
            "status": self.BATCH_STATUS,
        })
        dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
        dossier["notice"] = self.canonical_notice(dossier)
        dossier["editorialMethod"] = self.update_method(dossier.get("editorialMethod", ""))

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        catalog["collections"] = [item for item in catalog["collections"] if item.get("id") != self.COLLECTION_ID]
        with self.renderer_batch_context():
            catalog["collections"].append(self.build_catalog(registry))
        catalog["version"] = max(int(catalog.get("version", 0)), self.CATALOG_VERSION)

        DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.update_attribution_doc()
        print(f"Added {len(self.expected)} dossiers; total={len(dossier['verses'])}; batch={self.BATCH_RANGE}")
