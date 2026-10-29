const CORPUS_URL = "static/offline-corpus.json";
const LEXICON_URL = "static/concept-lexicon.json";
const STORY_INDEX_URL = "static/story-index.json";
const STORY_DOSSIERS_URL = "static/story-dossiers.json";
const TOPIC_CATALOG_URL = "static/topic-catalog.json";
const TAFSIR_SOURCES_URL = "static/tafsir-sources.json";
const TAFSIR_CATALOG_URL = "static/tafsir-catalog.json";
const VERSE_STUDIES_URL = "static/verse-study-annotations.json";
const SCHOLAR_BANK_URL = "static/scholar-bank.json";
const SCHOLAR_LAYER_URL = "static/verse-scholar-layer.json";
const SCHOLAR_PILOT_URL = "static/scholar-pilot.json";
const SCHOLAR_APPLICATION_URL = "static/scholar-application.json";
const VERSE_DOSSIER_URL = "static/verse-dossiers.json";
const SURAH_DOSSIERS_URL = "static/surah-dossiers.json";
const NOTEBOOK_KEY = "zehnyar-verse-notebook-v2";
const FIELD_NOTES_KEY = "quran-pazhuheh-field-notes-v1";
const VERSE_PROPOSALS_KEY = "quran-pazhuheh-verse-proposals-v1";
const ADMIN_TOKEN_KEY = "zehnyar-admin-token-session";
const PAGE_SIZE = 12;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = {
  scholarAnchorById: null,
  scholarLayer: null,
  scholarPilot: null,
  scholarPilotData: null,
  scholarApplication: null,
  scholarApplicationMeta: null,
  verseDossiers: null,
  verseDossierMeta: null,
  screen: "search",
  corpus: [],
  recordById: new Map(),
  lexicon: null,
  concepts: [],
  topicCategories: [],
  tafsirSources: [],
  tafsirRegistry: [],
  tafsirLoads: new Map(),
  tafsirLoading: null,
  tafsirLoadFailed: false,
  fieldNotes: loadFieldNotes(),
  tafsirCatalog: [],
  verseStudies: {},
  stories: [],
  storyDossiers: {},
  selectedStory: null,
  storyTab: "verses",
  libraryMode: null,
  selectedSurah: null,
  surahDossiers: {},
  surahDossierMeta: { sources: {}, editorialMethod: {}, notice: "" },
  surahTab: "overview",
  query: "",
  concept: null,
  terms: [],
  matches: [],
  shown: PAGE_SIZE,
  filter: "all",
  contextVerseId: null,
  inlineStudy: { verseId: null, tab: "notes" },
  selected: null,
  detailTab: "notes",
  searchTranslations: false,
  notebook: loadNotebook(),
  verseProposals: loadVerseProposals(),
};

function escapeHTML(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function faNumber(value) {
  return Number(value || 0).toLocaleString("fa-IR");
}

function normalize(value = "") {
  return value
    .replace(/[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]/g, "")
    .replace(/[ٱأإآ]/g, "ا")
    .replace(/ى/g, "ی")
    .replace(/ي/g, "ی")
    .replace(/ئ/g, "ی")
    .replace(/ؤ/g, "و")
    .replace(/ك/g, "ک")
    .replace(/ة/g, "ه")
    .replace(/[ـ‌]/g, " ")
    .replace(/[^\w\s\u0600-\u06ff]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function loadNotebook() {
  try {
    const saved = JSON.parse(localStorage.getItem(NOTEBOOK_KEY) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function persistNotebook() {
  localStorage.setItem(NOTEBOOK_KEY, JSON.stringify(state.notebook));
}

function loadFieldNotes() {
  try {
    const saved = JSON.parse(localStorage.getItem(FIELD_NOTES_KEY) || "{}");
    return saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {};
  } catch {
    return {};
  }
}

function saveFieldNote(input) {
  const key = `${input.dataset.verseId}:${input.dataset.fieldNote}`;
  state.fieldNotes[key] = input.value.slice(0, 3000);
  localStorage.setItem(FIELD_NOTES_KEY, JSON.stringify(state.fieldNotes));
  const status = input.parentElement.querySelector(".field-note-status");
  if (status) status.textContent = "ذخیره شد؛ فقط روی همین دستگاه.";
}

function loadVerseProposals() {
  try {
    const value = JSON.parse(localStorage.getItem(VERSE_PROPOSALS_KEY) || "[]");
    return Array.isArray(value) ? value.filter((item) => item?.verseId && item.kind && item.claim && item.witness).map((item) => ({ ...item, storage: "local" })) : [];
  } catch { return []; }
}

function persistVerseProposals() {
  localStorage.setItem(VERSE_PROPOSALS_KEY, JSON.stringify(state.verseProposals.filter((item) => item.storage === "local")));
}

async function refreshPublicProposals() {
  try {
    let localItems = state.verseProposals.filter((item) => item.storage === "local");
    for (const item of [...localItems]) {
      const migrated = await fetch("/api/proposals", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verse_id: item.verseId, kind: item.kind, claim: item.claim, witness: item.witness }) });
      if (migrated.ok) localItems = localItems.filter((candidate) => candidate.id !== item.id);
    }
    const response = await fetch("/api/proposals", { cache: "no-store" });
    if (!response.ok) return;
    const payload = await response.json();
    const published = (payload.proposals || []).map((item) => ({ ...item, verseId: item.verse_id, storage: "server" }));
    state.verseProposals = [...published, ...localItems];
    persistVerseProposals();
  } catch { /* Offline readers retain their own local proposals. */ }
}

function isSaved(verse) {
  return state.notebook.some((item) => item.id === verse.id);
}

function saveCurrentVerse() {
  const verse = state.selected;
  if (!verse) return;
  const index = state.notebook.findIndex((item) => item.id === verse.id);
  if (index >= 0) {
    state.notebook.splice(index, 1);
  } else {
    state.notebook.unshift({
      id: verse.id,
      query: state.query,
      reference: verse.reference,
      arabic: verse.arabic,
      persian: verse.persian,
      note: "",
      savedAt: new Date().toISOString(),
    });
  }
  persistNotebook();
  updateSaveButton();
}

function updateSaveButton() {
  const button = $("#save-verse");
  const saved = state.selected && isSaved(state.selected);
  button.textContent = saved ? "در دفتر ✓" : "ذخیره در دفتر";
  button.classList.toggle("saved", Boolean(saved));
}

function recordFromTuple(tuple) {
  const [surah, ayah, arabic, persian, surahName, revelation] = tuple;
  return {
    id: `${surah}:${ayah}`,
    surah,
    ayah,
    arabic,
    persian,
    surahName,
    revelation,
    reference: `${surahName} ${surah}:${ayah}`,
    arabicNormalized: normalize(arabic),
    persianNormalized: normalize(persian),
  };
}

async function loadScholarLayer() {
  try {
    const [bankResponse, layerResponse, pilotResponse, applicationResponse, dossierResponse] = await Promise.all([
      fetch(SCHOLAR_BANK_URL), fetch(SCHOLAR_LAYER_URL), fetch(SCHOLAR_PILOT_URL), fetch(SCHOLAR_APPLICATION_URL), fetch(VERSE_DOSSIER_URL),
    ]);
    if (!bankResponse.ok || !layerResponse.ok) return;
    const bank = await bankResponse.json();
    const layer = await layerResponse.json();
    state.scholarAnchorById = new Map((bank.anchors || []).map((anchor) => [anchor.id, anchor]));
    state.scholarLayer = layer.anchors || {};
    state.scholarPilot = new Set(layer.pilot || []);
    if (pilotResponse.ok) {
      state.scholarPilotData = (await pilotResponse.json()).verses || {};
    }
    if (applicationResponse.ok) {
      const application = await applicationResponse.json();
      state.scholarApplication = application.verses || {};
      state.scholarApplicationMeta = {
        batches: application.batches || [],
        method: application.method || null,
      };
    }
    if (dossierResponse.ok) {
      const dossier = await dossierResponse.json();
      state.verseDossiers = dossier.verses || {};
      state.verseDossierMeta = {
        batches: dossier.batches || [],
        method: dossier.editorialMethod || "",
        notice: dossier.notice || "",
      };
    }
  } catch (error) {
    // لایهٔ پژوهشی اختیاری است؛ نبودِ آن نباید مطالعهٔ آیه را متوقف کند.
    state.scholarAnchorById = null;
  }
}

async function loadData() {
  const [corpusResponse, lexiconResponse, storyResponse, storyDossiersResponse, catalogResponse, tafsirRegistryResponse, tafsirCatalogResponse, studiesResponse, surahDossiersResponse] = await Promise.all([
    fetch(CORPUS_URL), fetch(LEXICON_URL), fetch(STORY_INDEX_URL), fetch(STORY_DOSSIERS_URL), fetch(TOPIC_CATALOG_URL), fetch(TAFSIR_SOURCES_URL), fetch(TAFSIR_CATALOG_URL), fetch(VERSE_STUDIES_URL), fetch(SURAH_DOSSIERS_URL),
  ]);
  if (!corpusResponse.ok || !lexiconResponse.ok || !storyResponse.ok || !storyDossiersResponse.ok || !catalogResponse.ok || !tafsirRegistryResponse.ok || !tafsirCatalogResponse.ok || !studiesResponse.ok || !surahDossiersResponse.ok) {
    throw new Error("پیکرهٔ محلی یا فهرست پژوهش در دسترس نیست.");
  }
  const corpus = await corpusResponse.json();
  state.lexicon = await lexiconResponse.json();
  const catalog = await catalogResponse.json();
  const tafsirRegistry = await tafsirRegistryResponse.json();
  const tafsirCatalog = await tafsirCatalogResponse.json();
  state.tafsirCatalog = tafsirCatalog.collections || [];
  const studyPayload = await studiesResponse.json();
  state.verseStudies = studyPayload.verses || {};
  state.concepts = [...(state.lexicon.concepts || []), ...(catalog.concepts || [])];
  state.topicCategories = catalog.categories || [];
  state.stories = (await storyResponse.json()).stories || [];
  state.storyDossiers = (await storyDossiersResponse.json()).dossiers || {};
  const surahDossierPayload = await surahDossiersResponse.json();
  state.surahDossiers = surahDossierPayload.surahs || {};
  state.surahDossierMeta = {
    sources: surahDossierPayload.sources || {},
    editorialMethod: surahDossierPayload.editorialMethod || {},
    notice: surahDossierPayload.notice || "",
  };
  state.tafsirRegistry = tafsirRegistry.sources || [];
  const tafsirResults = await Promise.allSettled(state.tafsirRegistry.filter((source) => source.preload !== false).map(loadTafsirSource));
  state.tafsirSources = tafsirResults.filter((result) => result.status === "fulfilled").map((result) => result.value);
  state.corpus = corpus.verses.map(recordFromTuple);
  state.recordById = new Map(state.corpus.map((record) => [record.id, record]));
  $("#result-corpus").textContent = `${faNumber(state.corpus.length)} آیه`;
  await loadScholarLayer();
  await refreshPublicProposals();
  renderStarters();
}

function loadTafsirSource(source) {
  if (state.tafsirLoads.has(source.id)) return state.tafsirLoads.get(source.id);
  const request = fetch(source.file).then((response) => {
    if (!response.ok) throw new Error(`بارگیری ${source.title} ناموفق بود.`);
    return response.json();
  }).then((payload) => ({
    ...source,
    verses: payload.verses || {},
    contents: payload.contents || {},
    ayahMapping: payload.ayahMapping || {},
    edition: payload.edition || {},
  })).catch((error) => {
    state.tafsirLoads.delete(source.id);
    throw error;
  });
  state.tafsirLoads.set(source.id, request);
  return request;
}

async function loadDeferredTafsir(sourceId) {
  const source = state.tafsirRegistry.find((item) => item.id === sourceId && item.preload === false);
  if (!source || state.tafsirSources.some((loaded) => loaded.id === sourceId) || state.tafsirLoading) return;
  state.tafsirLoading = sourceId;
  state.tafsirLoadFailed = false;
  renderDetailPanel();
  try {
    const loaded = await loadTafsirSource(source);
    // Keep only one large comparison text in memory at a time on mobile.
    state.tafsirSources = [...state.tafsirSources.filter((item) => item.preload !== false), loaded];
  } catch {
    state.tafsirLoadFailed = true;
  } finally {
    state.tafsirLoads.delete(sourceId);
    state.tafsirLoading = null;
  }
  if (state.detailTab === "tafsir") renderDetailPanel();
}

function renderStarters() {
  // صفحهٔ نخست عمداً ساده است؛ نقشهٔ کامل موضوعات از دکمهٔ جداگانه باز می‌شود.
  const list = $("#starter-list");
  if (!list) return;
  list.innerHTML = "";
}

function resolveConcept(query) {
  const normalized = normalize(query);
  const matches = state.concepts.flatMap((concept) => (concept.aliases || []).map((alias) => ({ concept, alias: normalize(alias) })))
    .filter((item) => item.alias && normalized.includes(item.alias))
    .sort((a, b) => b.alias.length - a.alias.length);
  return matches[0]?.concept || null;
}

function probablyArabic(value) {
  const raw = String(value || "");
  return /[يكىةىأإؤء]/.test(raw) || normalize(raw).split(" ").join("").length <= 4;
}

function uniqueTerms(terms) {
  const seen = new Set();
  return terms.filter((term) => {
    const key = `${term.scope}:${term.value}`;
    if (!term.value || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildTerms(query, concept, includeTranslation, manualArabic = "") {
  const normalizedQuery = normalize(query);
  const terms = manualArabic.split(/[،,]/).map((value) => value.trim()).filter(Boolean).map((value) => ({
    value: normalize(value), label: `واژهٔ عربیِ شما: ${value}`, type: "exact", scope: "arabic", origin: "کلیدواژهٔ عربیِ کاربر",
  }));
  if (concept) {
    (concept.equivalents || []).forEach(([term, label]) => terms.push({
      value: normalize(term), label, type: "equivalent", scope: "arabic", origin: "معادل قرآنیِ واژه‌نامه",
    }));
    (concept.related || []).forEach(([term, label]) => terms.push({
      value: normalize(term), label, type: "related", scope: "arabic", origin: "پیوند مرتبطِ واژه‌نامه",
    }));
  }
  const isKnownEquivalent = (concept?.equivalents || []).some(([term]) => normalize(term) === normalizedQuery);
  if (probablyArabic(query) && (!concept || isKnownEquivalent)) {
    terms.unshift({
      value: normalizedQuery, label: "عبارت عربیِ کاربر", type: "exact", scope: "arabic", origin: "عبارتِ کاربر",
    });
  }
  if (includeTranslation) {
    terms.unshift({
      value: normalizedQuery, label: "عبارت فارسیِ کاربر", type: "exact", scope: "persian", origin: "جست‌وجوی دقیق در ترجمه",
    });
  }
  return uniqueTerms(terms);
}

function typeLabel(type) {
  return { equivalent: "معادل", related: "موضوع/هم‌معنا", exact: "کلیدواژه یا هم‌ریشه" }[type] || "شاهد";
}

function evaluateRecord(record, terms) {
  const evidence = [];
  terms.forEach((term) => {
    const inArabic = term.scope !== "persian" && record.arabicNormalized.includes(term.value);
    const inPersian = term.scope === "persian" && record.persianNormalized.includes(term.value);
    if (!inArabic && !inPersian) return;
    evidence.push({
      ...term,
      source: inArabic ? "متن عربی" : "ترجمهٔ فارسی",
    });
  });
  if (!evidence.length) return null;
  const rank = { exact: 30, equivalent: 12, related: 3 };
  const type = evidence.some((item) => item.type === "exact") ? "exact"
    : evidence.some((item) => item.type === "equivalent") ? "equivalent" : "related";
  return { ...record, evidence, type, score: evidence.reduce((sum, item) => sum + rank[item.type], 0) };
}

function searchResearchFields() {
  const values = {
    keyword: $("#keyword-query").value.trim(),
    concept: $("#concept-query").value.trim(),
    topic: $("#topic-query").value.trim(),
    quranicEquivalent: $("#quranic-equivalent-query").value.trim(),
    translationEquivalent: $("#translation-equivalent-query").value.trim(),
    semantic: $("#semantic-query").value.trim(),
    synonym: $("#synonym-query").value.trim(),
    root: $("#root-query").value.trim(),
  };
  const status = $("#search-status");
  const primary = values.keyword || values.concept || values.topic || values.quranicEquivalent || values.translationEquivalent || values.semantic || values.synonym || values.root;
  if (!primary) {
    status.textContent = "دست‌کم یکی از مسیرهای جست‌وجو را وارد کنید.";
    $("#keyword-query").focus();
    return;
  }

  const conceptMatch = resolveConcept(values.concept);
  const topicMatch = resolveConcept(values.topic);
  const semanticMatch = resolveConcept(values.semantic);
  const synonymMatch = resolveConcept(values.synonym);
  const activeConcept = conceptMatch || topicMatch || semanticMatch || synonymMatch || resolveConcept(primary);
  const terms = [];
  const splitTerms = (value, label, type, origin, scope = "arabic", compact = false) => value.split(/[،,]/).map((item) => item.trim()).filter(Boolean).forEach((item) => {
    const itemScope = scope === "auto" ? (probablyArabic(item) ? "arabic" : "persian") : scope;
    terms.push({ value: compact ? normalize(item).replaceAll(" ", "") : normalize(item), label: `${label}: ${item}`, type, scope: itemScope, origin });
  });
  const addConcept = (concept, origin, modes = ["equivalents", "related"]) => {
    if (!concept) return;
    if (modes.includes("equivalents")) (concept.equivalents || []).forEach(([term, label]) => terms.push({
      value: normalize(term), label, type: "equivalent", scope: "arabic", origin,
    }));
    if (modes.includes("related")) (concept.related || []).forEach(([term, label]) => terms.push({
      value: normalize(term), label, type: "related", scope: "arabic", origin,
    }));
  };

  splitTerms(values.keyword, "کلیدواژه", "exact", "کلیدواژهٔ واردشده", "auto");
  splitTerms(values.root, "هم‌ریشه / صورت", "exact", "ریشه یا صورتِ عربیِ واردشده", "arabic", true);
  splitTerms(values.quranicEquivalent, "معادل قرآنی", "equivalent", "معادل قرآنیِ واردشده", "arabic");
  splitTerms(values.translationEquivalent, "معادل ترجمه", "equivalent", "معادلِ واردشده در ترجمهٔ فارسی", "persian");
  addConcept(conceptMatch, "مفهومِ واژه‌نامه");
  addConcept(topicMatch, "موضوعِ نقشهٔ قرآن");
  addConcept(semanticMatch, "هم‌معنای واژه‌نامه", ["related"]);
  addConcept(synonymMatch, "مترادفِ واژه‌نامه", ["equivalents", "related"]);
  if (values.semantic && !semanticMatch) splitTerms(values.semantic, "هم‌معنای واردشده", "related", "هم‌معنای بدون نگاشت واژه‌نامه", "auto");
  if (values.synonym && !synonymMatch) splitTerms(values.synonym, "مترادفِ واردشده", "related", "مترادف بدون نگاشت واژه‌نامه", "auto");
  if (values.topic && !topicMatch) splitTerms(values.topic, "موضوعِ واردشده", "related", "موضوع بدون نگاشت واژه‌نامه", "auto");
  if (values.concept && !conceptMatch) splitTerms(values.concept, "مفهومِ واردشده", "related", "مفهوم بدون نگاشت واژه‌نامه", "auto");

  state.terms = uniqueTerms(terms);
  if (!state.terms.length) {
    status.textContent = "برای این ورودی هنوز مسیر قابل جست‌وجویی ساخته نشد؛ یک کلیدواژه، معادل یا صورت عربی وارد کنید.";
    return;
  }
  state.query = primary;
  state.concept = activeConcept;
  state.matches = state.corpus.map((record) => evaluateRecord(record, state.terms)).filter(Boolean)
    .sort((a, b) => b.score - a.score || a.surah - b.surah || a.ayah - b.ayah);
  state.shown = PAGE_SIZE;
  state.filter = "all";
  state.contextVerseId = state.matches[0]?.id || null;
  state.inlineStudy = { verseId: null, tab: "notes" };
  state.selected = null;
  status.textContent = "";
  renderResults();
  navigate("results");
}

function runStarter(query) {
  $("#concept-query").value = query;
  ["#keyword-query", "#topic-query", "#quranic-equivalent-query", "#translation-equivalent-query", "#semantic-query", "#synonym-query", "#root-query"].forEach((selector) => { $(selector).value = ""; });
  searchResearchFields();
}

function renderTermGroups() {
  const byType = ["equivalent", "related", "exact"].map((type) => ({ type, terms: state.terms.filter((term) => term.type === type) })).filter((group) => group.terms.length);
  $("#active-terms").innerHTML = byType.map((group) => `<span class="term-group ${group.type === "related" ? "related" : ""}"><b>${typeLabel(group.type)}:</b> ${group.terms.map((term) => escapeHTML(term.label)).join("، ")}</span>`).join("");
}

function resultsByFilter() {
  // «فهم آیه در سیاق» یک نمای تحلیلی است، نه یک لایهٔ حذف‌کنندهٔ نتایج.
  return state.filter === "all" || state.filter === "context" ? state.matches : state.matches.filter((item) => item.type === state.filter);
}

function recordsForEvidence(evidence) {
  if (!evidence?.value) return [];
  const field = evidence.scope === "persian" ? "persianNormalized" : "arabicNormalized";
  return state.corpus.filter((record) => record[field].includes(evidence.value));
}

function evidenceDistribution(verse) {
  return verse.evidence.map((evidence) => {
    const records = recordsForEvidence(evidence);
    return {
      ...evidence,
      count: records.length,
      surahs: new Set(records.map((record) => record.surah)).size,
      references: records.slice(0, 6).map((record) => record.reference),
    };
  });
}

function closeReadingPrompts(verse) {
  const label = verse.evidence[0]?.label || state.query;
  const occurrence = evidenceDistribution(verse).find((item) => item.count)?.count;
  return [
    `«${label}» در جملهٔ این آیه چه چیزی را توصیف می‌کند و چه نشانه‌ای در خودِ عبارت برای آن دارید؟`,
    "رابطهٔ آیه با جمله یا آیهٔ پیش و پس چیست: توضیح، تقابل، نتیجه، نمونه یا موضوعی تازه؟",
    occurrence ? `این صورتِ جست‌وجو در پیکرهٔ فعلی ${faNumber(occurrence)} بار بازیابی شده است؛ پیش از تعمیم، همهٔ مواضع آن را مقایسه کنید.` : "برای سنجش ظرفیت معنایی، مواضع دیگرِ واژه و سیاق هر موضع را جداگانه مقایسه کنید.",
  ];
}

function renderContextStudy() {
  const container = $("#context-study");
  if (state.filter !== "context") {
    container.hidden = true;
    container.innerHTML = "";
    return;
  }
  const verse = state.matches.find((item) => item.id === state.contextVerseId) || state.matches[0];
  if (!verse) {
    container.hidden = true;
    return;
  }
  state.contextVerseId = verse.id;
  const localContext = getContext(verse);
  const distributions = evidenceDistribution(verse);
  const chooser = state.matches.slice(0, Math.max(state.shown, PAGE_SIZE));
  container.hidden = false;
  container.innerHTML = `<section class="context-workspace" aria-labelledby="context-reading-title">
    <div class="context-workspace-head"><div><p class="eyebrow">فهم آیه در سیاق</p><h3 id="context-reading-title">خوانشِ متن‌محورِ ${escapeHTML(verse.reference)}</h3></div><span>${faNumber(verse.surah)}:${faNumber(verse.ayah)} · ${escapeHTML(verse.revelation)}</span></div>
    <p class="reading-notice">این نما «تفسیر خودکار» نیست: دادهٔ دقیقِ بازیابی، پنجرهٔ پیش و پس، و پرسش‌های کنترلِ استنتاج را کنار هم می‌گذارد تا ظرفیت معناییِ آیه در متن آزموده شود.</p>
    ${chooser.length > 1 ? `<div class="context-selector" role="list" aria-label="انتخاب آیه برای خوانش سیاق">${chooser.map((item) => `<button type="button" data-context-study-id="${escapeHTML(item.id)}" class="${item.id === verse.id ? "active" : ""}" role="listitem">${escapeHTML(item.reference)}</button>`).join("")}</div>` : ""}
    <div class="context-window">${localContext.map((item) => `<article class="context-window-verse ${item.id === verse.id ? "current" : ""}"><b>${escapeHTML(item.reference)}${item.id === verse.id ? " · آیهٔ پژوهش" : ""}</b><p lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><small>${escapeHTML(item.persian)}</small></article>`).join("")}</div>
    <div class="semantic-reading-grid">
      <section><h4>شاهدِ بازیابی</h4><ul>${distributions.map((item) => `<li><b>${escapeHTML(item.label)}</b><span>${escapeHTML(item.source || "متن")}</span></li>`).join("")}</ul></section>
      <section><h4>دامنهٔ قابل سنجش در پیکره</h4><ul>${distributions.map((item) => item.count ? `<li><b>${faNumber(item.count)} آیه در ${faNumber(item.surahs)} سوره</b><span>${escapeHTML(item.references.join("، "))}${item.count > item.references.length ? " …" : ""}</span></li>` : `<li><b>${escapeHTML(item.label)}</b><span>این مسیر روایی/پرونده‌ای است؛ آمارِ تطابق واژگانی ندارد.</span></li>`).join("")}</ul></section>
      <section class="reading-questions"><h4>پرسش‌های ظرفیت معنایی</h4><ol>${closeReadingPrompts(verse).map((prompt) => `<li>${escapeHTML(prompt)}</li>`).join("")}</ol></section>
    </div>
  </section>`;
}

function renderResults() {
  const allSurahs = new Set(state.matches.map((item) => item.surah)).size;
  const equivalentCount = state.matches.filter((item) => item.type === "equivalent" || item.type === "exact").length;
  const relatedCount = state.matches.filter((item) => item.type === "related").length;
  const title = state.concept?.title || state.query;
  $("#result-topic").textContent = title;
  $("#result-summary").textContent = !state.terms.length
    ? `این فهرست از مسیر پژوهشیِ «${state.query}» آمده است. برای تفسیر یا پیامِ داستان، آیه‌ها را در پروندهٔ مستقل و منابعِ ارجاع‌دار بررسی کنید.`
    : state.concept
      ? `برای «${title}»، ${faNumber(equivalentCount)} شاهدِ واژگانیِ عربی و ${faNumber(relatedCount)} پیوندِ مرتبط پیدا شد. هر پیوند مرتبط از معادل قرآنی جدا نگه داشته شده است.`
      : `نتایجِ عبارت «${state.query}» فقط بر پایهٔ مسیرِ انتخاب‌شده در جست‌وجو بازیابی شده‌اند.`;
  renderTermGroups();
  renderVerseList();
}

const STUDY_COMMANDS = new Set([
  "اعبدوا", "اتقوا", "انفقوا", "اقيموا", "آتوا", "اذكروا", "اتبعوا", "استغفروا", "توبوا", "اصبروا", "اوفوا", "قولوا", "خذوا", "كلوا", "اشربوا", "انظروا", "اعملوا", "ادعوا", "اسجدوا", "اركعوا", "احسنوا", "اعدلوا", "كونوا", "آمنوا", "امنوا", "استعينوا", "وفوا", "أقيموا", "ءامنوا"
]);

function verseTokens(verse) {
  return (String(verse.arabic || "").match(/[\u0621-\u063a\u0641-\u064a\u0671]+/g) || []).map((raw) => ({ raw, key: normalize(raw) }));
}

function compactSourceText(text = "", maximum = 460) {
  const clean = String(text).replace(/\s+/g, " ").trim();
  if (clean.length <= maximum) return clean;
  const end = Math.max(clean.lastIndexOf(". ", maximum), clean.lastIndexOf("، ", maximum), clean.lastIndexOf("؛ ", maximum));
  const cut = end > maximum * 0.56 ? end + 1 : maximum;
  return `${clean.slice(0, cut).trim()} …`;
}

function primaryTafsirEntry(verse) {
  return tafsirEntries(verse).find((entry) => entry.source.language === "fa") || tafsirEntries(verse)[0] || null;
}

function sourceReference(entry) {
  return `${entry.source.title}، ${entry.source.author}، نسخهٔ ${entry.source.version}${entry.referenceRange ? `، بازهٔ ارجاع ${entry.referenceRange}` : ""}`;
}

function tafsirExcerptItems(verse, maximum = 360) {
  return tafsirEntries(verse).map((entry) => ({
    title: `خوانشِ منبع‌دار: ${entry.source.title}`,
    text: `«${compactSourceText(entry.text, maximum)}»`,
    evidence: sourceReference(entry),
    sourceUrl: entry.source.sourceUrl,
    evidenceKind: "tafsir-quotation",
  }));
}

function verseStructureObservations(verse) {
  const tokens = verseTokens(verse);
  const observations = [];
  const speech = tokens.find(({ key }) => ["قل", "قال", "قالوا", "قالت", "قيل"].includes(key));
  if (speech) observations.push({
    title: "قابِ گفتار در روایت",
    text: `فعلِ «${speech.raw}» در متن، رخدادِ گفتن/گفتار را نشان می‌دهد؛ گوینده و محتوای سخن را باید از ادامهٔ آیه و سیاق تعیین کرد.`,
    evidence: `شاهد عربی: ${speech.raw}`,
    evidenceKind: "discourse-marker",
  });
  const address = tokens.find(({ key }) => key === "یا" || key.startsWith("یاایها"));
  if (address) {
    const start = tokens.indexOf(address);
    const phrase = tokens.slice(start, start + 3).map((item) => item.raw).join(" ");
    observations.push({ title: "مخاطبِ آشکار", text: `آیه خطابِ صریحِ «${phrase}» دارد؛ دامنهٔ مخاطب را باید با همین ترکیب و سیاق خواند.`, evidence: `شاهد عربی: ${phrase}`, evidenceKind: "discourse-marker" });
  }
  const interrogative = tokens.find(({ key }) => ["هل", "كيف", "متى", "أين", "این"].includes(key) || /^ا(?:ت|ف|و|م|ن|ی|ذ|ل|ک|ج)/.test(key));
  if (interrogative) observations.push({ title: "ساختِ پرسشی", text: `نشانگرِ «${interrogative.raw}» پرسش را وارد آیه می‌کند. پرسش می‌تواند کارکردهای گوناگون داشته باشد؛ نوع آن را بدون قرینهٔ سیاقی قطعی نمی‌کنیم.`, evidence: `شاهد عربی: ${interrogative.raw}`, evidenceKind: "discourse-marker" });
  const contrast = tokens.find(({ key }) => ["بل", "لكن", "الا"].includes(key));
  if (contrast) observations.push({ title: "مرزبندی یا تقابل", text: `«${contrast.raw}» مرز یا تقابلی در جمله می‌سازد؛ دو سوی آن باید با هم خوانده شوند.`, evidence: `شاهد عربی: ${contrast.raw}`, evidenceKind: "discourse-marker" });
  return observations;
}

function directCommandItems(verse) {
  const tokens = verseTokens(verse);
  const found = tokens.filter(({ key }) => STUDY_COMMANDS.has(key));
  return [...new Set(found.map(({ raw, key }) => JSON.stringify({ raw, key })))].map((value) => JSON.parse(value)).map(({ raw, key }) => ({
    title: `امرِ صریحِ قابل بررسی: «${raw}»`,
    text: `این صورت با فهرستِ محدودِ فعل‌های امرِ برنامه تطبیق دارد. فقط در صورت تأییدِ صرف، مخاطب و دامنه با سیاق و تفسیر می‌توان آن را به اصلِ زندگی صورت‌بندی کرد؛ خودِ تطبیق به‌تنهایی فتوا یا قاعدهٔ عام نیست.`,
    evidence: `شاهد عربی: ${raw}`,
    evidenceKind: "provisional-imperative",
  }));
}

function studyItems(verse, kind) {
  const observations = verseStructureObservations(verse);
  const sources = tafsirExcerptItems(verse, kind === "notes" ? 420 : 360);
  if (kind === "notes") {
    const items = [...observations, ...sources.slice(0, 5)];
    return items.length ? items : [{
      title: "نیازمند خوانشِ منبع‌دار",
      text: "در این دادهٔ محلی، شاهدِ تفسیریِ فعال یا نشانگرِ ساختاریِ قابل استفاده پیدا نشد؛ بنابراین نکته‌ای فراتر از ترجمه جعل نمی‌شود.",
      evidence: `آیهٔ بررسی‌شده: ${verse.reference}`,
      evidenceKind: "unavailable",
    }];
  }
  if (kind === "messages") {
    // A message is not a translation paraphrase. Show verse-specific discourse cues and exact tafsir readings as candidates.
    const items = [...observations.map((item) => ({ ...item, title: `جهتِ ارتباطیِ قابل بررسی: ${item.title}` })), ...sources.slice(0, 5)];
    return items.length ? items : [{
      title: "پیامِ مستقل احراز نشد",
      text: "از متن و تفسیرهای بارگیری‌شده، پیامِ هدایتیِ مستقلی فراتر از ترجمه احراز نشد؛ برای پرهیز از نسبتِ بی‌شاهد، این بخش خالی می‌ماند.",
      evidence: `آیهٔ بررسی‌شده: ${verse.reference}`,
      evidenceKind: "unavailable",
    }];
  }
  if (kind === "principles") {
    const commands = directCommandItems(verse);
    return commands.length ? commands : [{
      title: "اصلِ زندگیِ مستقیم استخراج نشد",
      text: "در این آیه فعلِ امری از فهرستِ محدودِ برنامه شناسایی نشد. این نتیجه نمی‌گوید آیه فاقد دلالت اخلاقی است؛ فقط اصلِ رفتاریِ بی‌پشتوانه از آن ساخته نمی‌شود.",
      evidence: `بررسی متن عربی و ترجمهٔ ${verse.reference}; بررسی صرفیِ انسانی همچنان لازم است.`,
      evidenceKind: "unavailable",
    }];
  }
  return [];
}

function inlineStudyItems(items, label = "یافته") {
  const verified = items.filter((item) => !item.placeholder);
  const unavailable = items.filter((item) => item.placeholder);
  const list = verified.length ? `<ol class="inline-study-list">${verified.map((item, index) => `<li><b>${escapeHTML(label)} ${faNumber(index + 1)} · ${escapeHTML(item.title)}</b><span>${escapeHTML(item.text)}</span>${item.evidence ? `<small>${escapeHTML(item.evidence)}</small>` : ""}</li>`).join("")}</ol>` : "";
  const notices = unavailable.map((item) => `<aside class="study-unavailable"><b>${escapeHTML(item.title)}</b><p>${escapeHTML(item.text)}</p><small>${escapeHTML(item.evidence || "")}</small></aside>`).join("");
  return `${list}${notices}`;
}

function proposalContent(verse) {
  return `${verse.arabic} ${verse.persian}`;
}

function meaningfulProposalTokens(value) {
  const stop = new Set(["و", "در", "به", "از", "که", "را", "این", "آن", "است", "می", "شود", "برای", "اما", "هم", "من", "ما", "او", "اینکه"]);
  return [...new Set(normalize(value).split(" ").filter((token) => token.length >= 3 && !stop.has(token)))];
}

function validateVerseProposal(verse, claim, witness) {
  const content = proposalContent(verse);
  const cleanClaim = String(claim || "").trim();
  const cleanWitness = String(witness || "").trim();
  if (cleanClaim.length < 18) return { accepted: false, reason: "متن پیشنهاد باید دست‌کم ۱۸ نویسه داشته باشد." };
  if (!cleanWitness || !normalize(content).includes(normalize(cleanWitness))) return { accepted: false, reason: "رد شد: شاهد دقیق در متن همین آیه، ترجمه یا تفسیرهای بارگیری‌شده پیدا نشد." };
  const evidenceTerms = new Set(meaningfulProposalTokens(content));
  const overlap = meaningfulProposalTokens(cleanClaim).filter((token) => evidenceTerms.has(token));
  if (!overlap.length) return { accepted: false, reason: "رد شد: متن پیشنهاد با شاهدهای همین آیه واژهٔ محتواییِ مشترک ندارد." };
  return { accepted: true, overlap };
}

function proposalForm(verse, kind) {
  const labels = { notes: "نکته", messages: "پیام", principles: "اصل زندگی", research: "موضوع پژوهشی" };
  const label = labels[kind];
  const accepted = state.verseProposals.filter((item) => item.verseId === verse.id && item.kind === kind);
  const saved = accepted.map((item, index) => `<article><b>${label} پیشنهادیِ کاربر ${faNumber(index + 1)}</b><p>${escapeHTML(item.claim)}</p><small>شاهد: «${escapeHTML(item.witness)}» · ${item.storage === "server" ? "تأیید و منتشرشده" : "ذخیرۀ محلیِ این مرورگر"}</small>${item.storage === "local" ? `<button type="button" data-delete-proposal="${escapeHTML(item.id)}">حذفِ محلی</button>` : ""}</article>`).join("");
  const claimLabel = kind === "research" ? "موضوع یا پرسش پژوهشی" : "صورت‌بندی";
  const witnessLabel = kind === "research" ? "واژه یا عبارت دقیق از متن/ترجمهٔ همین آیه" : "شاهدِ دقیق از همین آیه";
  return `<section class="proposal-workspace"><h4>پیشنهادِ پژوهشگر: ${label}</h4><p>پیشنهاد پس از بررسیِ شاهد ثبت و تا تأییدِ مدیر منتشر نمی‌شود؛ پیش‌فیلتر، تأییدِ علمی را تضمین نمی‌کند.</p>${saved ? `<div class="user-proposal-list">${saved}</div>` : ""}<form data-proposal-form data-proposal-kind="${kind}" data-proposal-verse-id="${escapeHTML(verse.id)}"><label>${claimLabel}<textarea name="claim" maxlength="1600" required></textarea></label><label>${witnessLabel}<input name="witness" maxlength="600" required></label><button type="submit">ارسال برای بازبینی</button><output class="proposal-status" aria-live="polite"></output></form></section>`;
}

async function submitVerseProposal(form) {
  const verseId = form.dataset.proposalVerseId;
  const verse = state.selected?.id === verseId ? state.selected : state.matches.find((item) => item.id === verseId);
  if (!verse) return;
  const status = form.querySelector(".proposal-status");
  const claim = form.querySelector("[name=claim]")?.value || "";
  const witness = form.querySelector("[name=witness]")?.value || "";
  const result = validateVerseProposal(verse, claim, witness);
  if (!result.accepted) { status.textContent = result.reason; status.dataset.status = "rejected"; return; }
  try {
    const response = await fetch("/api/proposals", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verse_id: verse.id, kind: form.dataset.proposalKind, claim: claim.trim(), witness: witness.trim() }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "ثبتِ پیشنهاد ناموفق بود.");
    status.textContent = payload.message || "پیشنهاد برای بازبینی مدیر ثبت شد.";
    status.dataset.status = "accepted";
    form.reset();
  } catch (error) {
    if (error instanceof TypeError) {
      state.verseProposals.unshift({ id: `local-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`}`, verseId: verse.id, kind: form.dataset.proposalKind, claim: claim.trim(), witness: witness.trim(), storage: "local" });
      persistVerseProposals();
      renderDetailPanel();
      return;
    }
    status.textContent = error.message || "ثبتِ پیشنهاد ناموفق بود.";
    status.dataset.status = "rejected";
  }
}

function deleteVerseProposal(id) {
  state.verseProposals = state.verseProposals.filter((item) => item.id !== id);
  persistVerseProposals();
  if (state.screen === "detail") renderDetailPanel(); else renderVerseList();
}

function renderAdminProposals(items) {
  const host = $("#admin-proposals");
  if (!items.length) { host.innerHTML = '<p class="empty-state">پیشنهادی برای بازبینی نیست.</p>'; return; }
  const labels = { notes: "نکته", messages: "پیام", principles: "اصل زندگی", research: "موضوع پژوهشی" };
  host.innerHTML = items.map((item) => `<article class="admin-proposal" data-admin-proposal-id="${escapeHTML(item.id)}"><header><b>${escapeHTML(item.verse_id)} · ${labels[item.kind] || escapeHTML(item.kind)}</b><small>${escapeHTML(item.status)} · ${escapeHTML(item.submitted_at || "")}</small></header><label>متن<textarea name="claim" maxlength="1600">${escapeHTML(item.claim)}</textarea></label><label>شاهد از همان آیه<input name="witness" maxlength="600" value="${escapeHTML(item.witness)}" /></label><label>وضعیت<select name="status"><option value="pending" ${item.status === "pending" ? "selected" : ""}>در انتظار</option><option value="approved" ${item.status === "approved" ? "selected" : ""}>تأیید و انتشار</option><option value="rejected" ${item.status === "rejected" ? "selected" : ""}>رد</option></select></label><div class="admin-actions"><button type="button" data-admin-save>ذخیرهٔ اصلاح</button><button type="button" class="danger-button" data-admin-delete>حذف</button></div></article>`).join("");
}

async function loadAdminProposals() {
  const token = $("#admin-token").value.trim() || sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
  const status = $("#admin-status");
  if (!token) { status.textContent = "توکن مدیر را وارد کنید."; return; }
  try {
    const response = await fetch("/api/admin/proposals", { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "دسترسی مدیر تأیید نشد.");
    sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
    $("#admin-token").value = token;
    renderAdminProposals(payload.proposals || []);
    status.textContent = `تعداد پیشنهادها: ${faNumber((payload.proposals || []).length)}؛ مواردِ تأییدشده برای کاربران منتشر می‌شوند.`;
  } catch (error) { status.textContent = error.message || "ارتباط با سرور ناموفق بود."; }
}

async function moderateAdminProposal(card, remove = false) {
  const id = card.dataset.adminProposalId;
  const token = sessionStorage.getItem(ADMIN_TOKEN_KEY) || $("#admin-token").value.trim();
  const status = $("#admin-status");
  try {
    const response = await fetch(`/api/admin/proposals/${encodeURIComponent(id)}`, {
      method: remove ? "DELETE" : "PATCH",
      headers: { Authorization: `Bearer ${token}`, ...(remove ? {} : { "Content-Type": "application/json" }) },
      ...(remove ? {} : { body: JSON.stringify({ claim: card.querySelector('[name="claim"]').value, witness: card.querySelector('[name="witness"]').value, status: card.querySelector('[name="status"]').value }) }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "ذخیرۀ تغییرات ناموفق بود.");
    status.textContent = remove ? "پیشنهاد حذف شد." : "اصلاح و وضعیت ذخیره شد.";
    await Promise.all([loadAdminProposals(), refreshPublicProposals()]);
    if (state.screen === "detail") renderDetailPanel(); else renderVerseList();
  } catch (error) { status.textContent = error.message || "ارتباط با سرور ناموفق بود."; }
}

function quranicAnchorTerms(verse, maximum = 8) {
  const stop = new Set(["و", "فی", "في", "من", "عن", "على", "الى", "إلى", "ان", "أن", "ما", "لا", "لم", "لن", "قد", "هو", "هي", "هم", "هن", "هذا", "هذه", "ذلك", "الذي", "التي", "الذين", "كان", "كانت", "قال", "قالوا", "قل"]);
  const seen = new Set();
  return verseTokens(verse).filter(({ key }) => {
    if (key.length < 3 || stop.has(key) || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, maximum);
}

function anchorDistribution(token) {
  const key = token.key;
  const count = state.corpus.reduce((total, record) => total + (record.arabicNormalized.split(" ").includes(key) ? 1 : 0), 0);
  return { token: token.raw, count };
}

function reviewedStudyFor(verse) {
  return state.verseStudies?.[verse.id] || null;
}

function reviewedStudySources(annotation) {
  return (annotation.sources || []).map((id) => state.tafsirSources.find((source) => source.id === id)).filter(Boolean);
}

function reviewedStudyField(verse, field) {
  const annotation = reviewedStudyFor(verse);
  if (!annotation || !annotation[field]) return "";
  const value = annotation[field];
  const sourceLine = reviewedStudySources(annotation).map((source) => `<span>${escapeHTML(source.title)} · ${escapeHTML(source.author)}</span>`).join("");
  if (field === "framework") {
    const cards = [["izutsu", "ایزوتسو: شبکهٔ واژگان و جهان‌بینی"], ["fillmore", "فیلمور: قاب و نقش‌های صحنه"], ["cognitive", "معناشناسی شناختی: طرح‌واره و نگاشت"]];
    return `<p class="reviewed-badge">تحلیلِ تحریریِ آیه · ${escapeHTML(annotation.status)}</p><div class="semantic-model-grid">${cards.map(([key,title]) => { const model=value[key]; return `<section class="semantic-model-card"><h4>${title}</h4><p><b>دادهٔ این آیه:</b> ${escapeHTML(model.input)}</p><p><b>عملیات مدل:</b> ${escapeHTML(model.operation)}</p><p><b>معنا/اثر ارتباطی:</b> ${escapeHTML(model.meaning)}</p><p><b>حدّ استنباط:</b> ${escapeHTML(model.limit)}</p></section>`; }).join("")}</div><div class="reviewed-sources">${sourceLine}</div>`;
  }
  const label = { notes: "نکته", messages: "پیام", principles: "اصلِ زندگی", thematic: "پیوند موضوعی", context: "پیوند سیاقی", network: "پیوند شبکه‌ای" }[field] || "یافته";
  const entries = Array.isArray(value) ? value : [];
  const list = entries.length ? `<ol class="inline-study-list">${entries.map((item,index) => `<li><b>${label} ${faNumber(index+1)}${item.level ? ` · ${escapeHTML(item.level)}` : ""}</b><span>${escapeHTML(item.text || item.relation || "")}</span>${item.evidence ? `<small>شاهد/مبنا: ${escapeHTML(item.evidence)}</small>` : ""}${item.reference ? `<small>آیهٔ پیوندی: ${escapeHTML(item.reference)}</small>` : ""}</li>`).join("")}</ol>` : "";
  return `<p class="reviewed-badge">تحلیلِ تحریریِ آیه · ${escapeHTML(annotation.status)}</p>${list}<div class="reviewed-sources">${sourceLine}</div>`;
}

function inlineStudyBody(verse, tab) {
  const curated = reviewedStudyField(verse, tab);
  if (curated) return curated;
  const distributions = evidenceDistribution(verse);
  const witness = verse.evidence.map((item) => `${item.label} (${item.source})`).join("، ");
  const notes = studyItems(verse, "notes").slice(0, 7);
  const messages = studyItems(verse, "messages").slice(0, 7);
  const principles = studyItems(verse, "principles").slice(0, 20);
  const anchors = quranicAnchorTerms(verse, 6).map(anchorDistribution);
  const panels = {
    notes: `<p class="inline-study-intro">نکته‌ها از ساختِ قابل مشاهده و شرحِ تفسیریِ همین آیه می‌آیند؛ نقلِ مفسر با تحلیلِ پژوهشگر یکی نیست و منبع هر نقل کنار آن آمده است.</p>${inlineStudyItems(notes, "نکته")}${proposalForm(verse, "notes")}`,
    messages: `<p class="inline-study-intro">پیامِ مستقل را فقط وقتی نشان می‌دهیم که جهتِ گفتار یا تفسیرِ منبع‌دار شاهد داشته باشد؛ متنِ مفسر صریحاً به‌عنوان خوانشِ همان منبع برچسب می‌خورد.</p>${inlineStudyItems(messages, "پیام / خوانشِ منبع")}${proposalForm(verse, "messages")}`,
    principles: `<p class="inline-study-intro">اصولِ رفتاری از فهرستِ محدودِ فعل‌های امرِ متن نامزد می‌شوند؛ هر مورد نیازمند کنترلِ صرف، مخاطب، قید و سیاق است. تعدادِ کم بهتر از تعمیمِ بی‌شاهد است.</p>${inlineStudyItems(principles, "اصلِ نیازمندِ بازبینی")}${proposalForm(verse, "principles")}`,
    foundations: `<p class="inline-study-intro">این‌ها واژه‌های لنگر برای آغازِ پژوهش‌اند، نه «مبنای اندیشه»ی اثبات‌شده؛ بسامدِ پیکره هم معنای واژه را به‌تنهایی تعیین نمی‌کند.</p>${inlineStudyItems(anchors.map((item) => ({ title: `واژهٔ لنگر «${item.token}»`, text: `این صورت در ${faNumber(item.count)} آیه از پیکره دیده می‌شود؛ برای تعیینِ نقش مفهومی باید کاربردهای سیاقی و شرح تفاسیر مقایسه شوند.`, evidence: `شاهد عربیِ همین آیه: ${item.token}` })), "واژه")}`,
    framework: `<p class="inline-study-intro">سه مدل پرسش‌های متفاوتی می‌پرسند و از همین آیه شاهد می‌گیرند.</p>${semanticModelCards(verse)}`,
    thematic: detailPanelThematic(verse),
    context: detailPanelContext(verse),
    network: detailPanelNetwork(verse),
  };
  const draftNotice = `<p class="reading-notice draft-study-notice">پیش‌نویسِ متن‌محورِ خودکار؛ هنوز خوانشِ تحریریِ اختصاصیِ این آیه نیست. نقل‌ها و نشانگرها شاهد پژوهش‌اند، نه نتیجهٔ قطعی.</p>`;
  return `${draftNotice}${panels[tab] || panels.notes}`;
}

function inlineStudyContent(verse, tab) {
  return `<div class="inline-study-content" data-inline-study="${escapeHTML(tab)}">${inlineStudyBody(verse, tab)}<button class="inline-open-detail" type="button" data-open-verse="${escapeHTML(verse.id)}">پروندهٔ کامل آیه، سیاق و تفاسیر ←</button></div>`;
}

function verseCard(verse) {
  const primaryEvidence = verse.evidence.slice(0, 2).map((item) => `${item.label} · ${item.source}`).join("، ");
  return `<article class="verse-card" data-verse-id="${escapeHTML(verse.id)}">
    <button class="verse-open" type="button" data-open-verse="${escapeHTML(verse.id)}">
      <span class="verse-head"><span class="verse-reference">${escapeHTML(verse.reference)}</span></span>
      <span class="verse-arabic" lang="ar" dir="rtl">${escapeHTML(verse.arabic)}</span>
      <span class="verse-persian">${escapeHTML(verse.persian)}</span>
      <span class="verse-match"><b>مسیر ورود:</b> ${escapeHTML(primaryEvidence)} <i class="open-cue" aria-hidden="true">←</i></span>
    </button>
  </article>`;
}

function emptyLayerNotice() {
  const topicName = state.concept?.title || state.query;
  if (state.filter === "equivalent") {
    const equivalents = state.terms.filter((term) => term.type === "equivalent");
    const body = equivalents.length
      ? `واژه‌های معادلِ فعال بررسی شدند، اما در پیکرهٔ فعلی برای «${topicName}» شاهدی در این لایه بازنگشت.`
      : `این جست‌وجو با ریشه یا صورتِ عربی آغاز شده است. برای «${topicName}» هنوز معادلِ قرآنیِ بازبینی‌شده‌ای در واژه‌نامهٔ محلی ثبت نشده؛ برنامه به‌جای ساختنِ مترادفِ حدسی، این مرز را آشکار می‌کند.`;
    return `<section class="layer-notice"><p class="eyebrow">لایهٔ معادل قرآنی</p><h3>این لایه بررسی شد؛ شاهدِ مستقلی ندارد.</h3><p>${escapeHTML(body)}</p><p>برای خودِ آیه، «فهم آیه در سیاق» را باز کنید؛ برای گسترش موضوع، از نقشهٔ موضوعات یک مسیر واژگانیِ صریح برگزینید.</p></section>`;
  }
  if (state.filter === "related") {
    const related = state.terms.filter((term) => term.type === "related");
    const body = related.length
      ? `پیوندهای مرتبطِ فعال برای «${topicName}» جست‌وجو شدند، ولی در پیکرهٔ فعلی شاهدی بازنگشت.`
      : `برای «${topicName}» پیوندِ مرتبطِ بازبینی‌شده‌ای فعال نشده است. این نتیجه، خلأ داده را نشان می‌دهد و از افزودنِ ارتباط معناییِ بی‌دلیل جلوگیری می‌کند.`;
    return `<section class="layer-notice"><p class="eyebrow">لایهٔ پیوندهای مرتبط</p><h3>پیوند حدسی جای داده را نگرفته است.</h3><p>${escapeHTML(body)}</p><p>در نقشهٔ موضوعات، موضوع‌های گسترده‌تر با واژه‌های عربیِ آشکار در دسترس‌اند؛ هر پیوند مرتبط در آن‌ها جداگانه برچسب می‌خورد.</p></section>`;
  }
  return `<section class="layer-notice"><p class="eyebrow">نتیجه‌ای در این لایه نیست</p><h3>دامنهٔ جست‌وجو را بررسی کنید.</h3><p>می‌توانید یک صورت عربی، کلیدواژهٔ دقیق یا مسیر موضوعی دیگر وارد کنید.</p></section>`;
}

function renderVerseList() {
  const filtered = resultsByFilter();
  const visible = filtered.slice(0, state.shown);
  const list = $("#verse-list");
  if (!visible.length) {
    list.innerHTML = emptyLayerNotice();
  } else {
    list.innerHTML = visible.map(verseCard).join("");
  }
  $("#result-progress").textContent = `${faNumber(visible.length)} از ${faNumber(filtered.length)} آیه · ${faNumber(new Set(state.matches.map((item) => item.surah)).size)} سوره در نتایج این جست‌وجو`;
  const loadMore = $("#load-more");
  loadMore.hidden = visible.length >= filtered.length;
  if (!loadMore.hidden) loadMore.textContent = `نمایش ${faNumber(Math.min(PAGE_SIZE, filtered.length - visible.length))} آیهٔ بعدی`;
}

function openVerse(id, shouldNavigate = true) {
  const verse = state.matches.find((item) => item.id === id);
  if (!verse) return;
  state.selected = verse;
  state.detailTab = "notes";
  renderDetail();
  if (shouldNavigate) navigate("detail", id);
}

function getContext(verse) {
  return [-1, 0, 1].map((delta) => state.recordById.get(`${verse.surah}:${verse.ayah + delta}`)).filter(Boolean);
}

function evidencePills(evidence) {
  return evidence.map((item) => `<span class="evidence-pill ${item.type === "related" ? "related" : ""}">${escapeHTML(typeLabel(item.type))}: ${escapeHTML(item.label)} · ${escapeHTML(item.source)}</span>`).join("");
}

function renderDetail() {
  const verse = state.selected;
  if (!verse) return;
  $("#detail-reference").textContent = `${verse.reference} · ${verse.revelation}`;
  $("#detail-title").textContent = verse.arabic;
  $("#detail-persian").textContent = verse.persian;
  $("#detail-evidence").innerHTML = evidencePills(verse.evidence);
  updateSaveButton();
  $$("#detail-screen [data-detail-tab]").forEach((button) => {
    const active = button.dataset.detailTab === state.detailTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  renderDetailPanel();
}

function promptsForVerse() {
  return state.concept?.prompts || [
    "فاعل، مخاطب و قیدهای آیه را از خود متن جدا کنید.",
    "پیش از نتیجه‌گیری، آیه‌های پیش و پس را بخوانید.",
  ];
}

function tafsirEntries(verse) {
  return state.tafsirSources.map((source) => {
    const surah = String(verse.surah);
    const ayah = String(verse.ayah);
    const direct = source.verses?.[surah]?.[ayah];
    const contentId = source.ayahMapping?.[surah]?.[ayah];
    const entry = direct || source.contents?.[String(contentId)];
    return entry?.text ? { source, text: entry.text, footnotes: entry.footnotes || "", referenceRange: entry.referenceRange || "" } : null;
  }).filter(Boolean);
}

function tafsirCitation(source) {
  return `${source.title}، ${source.author}، نسخهٔ ${source.version}، ${source.source}`;
}

function sourceEvidenceNotice(verse) {
  const entries = tafsirEntries(verse);
  return entries.length ? `<p class="source-availability">برای این آیه ${faNumber(entries.length)} متن تفسیریِ منبع‌دار موجود است؛ هنگام نتیجه‌گیری، آن‌ها را در تب «منابع تفسیری آیه» با انتساب کامل مقایسه کنید.</p>` : "";
}

function tenMajorTafsirLinks(verse) {
  const collection = state.tafsirCatalog.find((item) => item.id === "ten-major-tafsirs");
  if (!collection?.items?.length) return "";
  const groups = [
    { title: "پنج تفسیر شیعهٔ امامیه", items: collection.items.filter((item) => item.tradition === "شیعهٔ امامیه") },
    { title: "پنج تفسیر اهل‌سنت", items: collection.items.filter((item) => item.tradition === "اهل‌سنت") },
  ];
  return `<section class="tafsir-catalog"><p class="eyebrow">متون کامل در منبع اصلی</p><h3>ده تفسیر جامع منتخب؛ پیوندِ مطالعه برای آیهٔ ${faNumber(verse.surah)}:${faNumber(verse.ayah)}</h3><p class="reading-notice">این پیوندها متنِ میزبانی‌شده را در کتابخانه باز می‌کنند و متن را در قرآن‌پژوهه بازنشر نمی‌کنند. لینک‌های آیه‌محور فقط برای آثاری است که مقصدِ آن آیه بررسی شده؛ در سایر موارد، صفحهٔ آغاز کتاب باز می‌شود و باید از فهرست یا جست‌وجوی کتابخانه استفاده کرد. پیوند به‌تنهایی مجوزِ بازنشر یا استفادهٔ تجاری نیست.</p>${groups.map((group) => `<div class="tafsir-catalog-collection"><h4>${escapeHTML(group.title)}</h4><div class="tafsir-catalog-grid">${group.items.map((item) => {
    const template = String(item.verseUrlTemplate || "");
    const verseUrl = template.replaceAll("{surah}", encodeURIComponent(String(verse.surah))).replaceAll("{ayah}", encodeURIComponent(String(verse.ayah)));
    const safeVerseUrl = /^https?:\/\//i.test(verseUrl) ? verseUrl : "";
    const libraryUrl = /^https?:\/\//i.test(String(item.libraryUrl || "")) ? item.libraryUrl : "";
    return `<article class="tafsir-catalog-card"><h4>${escapeHTML(item.title)}</h4><p>${escapeHTML(item.author)}</p><small>${escapeHTML(item.tradition)} · ${escapeHTML(item.language)} · ${escapeHTML(item.era || "")}</small><span class="catalog-method">${escapeHTML(item.method || "")}</span><b>پیوند بیرونی؛ متن داخل اپ نیست</b>${safeVerseUrl ? `<a class="catalog-source-link" href="${escapeHTML(safeVerseUrl)}" target="_blank" rel="noopener noreferrer">مطالعهٔ آیهٔ ${faNumber(verse.surah)}:${faNumber(verse.ayah)} ↗</a>` : ""}${libraryUrl ? `<a class="catalog-source-link" href="${escapeHTML(libraryUrl)}" target="_blank" rel="noopener noreferrer">مطالعهٔ متن در کتابخانهٔ مدرسهٔ فقاهت ↗</a>` : ""}</article>`;
  }).join("")}</div></div>`).join("")}</section>`;
}

function tafsirCatalogCards() {
  const requested = state.tafsirCatalog.find((collection) => collection.id === "requested-comparative");
  if (!requested?.items?.length) return "";
  return `<section class="tafsir-catalog"><p class="eyebrow">فهرستِ مقایسه‌ایِ درخواستی</p><h3>${escapeHTML(requested.title)}</h3><p class="reading-notice">فهرست، وضعیت واقعی هر متن را نشان می‌دهد؛ متنِ بدون انتساب یا نسخه به آیه نسبت داده نمی‌شود.</p><div class="tafsir-catalog-grid">${requested.items.map((item) => `<article class="tafsir-catalog-card"><h4>${escapeHTML(item.title)}</h4><p>${escapeHTML(item.author)}</p><small>${escapeHTML(item.language)} · ${escapeHTML(item.era || "")}</small><b>${item.status === "available" ? "متن در برنامه موجود است" : item.status === "needs-permission" ? "نیازمند اجازهٔ بازنشر" : "نیازمند نسخهٔ محقق و بازبینی‌شده"}</b><span>${item.status === "available" ? "متن آیه‌به‌آیه در پروندهٔ تفاسیر همین آیه قابل مشاهده است." : "متن این اثر هنوز در برنامه وارد نشده است."}</span><em>${escapeHTML(item.basis)}</em></article>`).join("")}</div></section>`;
}

const MODERN_RESEARCH_LENSES = [
  { terms: ["عدل", "قسط", "ميزان", "حكم", "حق"], title: "عدالت، حقوق و داوری", question: "مفهومِ شاهد را با معیارهای معاصرِ انصاف و رویهٔ عادلانه مقایسه کنید؛ مرز میان معنای تاریخیِ آیه و چارچوب حقوقی امروز را صریح نگه دارید." },
  { terms: ["مال", "ربو", "انفق", "تجر", "كيل", "وزن"], title: "اقتصاد و توزیع منابع", question: "زبانِ مال، مبادله یا بخشش در این آیه چه مسئله‌ای را طرح می‌کند و با کدام داده‌های اقتصادیِ امروز می‌توان آن را فقط به‌عنوان پرسش مقایسه‌ای سنجید؟" },
  { terms: ["ارض", "ماء", "مطر", "نبت", "بحر", "سماء", "زرع"], title: "محیط زیست و منابع طبیعی", question: "عنصر طبیعیِ یادشده در بافت آیه چه نقشی دارد؟ آن را با یک مسئلهٔ محیط‌زیستی امروز مقایسه کنید، بی‌آنکه از آیه ادعای علمیِ پیش‌بینی‌گر بسازید." },
  { terms: ["علم", "عقل", "نظر", "بصر", "سمع", "نبأ", "خبر"], title: "دانش، شواهد و سواد اطلاعاتی", question: "آیه چه نسبتی میان دانستن، مشاهده یا دریافت خبر برقرار می‌کند؟ این پرسش را با معیارهای امروزِ ارزیابی شاهد و اطلاعات مقایسه کنید." },
  { terms: ["قول", "شهد", "كتب", "نبأ", "خبر"], title: "گفتار عمومی و مسئولیت رسانه‌ای", question: "صورتِ گفتار، گواهی یا خبر در آیه چه پیامدی دارد؟ آن را با اخلاق ارتباطات امروز بسنجید، اما حکمی دربارهٔ رسانهٔ جدید را بی‌واسطه به آیه نسبت ندهید." },
  { terms: ["نفس", "قلب", "خوف", "حزن", "امن", "طمأن"], title: "تجربهٔ انسانی و سلامت روان", question: "واژگانِ تجربهٔ درونی در آیه چه چیزی را واقعاً توصیف می‌کنند؟ آن‌ها را با مطالعات روان‌شناختیِ امروز در سطح پرسش مقایسه کنید، نه به‌عنوان تشخیص یا درمان." },
  { terms: ["ناس", "قوم", "أهل", "والد", "زوج", "يتيم", "ضعف"], title: "جامعه، خانواده و گروه‌های آسیب‌پذیر", question: "چه گروه‌ها یا رابطه‌هایی در آیه نام برده می‌شوند و نقش آن‌ها در استدلال چیست؟ با پژوهش اجتماعی امروز مقایسه کنید، بدون تعمیمِ بی‌سیاق." },
];

function detailPanelResearch(verse) {
  const dossier = detailPanelDossier(verse, "research");
  if (dossier) return dossier;
  const annotation = reviewedStudyFor(verse) || {};
  const curated = (annotation.research || []).map((item) => `<li><b>موضوع پژوهشی: ${escapeHTML(item.title)}</b><p>${escapeHTML(item.question)}</p><small>پایهٔ پیشنهادی: ${escapeHTML(item.evidence)}</small></li>`).join("");
  const tokens = [...new Set(verseTokens(verse).filter((token) => token.key.length >= 3).map((token) => JSON.stringify(token)))].map((item) => JSON.parse(item)).slice(0, 4);
  const lexical = tokens.map((token) => {
    const matches = state.corpus.filter((record) => record.arabicNormalized.split(" ").includes(token.key));
    const refs = matches.slice(0, 5).map((record) => record.reference).join("، ");
    return `<li><b>پرسش پیکره‌ای دربارهٔ «${escapeHTML(token.raw)}»</b><p>صورتِ دقیقِ این واژه در پیکره در ${faNumber(matches.length)} آیه دیده می‌شود. آیا با مقایسهٔ سیاقِ مواضع ${escapeHTML(refs || verse.reference)} می‌توان کارکردهای متفاوتش را از هم تفکیک کرد؟ شمارش، ریشه‌یابی صرفی نیست.</p><small>شاهد: متن عربی ${escapeHTML(verse.reference)}؛ جست‌وجوی صورت دقیق در پیکرهٔ محلی.</small></li>`;
  }).join("");
  const thematicItems = (annotation.thematic || []).slice(0, 3).map((item) => `<li><b>مقایسهٔ موضوعی با ${escapeHTML(item.reference || "موضع مرتبط")}</b><p>${escapeHTML(item.relation || "پیوند پیشنهادی در پروندهٔ تحریری")}</p><small>پرسش پژوهشی: این پیوند بر اشتراک واژه، سیاق یا تفسیر استوار است؟ دو موضع را جداگانه بخوانید و نوع شاهد را مشخص کنید.</small></li>`).join("");
  const contextItems = (annotation.context || []).slice(0, 2).map((item) => `<li><b>خوانش سیاقی با ${escapeHTML(item.reference || "آیات پیرامون")}</b><p>${escapeHTML(item.relation || "پیوند سیاقیِ ثبت‌شده")}</p><small>پرسش پژوهشی: تغییر مخاطب، موضوع یا ساختار گفتار در این بازه چه اثری بر خوانش آیه می‌گذارد؟</small></li>`).join("");
  const sources = tafsirEntries(verse);
  const sourceQuestion = sources.length >= 2 ? `<li><b>پژوهش تطبیقی در خوانش مفسران</b><p>${sources.map((entry) => escapeHTML(entry.source.title)).join(" و ")} را در شرح همین آیه کنار هم بگذارید. کدام واژه یا گزاره را برجسته می‌کنند و کجا اختلاف روش دارند؟</p><small>${sources.map((entry) => `${escapeHTML(entry.source.title)}، نسخه ${escapeHTML(entry.source.version)}`).join("؛ ")}</small></li>` : "";
  const keys = new Set(tokens.map((token) => token.key));
  const modern = MODERN_RESEARCH_LENSES.filter((lens) => lens.terms.some((term) => [...keys].some((key) => key.includes(term)))).slice(0, 2).map((lens) => `<li><b>زاویهٔ معاصر: ${escapeHTML(lens.title)}</b><p>${escapeHTML(lens.question)}</p><small>پیوند پیشنهادی فقط از واژهٔ «${escapeHTML(tokens.find((token) => lens.terms.some((term) => token.key.includes(term)))?.raw || "متن آیه")}» آغاز می‌شود؛ این مقایسه ادعای کاربرد قطعی یا پیش‌بینی علمی نیست.</small></li>`).join("");
  const items = [curated, lexical, thematicItems, contextItems, sourceQuestion, modern].filter(Boolean).join("");
  return `<section class="detail-panel research-panel"><p class="eyebrow">کارگاه پرسش‌سازی</p><h3>پژوهش در آیهٔ ${escapeHTML(verse.reference)}</h3><p class="reading-notice">این‌ها سرنخ و طرحِ اولیهٔ پژوهش بر اساس واژهٔ آیه، سیاقِ ثبت‌شده و متن‌های منبع‌دارند؛ پاسخ یا نتیجهٔ قطعی نیستند. برای زاویهٔ معاصر، ابتدا معنای آیه در بافت خودش و سپس حدود قیاس امروز را روشن کنید.</p><ol class="research-question-list">${items || `<li><b>پرسش متن‌محور</b><p>واژه‌های محوریِ همین آیه را در متن عربی، ترجمه، آیات مجاور و شرح‌های منبع‌دار ردیابی کنید؛ هر نتیجه را به شاهد مشخص پیوند دهید.</p></li>`}</ol></section>`;
}

function detailPanelTafsir(verse) {
  const entries = tafsirEntries(verse);
  const catalogue = tafsirCatalogCards();
  const major = tenMajorTafsirLinks(verse);
  const extended = state.tafsirRegistry.filter((source) => source.preload === false).map((source) => {
    const loaded = state.tafsirSources.some((item) => item.id === source.id);
    const loading = state.tafsirLoading === source.id;
    return `<article class="tafsir-choice"><div><b>${escapeHTML(source.title)}</b><small>${escapeHTML(source.author)} · نسخه ${escapeHTML(source.version)}</small></div>${loaded ? `<span class="tafsir-loaded">متن بارگیری‌شده</span>` : `<button type="button" data-load-tafsir="${escapeHTML(source.id)}" ${state.tafsirLoading ? "disabled" : ""}>${loading ? "در حال بارگیری…" : "نمایش متن کامل"}</button>`}</article>`;
  }).join("");
  const loadingNotice = state.tafsirLoading ? `<p class="source-availability" role="status">در حال دریافت و آماده‌سازی متن انتخاب‌شده؛ به‌دلیل حجم منابع، هر بار یک تفسیر تکمیلی بارگیری می‌شود.</p>` : "";
  const errorNotice = state.tafsirLoadFailed ? `<p class="study-unavailable">بارگیری کامل نشد؛ اتصال را بررسی و دوباره روی «نمایش متن کامل» بزنید.</p>` : "";
  // دو منبعِ کوتاهِ پیش‌فرض برای همهٔ آیه‌ها یکسان بارگیری می‌شوند؛ به‌جای تکرارِ پرحجم،
  // فقط در یک بخشِ بسته و با برچسبِ روشن نمایش داده می‌شوند.
  const shorts = entries.filter((entry) => entry.source.preload !== false);
  const shortBody = shorts.map(({ source, text, footnotes }) => `<article class="source-card" lang="${escapeHTML(source.language)}" dir="rtl"><div class="source-card-head"><div><h4>${escapeHTML(source.title)}</h4><p>${escapeHTML(source.author)}</p></div><a href="${escapeHTML(source.sourceUrl)}" target="_blank" rel="noreferrer">نسخه و منبع ↗</a></div><p class="source-citation">${escapeHTML(tafsirCitation(source))}${source.license ? ` · ${escapeHTML(source.license)}` : ""}</p><div class="source-text">${escapeHTML(text)}</div>${footnotes ? `<div class="source-footnotes"><b>پانویسِ منبع</b>${escapeHTML(footnotes)}</div>` : ""}</article>`).join("");
  const shortBlock = shortBody ? `<details class="tafsir-shorts"><summary>متنِ کوتاهِ مرجع (المختصر و المیسر) — برای هر آیه تکرار نمی‌شود</summary><p class="reading-notice">این دو متن، ترجمه و تفسیرِ کوتاهِ مرجع‌اند و خوانشِ تحریریِ همین اپ شمرده نمی‌شوند؛ خوانشِ کهن و معاصرِ هر آیه در فیلدهای «خوانش‌های کهن» و «مطالعات معاصر» آمده است.</p>${shortBody}</details>` : "";
  const curated = detailPanelDossier(verse, "classical");
  return `${curated}<section class="detail-panel tafsir-panel"><p class="eyebrow">منابع تفسیریِ آیه</p><h3>متنِ کامل، انتساب، نسخه و پیوندِ دقیق</h3><p class="reading-notice">متن‌ها بدون خلاصه‌سازی یا بازنویسی نمایش داده می‌شوند. منابع عربی و فارسی دیدگاه‌های متفاوت دارند؛ نقلِ یک مفسر را با نظر دیگران یکی نگیرید.</p>${loadingNotice}${errorNotice}<div class="tafsir-choices"><h4>تفاسیر تکمیلی: طبری، قرطبی و المیزان</h4>${extended}</div>${major}${catalogue}${shortBlock}</section>`;
}

const DOSSIER_FIELDS = {
  notes: { label: "نکته", title: "نکات مهم آیه", eyebrow: "نکات آیه · خوانشِ تحریری" },
  context: { label: "قرینهٔ سیاقی", title: "سیاق و جایگاه", eyebrow: "سیاق · درونِ سوره و مصحف" },
  classical: { label: "خوانش کهن", title: "خوانش‌های کهن", eyebrow: "تفسیرِ کهن · گزارش و استدلال" },
  modern: { label: "پژوهش معاصر", title: "مطالعات معاصر", eyebrow: "مطالعات قرآنی و تفسیریِ معاصر" },
  critical: { label: "پرسش انتقادی", title: "خوانش انتقادی", eyebrow: "خوانش انتقادی · سنجشِ پیش‌فرض و مرز" },
  research: { label: "پرسش پژوهشی", title: "پژوهش در آیه", eyebrow: "پرسش‌های پژوهشیِ تازه" },
};

function dossierFor(verse) {
  return (state.verseDossiers && state.verseDossiers[verse.id]) || null;
}

function dossierItems(verse, field) {
  const dossier = dossierFor(verse);
  const items = dossier && Array.isArray(dossier[field]) ? dossier[field] : [];
  if (!items.length) return "";
  const meta = DOSSIER_FIELDS[field] || { label: "بند" };
  return `<ol class="dossier-list">${items.map((item, index) => `<li class="dossier-item"><b>${escapeHTML(meta.label)} ${faNumber(index + 1)}</b><span>${scholarCite(item.text)}</span><small>${scholarCite(item.cite || "")}</small></li>`).join("")}</ol>`;
}

function dossierCoverage() {
  const written = Object.keys(state.verseDossiers || {}).length;
  const total = (state.corpus && state.corpus.length) || 6236;
  const batches = (state.verseDossierMeta && state.verseDossierMeta.batches) || [];
  const current = batches[batches.length - 1];
  const scope = current ? ` · آخرین بسته: ${escapeHTML(current.range)}` : "";
  const fresh = Object.values(state.verseDossiers || {}).filter((entry) => (entry.notes || []).length >= 4 && (entry.modern || []).length >= 4 && (entry.research || []).length >= 4).length;
  const standard = fresh ? ` از این میان، ${faNumber(fresh)} آیه در استانداردِ تازه (۴–۵ نکته، ۴–۵ مطالعهٔ معاصر، ۴–۵ پرسش) نوشته شده‌اند` : "";
  return `<p class="dossier-progress"><b>پیشرفتِ پرونده</b> ${faNumber(written)} آیه از ${faNumber(total)} آیه خوانشِ تحریریِ شش‌فیلدی دارند؛${standard} بقیه با لنگرهای پژوهشی و برچسبِ پیش‌نویس نمایش داده می‌شوند${scope}.</p>`;
}

function dossierMethodNote() {
  const meta = state.verseDossierMeta;
  const progress = dossierCoverage();
  if (!meta || !meta.method) return progress;
  return `<details class="dossier-method"><summary>روشِ این خوانش و قاعدهٔ ارجاع</summary><p>${escapeHTML(meta.method)}</p>${progress}</details>`;
}

function detailPanelDossier(verse, field) {
  const meta = DOSSIER_FIELDS[field];
  const items = dossierItems(verse, field);
  if (!items) return "";
  const dossier = dossierFor(verse);
  return `<section class="detail-panel dossier-panel"><p class="eyebrow">${escapeHTML(meta.eyebrow)}</p><h3>${escapeHTML((dossier && dossier.title) || meta.title)}${dossier && dossier.standard === 2 ? `<span class="standard-badge">استانداردِ تازه · ۴–۵ نکته · ۴–۵ مطالعهٔ معاصر · ۴ کاربست</span>` : ""}</h3>${items}${dossierMethodNote()}</section>`;
}

function dossierAnchors(verse, kind) {
  if (!state.scholarAnchorById) return [];
  const ids = (state.scholarLayer && state.scholarLayer[verse.id]) || [];
  return ids.map((id) => state.scholarAnchorById.get(id)).filter((anchor) => anchor && anchor.kind === kind);
}

function detailPanelModern(verse) {
  const curated = detailPanelDossier(verse, "modern");
  if (curated) return curated;
  const anchors = dossierAnchors(verse, "معاصر");
  const items = anchors.map((anchor) => `<li class="dossier-item"><b>${escapeHTML(anchor.field)}</b><span>${scholarCite(anchor.claim)}</span><small>${scholarCite(anchor.cite)}</small></li>`).join("");
  return `<section class="detail-panel dossier-panel"><p class="eyebrow">مطالعات قرآنی و تفسیریِ معاصر</p><h3>مسیرِ پژوهشِ امروز برای این آیه</h3><p class="reading-notice draft-study-notice">برای این آیه هنوز خوانشِ تحریریِ معاصر نوشته نشده است. به‌جای متنِ ساختگی، پژوهش‌های معاصرِ هم‌موضوع و مرزِ استنباطشان نشان داده می‌شود؛ این بندها جانشینِ خوانشِ همین آیه نیستند.</p>${items ? `<ol class="dossier-list">${items}</ol>` : `<p class="dossier-empty">در بانکِ پژوهش، لنگرِ معاصری برای این آیه ثبت نشده است؛ نوشتنِ خوانشِ معاصر باید از پیکره و منابعِ داوری‌شده آغاز شود.</p>`}${dossierCoverage()}</section>`;
}

function detailPanelCritical(verse) {
  const curated = detailPanelDossier(verse, "critical");
  if (curated) return curated;
  const anchors = [...dossierAnchors(verse, "معاصر"), ...dossierAnchors(verse, "کهن")].slice(0, 3);
  const items = anchors.map((anchor) => `<li class="dossier-item"><b>${escapeHTML(anchor.field)} · ${escapeHTML(anchor.kind)}</b><span>${scholarCite(anchor.limit)}</span><small>${scholarCite(anchor.cite)} · پرسشِ باز: ${scholarCite(anchor.question)}</small></li>`).join("");
  return `<section class="detail-panel dossier-panel"><p class="eyebrow">خوانش انتقادی · سنجشِ پیش‌فرض و مرز</p><h3>چه چیزی را می‌توان نقد کرد و چه چیزی را نه</h3><p class="reading-notice draft-study-notice">برای این آیه خوانشِ انتقادیِ تحریری نوشته نشده است. آنچه می‌بینید مرزِ استنباطِ لنگرهای پژوهشی است، نه نقدِ نهایی؛ خوانشِ انتقادی پیش از هر چیز پیش‌فرض‌ها و تبارِ تطبیق‌ها را می‌سنجد.</p>${items ? `<ol class="dossier-list">${items}</ol>` : `<p class="dossier-empty">لنگرِ پژوهشیِ ثبت‌شده‌ای برای سنجشِ انتقادیِ این آیه در بانک نیست.</p>`}${dossierCoverage()}</section>`;
}

function detailPanelNotes(verse) {
  const curated = detailPanelDossier(verse, "notes");
  if (curated) return curated;
  return `<section class="detail-panel"><p class="eyebrow">نکات آیه ـ دادهٔ قابل بازبینی</p><h3>متن، نکته‌های قابل پیگیری و شاهدِ منبع‌دار</h3>
    <p class="reading-notice">«صورتِ بازیابی» با «معنای نهایی» یکی نیست. نخست نکته‌های متن‌محور و نقلِ آیه را ببینید؛ سپس دادهٔ دقیقِ بازیابی و مرزِ استنتاج را کنترل کنید.</p>
    ${inlineStudyBody(verse, "notes")}
</section>`;
}

function detailPanelFoundations(verse) {
  return `<section class="detail-panel"><p class="eyebrow">اصول و مبانیِ خواندن آیه</p><h3>اصلِ زندگی و مبنای اندیشه را با شاهد بخوانید.</h3>
    ${sourceEvidenceNotice(verse)}
    ${inlineStudyBody(verse, "principles")}
    ${inlineStudyBody(verse, "foundations")}
</section>`;
}

function semanticModelCards(verse) {
  const anchors = quranicAnchorTerms(verse, 6).map(anchorDistribution);
  const tokens = verseTokens(verse);
  const cues = verseStructureObservations(verse);
  const frameCue = cues.find((item) => item.title.includes("گفتار") || item.title.includes("پرسش") || item.title.includes("مخاطب"));
  const schemaLexicon = [
    { title: "مسیر/حرکت", terms: ["صراط", "سبيل", "سبیل", "هدى", "هدی", "جاء", "ذهب", "رجع"] },
    { title: "ظرف/درون", terms: ["في", "قلب", "صدر", "قلوب", "صدور"] },
    { title: "نور/تاریکی", terms: ["نور", "ظلمات", "ظلمة"] },
    { title: "سنجش/تراز", terms: ["ميزان", "میزان", "وزن", "قسط"] },
    { title: "بالا/پایین", terms: ["فوق", "تحت", "رفع", "نزل", "سماء", "ارض"] },
    { title: "دادوستد", terms: ["اشترى", "اشتری", "باع", "تجارة", "تجاره", "ربح", "خسر"] },
  ].map((schema) => ({ ...schema, hits: tokens.filter((token) => schema.terms.some((term) => normalize(term) === token.key || token.key.includes(normalize(term)) )).map((token) => token.raw) })).filter((schema) => schema.hits.length);
  const izutsu = anchors.length ? `<ul>${anchors.map((item) => `<li><b>واژهٔ لنگر:</b> «${escapeHTML(item.token)}»؛ در ${faNumber(item.count)} آیه دیده شده است. <b>هم‌نشین‌های این موضع:</b> ${escapeHTML(anchors.filter((other) => other.token !== item.token).map((other) => other.token).join("، ") || "واژهٔ لنگرِ دیگری شناسایی نشد")}</li>`).join("")}</ul><p><b>عملیات مدل:</b> سنجشِ هم‌نشینی، تقابل و توزیعِ واژه‌ها؛ شمارش به‌تنهایی معنای نهایی نمی‌سازد.</p>` : `<p>واژهٔ محتواییِ قابل اتکا برای این تحلیلِ سطحی پیدا نشد؛ میدان معنایی ساخته نمی‌شود.</p>`;
  const fillmore = `<ul><li><b>قابِ زبانیِ قابل مشاهده:</b> ${escapeHTML(frameCue?.title || "گزارش/توصیفِ جمله؛ قابِ رویدادیِ قطعی از این لایه استخراج نشد")}</li><li><b>شاهد:</b> ${escapeHTML(frameCue?.evidence || "نشانگرِ روشنِ گفتار یا خطاب در این بررسی سطحی ثبت نشد")}</li><li><b>پرسش نقش‌ها:</b> فاعل، کنش، مخاطب و موضوعِ گفتار باید از نحو و سیاق تعیین شوند؛ در این نسخه نقشِ حذف‌شده حدس زده نمی‌شود.</li></ul><p><b>عملیات مدل:</b> بازسازی قاب/صحنه و نقش‌های معنایی فقط تا جایی که ساختِ متن آشکار می‌کند.</p>`;
  const cognitive = schemaLexicon.length ? `<ul>${schemaLexicon.map((item) => `<li><b>${escapeHTML(item.title)}:</b> محرک‌های لفظیِ همین آیه: ${escapeHTML([...new Set(item.hits)].join("، "))}.</li>`).join("")}</ul><p>وجودِ محرک فقط امکانِ بررسیِ طرح‌واره را می‌دهد؛ استعاره یا معنای اعتقادیِ نهایی را به‌تنهایی ثابت نمی‌کند.</p>` : `<p>در واژه‌های قابل شناساییِ این آیه، محرکِ لفظیِ طرح‌واره‌های فعالِ این واژه‌نامه پیدا نشد؛ از تصویرسازیِ بی‌شاهد خودداری می‌شود.</p>`;
  return `<div class="semantic-model-grid"><section class="semantic-model-card"><h4>ایزوتسو: شبکهٔ واژگان و جهان‌بینی</h4><p><b>پرسش مدل:</b> واژه‌های کانونی در این آیه با چه مفاهیم و تقابل‌هایی رابطه دارند؟</p>${izutsu}<p><b>حدّ نتیجه:</b> هم‌نشینی و بسامد، دادهٔ اکتشافی‌اند؛ برای تفسیر باید کاربردهای دیگر و شواهد تفسیری مقایسه شوند.</p></section><section class="semantic-model-card"><h4>فیلمور: قاب و نقش‌های صحنه</h4><p><b>پرسش مدل:</b> چه صحنه‌ای فعال است و چه کسی چه کنشی را نسبت به چه کسی/چیزی انجام می‌دهد؟</p>${fillmore}<p><b>حدّ نتیجه:</b> نقشِ نحوی و نقشِ معنایی همیشه یکی نیست؛ تحلیل نحویِ دقیق‌تر ممکن است لازم باشد.</p></section><section class="semantic-model-card"><h4>معناشناسی شناختی: طرح‌واره و نگاشت</h4><p><b>پرسش مدل:</b> کدام تجربهٔ مکانی/بدنی در صورت‌بندیِ مفهوم فعال شده است؟</p>${cognitive}<p><b>حدّ نتیجه:</b> نبودِ محرک، طرح‌واره را رد نمی‌کند؛ وجودِ واژه هم نگاشت استعاری را به‌تنهایی اثبات نمی‌کند.</p></section></div>`;
}

function detailPanelFramework(verse) {
  const curated = reviewedStudyField(verse, "framework");
  if (curated) return `<section class="detail-panel"><p class="eyebrow">چارچوب معنایی</p><h3>سه مدل، سه خوانشِ ویژهٔ همین آیه</h3>${curated}</section>`;
  return `<section class="detail-panel"><p class="eyebrow">چارچوب معنایی</p><h3>سه مدل، سه پرسشِ متفاوت از همین آیه</h3><p class="reading-notice draft-study-notice">پیش‌نویسِ الگوریتمیِ این آیه؛ هنوز خوانشِ تحریریِ اختصاصی نیست. هر کارت شاهد، عملیات مدل و حدّ استنباط را جدا می‌کند.</p>${semanticModelCards(verse)}</section>`;
}

function detailPanelMessages(verse) {
  const prompts = [...promptsForVerse(), ...closeReadingPrompts(verse)].filter((item, index, items) => items.indexOf(item) === index);
  return `<section class="detail-panel"><p class="eyebrow">پیام‌های آیه</p><h3>پیامِ متن‌محور را با سیاق و منبع بسنجید.</h3>
    ${sourceEvidenceNotice(verse)}
    ${inlineStudyBody(verse, "messages")}
    <p class="reading-notice">پرسش‌های زیر برای تکمیلِ خوانش‌اند، نه جایگزینِ پیام‌های مستندِ بالا. هر پاسخ تفسیری باید به متن، سیاق و منبعِ دقیق تکیه کند.</p>
    <ul class="study-list">${prompts.map((prompt, index) => `<li><b>پرسش ${faNumber(index + 1)}</b>${escapeHTML(prompt)}</li>`).join("")}<li><b>ثبت نتیجهٔ موقت</b>اگر پاسخی یافتید، دلیلِ لفظی، آیه‌های مقایسه‌ای و مأخذ تفسیری را در «یادداشت من» همراه با جلد و صفحه ثبت کنید.</li></ul></section>`;
}

function thematicRelatedVerses(verse) {
  const keys = new Set(verse.evidence.map((item) => `${item.scope || ""}:${item.value || item.label}`));
  return state.matches.filter((item) => item.id !== verse.id && item.evidence.some((evidence) => keys.has(`${evidence.scope || ""}:${evidence.value || evidence.label}`)))
    .sort((a, b) => a.surah - b.surah || a.ayah - b.ayah).slice(0, 8);
}

function detailPanelThematic(verse) {
  const curated = reviewedStudyField(verse, "thematic");
  if (curated) return `<section class="detail-panel thematic-panel"><p class="eyebrow">تفسیر موضوعی</p><h3>پیوندهای موضوعیِ تحریریِ این آیه</h3>${curated}</section>`;
  const relatedVerses = thematicRelatedVerses(verse);
  const citations = [verse, ...relatedVerses.slice(0, 3)].map((item) => {
    const entry = primaryTafsirEntry(item);
    return entry ? `<article class="thematic-source"><h4>${escapeHTML(item.reference)} · ${escapeHTML(entry.source.title)}</h4><blockquote>${escapeHTML(compactSourceText(entry.text, 360))}</blockquote><small>${escapeHTML(tafsirCitation(entry.source))}</small></article>` : "";
  }).filter(Boolean);
  return `<section class="detail-panel thematic-panel"><p class="eyebrow">تفسیر موضوعی · مقایسهٔ شواهد</p><h3>آیاتِ هم‌شاهد و شرح‌های منبع‌دار</h3><p class="reading-notice">این پنل تفسیرِ جامعِ خودکار نمی‌سازد؛ آیات را بر اساس شاهدِ جست‌وجوی مشترک کنار هم می‌چیند و نقلِ مفسر را عیناً با انتساب نشان می‌دهد. اشتراکِ واژه به‌تنهایی وحدتِ معنا را ثابت نمی‌کند.</p><p><b>شاهدِ ورود این آیه:</b> ${escapeHTML(verse.evidence.map((item) => item.label).join("، "))}</p>${relatedVerses.length ? `<h4>آیات دیگر با همان شاهد</h4><div class="related-verses">${relatedVerses.map((item) => `<button class="related-verse" type="button" data-related-id="${escapeHTML(item.id)}">${escapeHTML(item.reference)} · ${escapeHTML(item.evidence.filter((e) => verse.evidence.some((v) => v.value === e.value && v.scope === e.scope)).map((e) => e.label).join("، "))}</button>`).join("")}</div>` : `<p>در فهرست نتایجِ فعلی آیهٔ دیگری با شاهدِ مشترک نیست؛ این به معنای نبودِ پیوند موضوعی در قرآن نیست.</p>`}${citations.length ? `<h4>خوانشِ تفسیریِ قابل مقایسه</h4><div class="thematic-source-list">${citations.join("")}</div>` : `<p class="study-unavailable">شرح تفسیریِ فعال برای این مواضع در دسترس نیست.</p>`}</section>`;
}

function detailPanelNetwork(verse) {
  const curated = reviewedStudyField(verse, "network");
  if (curated) return `<section class="detail-panel network-panel"><p class="eyebrow">نظم شبکه‌ای</p><h3>گره‌ها و روابطِ مستندِ این آیه</h3>${curated}</section>`;
  const connected = thematicRelatedVerses(verse);
  const local = getContext(verse).filter((item) => item.id !== verse.id);
  const sameSurah = connected.filter((item) => item.surah === verse.surah);
  const otherSurahs = connected.filter((item) => item.surah !== verse.surah);
  const links = (items) => items.length ? `<ul>${items.map((item) => `<li><button class="related-verse" type="button" data-related-id="${escapeHTML(item.id)}">${escapeHTML(item.reference)} · ${escapeHTML(item.evidence[0]?.label || "شاهد")}</button></li>`).join("")}</ul>` : `<p>در نتایج فعلی پیوندی ثبت نشده است.</p>`;
  return `<section class="detail-panel network-panel"><p class="eyebrow">نظم شبکه‌ای · روابطِ داده‌پذیر</p><h3>از واژه و سیاق به مواضعِ دیگر</h3><p class="reading-notice">روابط در این صفحه تعریف عملیاتی دارند: تطابقِ شاهدِ جست‌وجو، هم‌جواری در همان سوره، و پیوندِ واژه‌نامه‌ای. این‌ها به‌تنهایی رابطهٔ علّی، بلاغی یا تفسیرِ نهایی را ثابت نمی‌کنند.</p><div class="network-grid"><section><h4>گرهٔ واژگانیِ جست‌وجو</h4><ul>${verse.evidence.map((item) => `<li><b>${escapeHTML(item.label)}</b> · ${escapeHTML(item.source || "متن")}${item.type === "related" ? " · پیوند مرتبط، نه معادل قطعی" : ""}</li>`).join("")}</ul></section><section><h4>گره‌های سیاقیِ مجاور</h4>${local.length ? `<ul>${local.map((item) => `<li><b>${escapeHTML(item.reference)}</b><span>${escapeHTML(compactSourceText(item.persian, 150))}</span></li>`).join("")}</ul>` : `<p>آیهٔ مجاور در پیکره موجود نیست.</p>`}</section><section><h4>هم‌شاهد در همین سوره</h4>${links(sameSurah)}</section><section><h4>هم‌شاهد در سوره‌های دیگر</h4>${links(otherSurahs)}</section></div><p class="study-capacity">این شبکه فقط پیوندهای قابل ردیابیِ دادهٔ فعلی را نشان می‌دهد؛ نظمِ بلاغیِ کلان باید با مطالعهٔ سوره و منابع اثبات شود.</p></section>`;
}

function detailPanelContext(verse) {
  const dossier = detailPanelDossier(verse, "context");
  if (dossier) {
    const window = getContext(verse);
    const strip = window.length ? `<section class="detail-panel context-strip"><p class="eyebrow">همسایگیِ متن</p><h3>آیه در پنجرهٔ پیش و پس</h3><div class="context-grid">${window.map((item) => `<article class="context-verse ${item.id === verse.id ? "current" : ""}"><b>${escapeHTML(item.reference)}${item.id === verse.id ? " · آیهٔ پژوهش" : ""}</b><p class="context-arabic" lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><p>${escapeHTML(item.persian)}</p></article>`).join("")}</div></section>` : "";
    return dossier + strip;
  }
  const curated = reviewedStudyField(verse, "context");
  if (curated) return `<section class="detail-panel"><p class="eyebrow">سیاق آیات</p><h3>پیش، خود و پسِ آیه در خوانش تحریری</h3>${curated}<div class="context-grid">${getContext(verse).map((item) => `<article class="context-verse ${item.id === verse.id ? "current" : ""}"><b>${escapeHTML(item.reference)}</b><p class="context-arabic" lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><p>${escapeHTML(item.persian)}</p></article>`).join("")}</div></section>`;
  const context = getContext(verse);
  return `<section class="detail-panel"><p class="eyebrow">آیه در سیاق سوره</p><h3>پیش و پسِ آیه را کنار هم بخوانید.</h3>${sourceEvidenceNotice(verse)}<p>پنجرهٔ خطیِ زیر جای مطالعهٔ کامل سوره را نمی‌گیرد، اما دادهٔ لازم برای پرهیز از بریده‌خوانی را نشان می‌دهد. برای جزئیاتِ توزیع و پرسش‌ها، «فهم آیه در سیاق» در صفحهٔ پیشین را باز کنید.</p>
    <div class="context-grid">${context.map((item) => `<button class="context-verse ${item.id === verse.id ? "current" : ""}" data-context-id="${escapeHTML(item.id)}" type="button"><b>${escapeHTML(item.reference)}${item.id === verse.id ? " · آیهٔ پژوهش" : ""}</b><p class="context-arabic" lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><p>${escapeHTML(item.persian)}</p></button>`).join("")}</div></section>`;
}

function detailPanelQuran(verse) {
  const sameSurah = state.matches.filter((item) => item.surah === verse.surah && item.id !== verse.id).slice(0, 5);
  return `<section class="detail-panel"><p class="eyebrow">آیه در نسبت با کل قرآن</p><h3>جای این آیه در مسیرِ همین پژوهش</h3>
    ${sourceEvidenceNotice(verse)}
    ${sameSurah.length ? `<div class="related-verses">${sameSurah.map((item) => `<button class="related-verse" type="button" data-related-id="${escapeHTML(item.id)}">${escapeHTML(item.reference)} · ${escapeHTML(item.evidence[0]?.label || "شاهد")}</button>`).join("")}</div>` : "<p>در مسیر فعلی، شاهدِ دیگری از همین سوره بازیابی نشده است.</p>"}</section>`;
}

function detailPanelNotebook(verse) {
  const saved = state.notebook.find((item) => item.id === verse.id);
  return `<section class="detail-panel"><p class="eyebrow">دفتر پژوهش، فقط روی همین دستگاه</p><h3>یادداشت و منبع خود را ثبت کنید.</h3><p>برای تفسیر یا منبع بیرونی، نام اثر، مؤلف، جلد و صفحه را دقیق بنویسید.</p>
    <textarea id="verse-note" class="note-area" placeholder="برداشت موقت، پرسش، یا ارجاع منبع…">${escapeHTML(saved?.note || "")}</textarea>
    <div class="note-actions"><button id="save-note" type="button">ذخیرهٔ یادداشت</button><span id="note-status"></span></div></section>`;
}

function fieldNotePanel(verse, field) {
  const labels = { notes: "نکات مهم آیه", foundations: "اصول زندگی و مبانی", framework: "چارچوب معنایی", messages: "پیام‌های آیه", context: "سیاق و جایگاه", thematic: "تفسیر موضوعی", network: "نظم شبکه‌ای", quran: "نسبت با قرآن", tafsir: "منابع تفسیری آیه", modern: "مطالعات معاصر", critical: "خوانش انتقادی", research: "پژوهش در آیه", application: "کاربست امروز" };
  const key = `${verse.id}:${field}`;
  const inputId = `field-note-${field}`;
  const proposalKind = field === "research" ? "research" : field === "messages" ? "messages" : field === "foundations" ? "principles" : "notes";
  return `<section class="field-note-panel"><label for="${inputId}"><b>یادداشت من</b><span>یادداشت شخصی برای بخش «${escapeHTML(labels[field] || field)}»</span></label><textarea id="${inputId}" class="note-area" data-field-note="${escapeHTML(field)}" data-verse-id="${escapeHTML(verse.id)}" maxlength="3000" placeholder="پرسش، برداشت شخصی یا ارجاعی که می‌خواهید برای این بخش نگه دارید…">${escapeHTML(state.fieldNotes[key] || "")}</textarea><small class="field-note-status" aria-live="polite">ذخیرهٔ خودکار فقط در همین دستگاه</small><details class="field-proposal"><summary>پیشنهاد من برای همین بخش</summary><p class="field-proposal-hint">پیشنهاد شما با شاهدِ همین آیه ثبت می‌شود و پس از بازبینی، مبنای به‌روزرسانیِ همین بخش قرار می‌گیرد.</p>${proposalForm(verse, proposalKind)}</details></section>`;
}

const SCHOLAR_SLICES = {
  notes: ["finding", "witness"],
  messages: ["finding", "classical"],
  principles: ["critique", "classical"],
  foundations: ["witness", "modern"],
  framework: ["modern", "critique"],
  context: ["witness", "classical"],
  network: ["modern", "question"],
  quran: ["finding", "modern"],
  tafsir: ["classical", "critique"],
  research: ["question", "critique", "modern"],
  modern: [],
  critical: [],
  application: [],
};

const SCHOLAR_LABEL = {
  finding: "یافته",
  witness: "شاهدِ متنی",
  classical: "خوانش کهن",
  modern: "پژوهش معاصر",
  critique: "خوانش انتقادی و مرزِ استنباط",
  question: "پرسش پژوهشیِ تازه",
};

function scholarCite(text) {
  return escapeHTML(text).replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function scholarBlock(verse, field) {
  if (!state.scholarAnchorById) return "";
  const pilot = state.scholarPilotData ? state.scholarPilotData[verse.id] : null;
  const ids = (state.scholarLayer && state.scholarLayer[verse.id]) || [];
  const anchors = ids.map((id) => state.scholarAnchorById.get(id)).filter(Boolean);
  if (!pilot && !anchors.length) return "";

  const rows = [];
  if (pilot) {
    for (const key of SCHOLAR_SLICES[field] || ["finding"]) {
      if (pilot[key]) {
        rows.push(`<li><b>${SCHOLAR_LABEL[key]}</b><span>${scholarCite(pilot[key])}</span></li>`);
      }
    }
    if (["context", "tafsir", "notes"].includes(field) && pilot.witness) {
      // شاهدِ متنی در این سه بخش تکرار نمی‌شود اگر پیش‌تر آمده باشد
    }
  } else {
    const wantCritique = ["principles", "research", "framework", "tafsir"].includes(field);
    const wantQuestion = ["research", "network"].includes(field);
    anchors.slice(0, 3).forEach((anchor) => {
      const kind = anchor.kind === "کهن" ? "خوانش کهن" : "پژوهش معاصر";
      rows.push(`<li><b>${kind} · ${escapeHTML(anchor.field)}</b><span>${scholarCite(anchor.claim)}</span><small>${scholarCite(anchor.cite)}</small></li>`);
      if (wantCritique) {
        rows.push(`<li><b>${SCHOLAR_LABEL.critique}</b><span>${scholarCite(anchor.limit)}</span></li>`);
      }
      if (wantQuestion) {
        rows.push(`<li><b>${SCHOLAR_LABEL.question}</b><span>${scholarCite(anchor.question)}</span></li>`);
      }
    });
  }

  const badge = pilot ? "بازبینی‌شده" : "پیش‌نویسِ تحلیلی";
  const note = pilot
    ? "این بخش با خوانشِ اختصاصیِ همین آیه نوشته شده و هر بندش شاهد یا منبع دارد."
    : "این بندها از بانکِ منابعِ کهن و پژوهش‌های داوری‌شده برگرفته شده‌اند و برای همین آیه انتخاب شده‌اند؛ ابزارِ سنجشِ خوانش‌اند، نه تفسیرِ نهایی.";
  return `<section class="scholar-layer"><p class="eyebrow">لایهٔ پژوهشی <span class="scholar-badge ${pilot ? "reviewed" : "draft"}">${badge}</span></p><ul class="scholar-list">${rows.join("")}</ul><p class="scholar-note">${note}</p></section>`;
}

function orderedApplicationIds() {
  return Object.keys(state.scholarApplication || {}).sort((a, b) => {
    const [s1, a1] = a.split(":").map(Number);
    const [s2, a2] = b.split(":").map(Number);
    return s1 - s2 || a1 - a2;
  });
}

function batchForVerse(id) {
  const meta = state.scholarApplicationMeta;
  if (!meta || !meta.batches.length) return null;
  const index = orderedApplicationIds().indexOf(id);
  if (index < 0) return null;
  let edge = 0;
  for (const batch of meta.batches) {
    edge += batch.count || 0;
    if (index < edge) return batch;
  }
  return meta.batches[meta.batches.length - 1];
}

function applicationPanel(verse) {
  const meta = state.scholarApplicationMeta;
  const entry = state.scholarApplication ? state.scholarApplication[verse.id] : null;
  const head = `<p class="eyebrow">کاربست امروز · استنباط، نه متن</p><h3>از متن به میدان، با مرزِ روشن</h3>
    <p class="reading-notice">چهار کاربست برای هر آیه؛ هر کاربست با شاهدِ لفظی از همین آیه، استنباطِ روشن، منبعِ دقیق و مرزِ سوءاستفادهٔ اختصاصی. کاربستِ بی‌شاهد، شعار است.</p>`;

  const uses = entry && Array.isArray(entry.uses) ? entry.uses.slice(0, 4) : (entry ? [entry] : []);
  if (uses.length) {
    const cards = uses.map((use, index) => `<article class="apply-card">
        <p class="apply-field"><b>${faNumber(index + 1)}.</b> ${escapeHTML(use.field)}</p>
        ${use.basis ? `<p class="apply-basis">شاهدِ متنی: «${escapeHTML(use.basis)}»</p>` : ""}
        <p class="apply-text">${scholarCite(use.text)}</p>
        <p class="apply-cite">${scholarCite(use.cite || "")}</p>
        <p class="apply-guard"><b>مرزِ سوءاستفاده</b>${scholarCite(use.guard || "")}</p>
      </article>`).join("");
    const pending = uses.length < 4 ? `<p class="apply-pending">برای این آیه ${faNumber(4 - uses.length)} کاربستِ دیگر در بازبینی است.</p>` : "";
    return `<section class="detail-panel application-panel">${head}<div class="apply-grid">${cards}</div>${pending}</section>`;
  }
  return `<section class="detail-panel application-panel">${head}
    <p class="apply-empty">برای این آیه هنوز چهار کاربستِ مستند نوشته نشده است. به‌جای تولیدِ خودکارِ کاربست (که به تحمیل می‌انجامد)، سه دروازهٔ زیر را کامل کنید تا استنباط‌تان قابلِ بازبینی باشد.</p>
    ${methodBlock(meta)}
  </section>`;
}

function methodBlock(meta) {
  const method = meta && meta.method;
  if (!method) return "";
  return `<div class="apply-method"><p class="eyebrow">${escapeHTML(method.title)}</p><ol>${method.steps.map((step) => `<li>${scholarCite(step)}</li>`).join("")}</ol><p class="apply-rule">${scholarCite(method.rule)}</p><p class="scholar-note">${scholarCite(method.cite)}</p></div>`;
}

function renderDetailPanel() {
  const verse = state.selected;
  if (!verse) return;
  const panels = {
    notes: detailPanelNotes,
    foundations: detailPanelFoundations,
    framework: detailPanelFramework,
    messages: detailPanelMessages,
    context: detailPanelContext,
    thematic: detailPanelThematic,
    network: detailPanelNetwork,
    quran: detailPanelQuran,
    tafsir: detailPanelTafsir,
    modern: detailPanelModern,
    critical: detailPanelCritical,
    research: detailPanelResearch,
    application: applicationPanel,
  };
  const panel = (panels[state.detailTab] || detailPanelNotes)(verse);
  const researchSubmission = state.detailTab === "research" ? `<section class="detail-panel research-submission"><h3>برداشت یا پیشنهاد پژوهش من</h3><p>موضوع را همراه شاهدی از همین آیه بفرستید؛ پیشنهاد تا بازبینی مدیر منتشر نمی‌شود.</p>${proposalForm(verse, "research")}</section>` : "";
  // لایهٔ پژوهشیِ عمومی فقط برای آیه‌های بدونِ پروندهٔ تحریری نمایش داده می‌شود؛
  // برای آیه‌های دارای پرونده، همان بندهای اختصاصیِ هر فیلد کافی است و تکرار لازم نیست.
  const scholar = (!dossierFor(verse) && !["modern", "critical"].includes(state.detailTab)) ? scholarBlock(verse, state.detailTab) : "";
  $("#detail-panels").innerHTML = `${panel}${scholar}${fieldNotePanel(verse, state.detailTab)}${researchSubmission}`;
}

function saveNote() {
  const input = $("#verse-note");
  if (!input || !state.selected) return;
  const existing = state.notebook.find((item) => item.id === state.selected.id);
  if (existing) {
    existing.note = input.value.trim().slice(0, 3000);
  } else {
    state.notebook.unshift({
      id: state.selected.id,
      query: state.query,
      reference: state.selected.reference,
      arabic: state.selected.arabic,
      persian: state.selected.persian,
      note: input.value.trim().slice(0, 3000),
      savedAt: new Date().toISOString(),
    });
  }
  persistNotebook();
  updateSaveButton();
  $("#note-status").textContent = "روی همین دستگاه ذخیره شد.";
}

function surahRecords(surah) {
  return state.corpus.filter((record) => record.surah === surah);
}

function openLibrary(mode, shouldNavigate = true) {
  state.libraryMode = mode;
  const surahs = [...new Map(state.corpus.map((record) => [record.surah, record])).values()];
  if (mode === "surahs") {
    $("#library-title").textContent = "پژوهش در ۱۱۴ سوره";
    $("#library-description").textContent = "در پروندهٔ هر سوره چهار فیلدِ جدا می‌بینید: نمای متن‌محور، موضوعاتِ دارای شاهد واژگانی، واژه‌های کم‌تکرار در بافت آیه، و نقل‌های دقیقِ یک منبع تفسیری با ارجاع.";
    $("#library-list").innerHTML = surahs.map((surah) => `<button class="library-card" type="button" data-surah="${surah.surah}"><b>${faNumber(surah.surah)} · ${escapeHTML(surah.surahName)}</b><span>${escapeHTML(surah.revelation)} · ${faNumber(surahRecords(surah.surah).length)} آیه</span><i>←</i></button>`).join("");
  } else if (mode === "topics") {
    const byId = new Map(state.concepts.map((concept) => [concept.id, concept]));
    $("#library-title").textContent = "نقشهٔ گستردهٔ موضوعات قرآن";
    $("#library-description").textContent = `${faNumber(state.concepts.length)} مسیر واژگانیِ شفاف در پنج حوزه آماده است. هر موضوع با واژه‌های عربیِ قابل مشاهده جست‌وجو می‌شود؛ این فهرست، نقشهٔ ورود به متن است نه فهرستِ تفسیرهای قطعی.`;
    $("#library-list").innerHTML = state.topicCategories.map((category) => {
      const concepts = category.topics.map((id) => byId.get(id)).filter(Boolean);
      return `<section class="topic-category"><p class="eyebrow">${escapeHTML(category.title)}</p><p>${escapeHTML(category.description)}</p><div class="topic-catalog-list">${concepts.map((concept) => `<button type="button" data-topic-concept="${escapeHTML(concept.id)}">${escapeHTML(concept.title)}</button>`).join("")}</div></section>`;
    }).join("");
  } else {
    $("#library-title").textContent = "داستان‌ها و مسیرهای روایی قرآن";
    $("#library-description").textContent = "هر مسیر روایی، بازهٔ آیات و پرسشِ خوانش خود را دارد. فهرست فعلی مسیرهای آغازین است و برای پوشش کامل‌تر، با منابعِ چندگانه نسخه‌بندی می‌شود.";
    $("#library-list").innerHTML = state.stories.map((story) => `<button class="library-card story-card" type="button" data-story="${escapeHTML(story.id)}"><b>${escapeHTML(story.title)}</b><span>${story.passages.map((passage) => `${faNumber(passage.surah)}:${faNumber(passage.start)}–${faNumber(passage.end)}`).join(" · ")}</span><i>←</i></button>`).join("");
  }
  if (shouldNavigate) navigate("library");
  else showScreen("library");
}

function openSurah(surahNumber, shouldNavigate = true) {
  const records = surahRecords(Number(surahNumber));
  if (!records.length) return;
  const sample = records[0];
  state.selectedSurah = { number: sample.surah, name: sample.surahName, revelation: sample.revelation, verses: records.length };
  state.surahTab = "overview";
  renderSurah();
  if (shouldNavigate) navigate("surah", String(surahNumber));
  else showScreen("surah", String(surahNumber));
}

function surahReferenceLabel(reference) {
  const match = String(reference).match(/^(\d+):(\d+)(?:-(\d+))?$/);
  if (!match) return String(reference);
  const [, surahNumber, startAyah, endAyah] = match;
  const start = `${faNumber(surahNumber)}:${faNumber(startAyah)}`;
  return endAyah && endAyah !== startAyah ? `${start}–${faNumber(endAyah)}` : start;
}

function surahVerseButton(reference, label = "") {
  const referenceText = String(reference);
  const match = referenceText.match(/^(\d+):(\d+)(?:-(\d+))?$/);
  const targetReference = match ? `${match[1]}:${match[2]}` : referenceText;
  const referenceLabel = surahReferenceLabel(referenceText);
  return `<button class="surah-reference-button" type="button" data-open-surah-verse="${escapeHTML(targetReference)}" aria-label="باز کردن آیهٔ ${escapeHTML(referenceLabel)}"><bdi dir="ltr">${escapeHTML(referenceLabel)}</bdi>${label ? `<span>${escapeHTML(label)}</span>` : ""}</button>`;
}

function surahSourceMeta(sourceId) {
  return state.surahDossierMeta?.sources?.[sourceId] || {};
}

function surahSourceLink(source, label = "پیوند به منبع بالادستی ↗") {
  const url = /^https?:\/\//i.test(String(source?.sourceUrl || "")) ? source.sourceUrl : "";
  return url ? `<a class="surah-source-link" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label)}</a>` : "";
}

function renderSurahOverview(surah, dossier) {
  const units = (dossier.overview || []).map((unit) => {
    const source = surahSourceMeta(unit.sourceId);
    const headings = (unit.headings || []).map((heading) => `<li>${escapeHTML(heading)}</li>`).join("");
    const title = unit.title || "بازهٔ تفسیری";
    const excerpt = unit.excerpt ? `<blockquote class="surah-source-excerpt" lang="fa" dir="rtl">${escapeHTML(unit.excerpt)}${unit.excerptTruncated ? `<span class="excerpt-ellipsis" aria-label="ادامهٔ متن در منبع حذف شده است"> …</span>` : ""}</blockquote>` : "";
    return `<details class="surah-outline-unit"><summary><bdi class="surah-range" dir="ltr">${escapeHTML(surahReferenceLabel(unit.reference))}</bdi><span>${escapeHTML(title)}</span><small>${faNumber((unit.headings || []).length)} عنوان</small></summary><div class="surah-outline-body">${excerpt}<p class="surah-outline-label">عنوان‌های ثبت‌شده در متن منبع</p>${headings ? `<ol class="surah-heading-list">${headings}</ol>` : `<p class="study-unavailable">برای این بازه عنوانِ جداگانه‌ای ثبت نشده است.</p>`}<div class="surah-reference-list">${surahVerseButton(unit.reference, "باز کردن آیهٔ آغازین")}</div><small class="surah-attribution">${escapeHTML(source.title || "المیزان")} · ${escapeHTML(source.source || "")} · نسخهٔ ${escapeHTML(source.version || "")}${unit.sourceRecordId ? ` · شناسهٔ قطعهٔ داده: ${escapeHTML(unit.sourceRecordId)}` : ""}</small>${surahSourceLink(source)}</div></details>`;
  }).join("");
  const method = state.surahDossierMeta?.editorialMethod?.overview || "";
  return `<section class="detail-panel surah-overview-panel"><p class="eyebrow">نمای کلی سوره</p><h3>نقشهٔ تفسیری بر پایهٔ بازه‌های واقعیِ آیه</h3><p class="reading-notice">${escapeHTML(method)} گزیده‌ها دیدگاهِ منبع را بازتاب می‌دهند؛ درج آن‌ها به‌معنای تأیید مستقلِ ادعاهای تاریخی، کلامی یا فقهی نیست. برای بررسی اختلاف، نقل‌های منابع دیگر را جداگانه ببینید.</p><div class="surah-outline-list">${units || `<p class="study-unavailable">نقشهٔ منبع‌دار برای این سوره در دسترس نیست.</p>`}</div></section>`;
}

function renderSurahThemes(dossier) {
  const sourceThemes = (dossier.themes || []).filter((theme) => theme.kind === "source-heading").map((theme) => {
    const source = surahSourceMeta(theme.sourceId);
    const references = theme.references || [];
    const firstReference = references[0] || "";
    const rangeLabel = firstReference ? surahReferenceLabel(firstReference) : "";
    const extraCount = references.length > 1 ? ` · ${faNumber(references.length)} بازه` : "";
    const referenceLinks = references.map((reference) => `<li>${surahVerseButton(reference)}</li>`).join("");
    return `<details class="surah-theme-source"><summary><span>${escapeHTML(theme.title)}</span><small>${escapeHTML(rangeLabel)}${extraCount}</small></summary><div class="surah-theme-source-body"><p>عنوانِ عینِ متنِ ${escapeHTML(source.title || "المیزان")} است، نه بازگوییِ تحریری یا نتیجهٔ موردِ اجماع.</p><ul class="surah-theme-reference-list">${referenceLinks}</ul><small class="surah-attribution">${escapeHTML(source.source || "")} · نسخهٔ ${escapeHTML(source.version || "")}</small>${surahSourceLink(source)}</div></details>`;
  }).join("");
  const lexicalThemes = (dossier.themes || []).filter((theme) => theme.kind === "lexical-witness").map((theme) => `<article class="surah-theme-card"><header><h4>${escapeHTML(theme.title)}</h4><span>${faNumber(theme.count)} آیهٔ دارای شاهد</span></header><p class="surah-theme-witnesses"><b>صورت‌های شاهد:</b> ${(theme.witnesses || []).map(escapeHTML).join("، ")}</p><p class="surah-theme-witnesses"><b>کلیدهای واژگانی:</b> ${(theme.terms || []).map(escapeHTML).join("، ")}</p><div class="surah-reference-list"><span>نمونهٔ مواضع:</span>${(theme.references || []).map((reference) => surahVerseButton(reference)).join("")}</div></article>`).join("");
  const method = state.surahDossierMeta?.editorialMethod?.themes || "";
  return `<section class="detail-panel surah-themes-panel"><p class="eyebrow">موضوعات محوری و کلیدی</p><h3>عنوان‌های تفسیری و شاهدهای واژگانی</h3><p class="reading-notice">${escapeHTML(method)} عنوان‌های منبع به همان اثر نسبت داده شده‌اند؛ نقشهٔ واژگانی فقط مواضعِ واژه‌های شاهد را نشان می‌دهد و به‌تنهایی محور قطعیِ سوره را اثبات نمی‌کند.</p><h4 class="surah-subsection-title">عنوان‌های المیزان · ${faNumber((dossier.themes || []).filter((theme) => theme.kind === "source-heading").length)}</h4><div class="surah-theme-source-list">${sourceThemes || `<p class="study-unavailable">عنوان تفسیری برای نمایش ثبت نشده است.</p>`}</div><h4 class="surah-subsection-title">نقشهٔ واژگانیِ تکمیلی</h4><div class="surah-theme-grid">${lexicalThemes || `<p class="study-unavailable">برای این سوره شاهد واژگانیِ کافی ثبت نشده است.</p>`}</div></section>`;
}

function renderSurahVocabulary(surah, dossier) {
  const entries = (dossier.vocabulary || []).map((item) => {
    const source = surahSourceMeta(item.sourceId);
    const words = item.words || [];
    const wordMarkup = words.map((word) => `<span class="surah-vocabulary-word"><bdi lang="${escapeHTML(source.language || "ar")}" dir="rtl">${escapeHTML(word.word)}</bdi>${word.surface && word.surface !== word.word ? `<small>صورتِ آیه: <bdi lang="ar" dir="rtl">${escapeHTML(word.surface)}</bdi></small>` : ""}<small>${escapeHTML(surahReferenceLabel(word.reference))} · ${faNumber(word.frequency)} بار در پیکره</small></span>`).join("");
    const verseLinks = words.map((word) => surahVerseButton(word.reference, "موضعِ واژه")).join("");
    const excerpt = item.excerpt ? `<blockquote class="surah-source-excerpt" lang="${escapeHTML(source.language || "ar")}" dir="rtl">${escapeHTML(item.excerpt)}${item.excerptTruncated ? `<span class="excerpt-ellipsis" aria-label="ادامهٔ متن در منبع حذف شده است"> …</span>` : ""}</blockquote>` : "";
    return `<details class="surah-vocabulary-entry"><summary><span class="surah-vocabulary-words">${wordMarkup}</span><small>${escapeHTML(source.title || "منبع تفسیری")} · ${escapeHTML(surahReferenceLabel(item.reference))}</small></summary><div class="surah-vocabulary-context">${item.focus ? `<p><b>عنوانِ بحث در منبع</b>${escapeHTML(item.focus)}</p>` : ""}${excerpt}<small class="surah-attribution">${escapeHTML(source.title || "")} · ${escapeHTML(source.source || "")} · نسخهٔ ${escapeHTML(source.version || "")} · ذیل ${escapeHTML(surahReferenceLabel(item.reference))}</small><div class="surah-reference-list">${verseLinks}</div>${surahSourceLink(source)}</div></details>`;
  }).join("");
  const method = state.surahDossierMeta?.editorialMethod?.vocabulary || "";
  return `<section class="detail-panel surah-vocabulary-panel"><p class="eyebrow">مفردات و لغات دشوار</p><h3>${faNumber((dossier.vocabulary || []).length)} مدخلِ لغویِ منبع‌دار</h3><p class="reading-notice">${escapeHTML(method)} این فهرست گزیدهٔ واژه‌هایی است که خودِ منابع درباره‌شان بحث کرده‌اند؛ بسامد فقط اطلاعاتِ کمکی است و معیارِ دشواری یا معنای قطعی نیست.</p><div class="surah-vocabulary-list">${entries || `<p class="study-unavailable">مدخلِ لغوی برای نمایش ثبت نشده است.</p>`}</div></section>`;
}

function renderSurahReflections(surah, dossier) {
  const cards = (dossier.reflections || []).map((item) => {
    const source = surahSourceMeta(item.sourceId);
    if (item.kind === "modern-research-note") {
      return `<article class="surah-reflection-card surah-research-note"><header><div><h4>یادداشتِ پژوهشیِ معاصر · بازگویی تحریری</h4><small>${escapeHTML(item.citation || "")} · ذیل ${escapeHTML(surahReferenceLabel(item.reference))}</small></div>${surahVerseButton(item.reference)}</header><p>${escapeHTML(item.text || "")}</p><small class="surah-attribution">این عبارت نقلِ مستقیم از اثر نیست؛ ارجاعِ ثبت‌شده در پروندهٔ پژوهشی حفظ شده است.</small></article>`;
    }
    const quote = item.quote || "";
    const excerpt = quote ? `<blockquote class="surah-source-excerpt" lang="${escapeHTML(source.language || "ar")}" dir="rtl">${escapeHTML(quote)}${item.quoteTruncated ? `<span class="excerpt-ellipsis" aria-label="ادامهٔ متن در منبع حذف شده است"> …</span>` : ""}</blockquote>` : "";
    const focus = item.focus ? `<h4>${escapeHTML(item.focus)}</h4>` : `<h4>گزیدهٔ تفسیری</h4>`;
    return `<article class="surah-reflection-card"><header><div>${focus}<small>${escapeHTML(source.title || "منبع تفسیری")} · ${escapeHTML(source.source || "")} · نسخهٔ ${escapeHTML(source.version || "")} · ذیل ${escapeHTML(surahReferenceLabel(item.reference))}</small></div>${surahVerseButton(item.reference)}</header>${excerpt}<small class="surah-attribution">نقلِ عینِ متنِ منبع؛ درج آن به‌معنای تأیید مستقل یا اجماع نیست.</small>${surahSourceLink(source)}</article>`;
  }).join("");
  const method = state.surahDossierMeta?.editorialMethod?.reflections || "";
  return `<section class="detail-panel surah-reflections-panel"><p class="eyebrow">اقوال مهم و تأمل‌برانگیز</p><h3>گزیده‌های منتسب از منابع کهن و جدید</h3><p class="reading-notice">${escapeHTML(method)} هر نقل در کنار نامِ منبع و بازهٔ آیه آمده است. بازگوییِ پژوهشی با نقلِ مستقیم جدا شده و هیچ قولی به‌عنوانِ اجماع عرضه نمی‌شود.</p><div class="surah-reflection-list">${cards || `<p class="study-unavailable">نقل یا یادداشتِ پژوهشی برای این سوره در دسترس نیست.</p>`}</div></section>`;
}

function renderSurah() {
  const surah = state.selectedSurah;
  if (!surah) return;
  const dossier = state.surahDossiers[String(surah.number)];
  $("#surah-reference").textContent = `سورهٔ ${faNumber(surah.number)} · ${surah.revelation} · ${faNumber(surah.verses)} آیه`;
  $("#surah-title").textContent = surah.name;
  $("#surah-description").textContent = dossier ? "پروندهٔ سوره چهار مسیرِ مستقل دارد: نمای متن‌محور، محورهای واژگانی، واژگانِ نیازمند بررسی و نقل‌های تفسیریِ مستند." : "دادهٔ پژوهشیِ این سوره در نسخهٔ محلی در دسترس نیست.";
  $$("#surah-screen [data-surah-tab]").forEach((button) => {
    const active = button.dataset.surahTab === state.surahTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  $("#surah-panels").setAttribute("aria-labelledby", `surah-tab-${state.surahTab}`);
  if (!dossier) {
    $("#surah-panels").innerHTML = `<section class="detail-panel"><p class="study-unavailable">پروندهٔ سوره بارگیری نشد؛ لطفاً داده‌های آفلاین برنامه را به‌روز کنید.</p></section>`;
    return;
  }
  const panels = {
    overview: renderSurahOverview(surah, dossier),
    themes: renderSurahThemes(dossier),
    vocabulary: renderSurahVocabulary(surah, dossier),
    reflections: renderSurahReflections(surah, dossier),
  };
  $("#surah-panels").innerHTML = panels[state.surahTab] || panels.overview;
}

function resultVerse(record, evidence, type = "exact") {
  return { ...record, evidence, type, score: 0 };
}

function prepareSurahVerseResults(surah) {
  state.query = `سورهٔ ${surah.name}`;
  state.concept = null;
  state.terms = [];
  state.matches = surahRecords(surah.number).map((record) => resultVerse(record, [{ label: "آیهٔ این سوره", type: "exact", source: "پیکرهٔ قرآن", origin: "پروندهٔ سوره" }]));
  state.shown = PAGE_SIZE;
  state.filter = "all";
  state.contextVerseId = state.matches[0]?.id || null;
  renderResults();
}

function openSurahVerses() {
  if (!state.selectedSurah) return;
  prepareSurahVerseResults(state.selectedSurah);
  navigate("results");
}

function openSurahReference(reference) {
  const record = state.recordById.get(reference);
  if (!record) return;
  const surah = { number: record.surah, name: record.surahName };
  prepareSurahVerseResults(surah);
  openVerse(reference);
}

function storyPassageIds(story) {
  const ids = new Set();
  story.passages.forEach((passage) => {
    for (let ayah = passage.start; ayah <= passage.end; ayah += 1) ids.add(`${passage.surah}:${ayah}`);
  });
  return ids;
}

function storyPassageRecords(story) {
  const records = [];
  const seen = new Set();
  story.passages.forEach((passage) => {
    for (let ayah = passage.start; ayah <= passage.end; ayah += 1) {
      const record = state.recordById.get(`${passage.surah}:${ayah}`);
      if (record && !seen.has(record.id)) {
        seen.add(record.id);
        records.push(record);
      }
    }
  });
  return records;
}

function storyRangeLabel(story) {
  return story.passages.map((passage) => `${faNumber(passage.surah)}:${faNumber(passage.start)}–${faNumber(passage.end)}`).join(" · ");
}

function sourceVerseButton(reference, label = "مشاهدهٔ آیه") {
  const match = String(reference || "").match(/(\d+)\s*:\s*(\d+)/);
  if (!match) return "";
  const record = state.recordById.get(`${Number(match[1])}:${Number(match[2])}`);
  return record ? `<button class="story-reference-button" type="button" data-story-verse-id="${escapeHTML(record.id)}">${escapeHTML(label)} · ${escapeHTML(record.reference)} ←</button>` : "";
}

function renderStory() {
  const story = state.selectedStory;
  if (!story) return;
  const dossier = state.storyDossiers[story.id] || { basis: story.note, charactersDetailed: [], stages: [], keyConcepts: [], topics: [], subtleties: [], lifePrinciples: [], wonders: [], narratology: {}, elements: {}, semiotics: [], applications: [] };
  const records = storyPassageRecords(story);
  const passageCount = records.length;
  const insights = (items, empty = "برای این بخش هنوز دادهٔ آیه‌لنگر ثبت نشده است.") => items?.length ? `<div class="story-insight-list">${items.map((item) => `<article><h4>${escapeHTML(item.title)}</h4><p>${escapeHTML(item.note)}</p>${item.reference ? sourceVerseButton(item.reference, `شاهد ${item.reference}`) : ""}</article>`).join("")}</div>` : `<p>${escapeHTML(empty)}</p>`;
  $("#story-reference").textContent = `${storyRangeLabel(story)} · ${faNumber(passageCount)} آیه`;
  $("#story-title").textContent = story.title;
  $("#story-description").textContent = `${dossier.basis} همهٔ مدخل‌ها با آیهٔ لنگر عرضه شده‌اند؛ برای تفسیر منبع‌دار هر آیه، پروندهٔ آیه و تب تفاسیر را باز کنید.`;
  $$("[data-story-tab]").forEach((button) => button.classList.toggle("active", button.dataset.storyTab === state.storyTab));
  const narratologyItems = [
    ["آغاز روایت", dossier.narratology?.opening], ["گره یا کشمکش", dossier.narratology?.tension], ["چرخش روایت", dossier.narratology?.turn], ["فرجام و افق خوانش", dossier.narratology?.closure],
  ].filter(([, item]) => item).map(([title, item]) => ({ title: `${title}: ${item.title}`, reference: item.reference, note: item.note }));
  const elementItems = [
    dossier.elements?.setting ? { title: "صحنهٔ آغاز", reference: dossier.elements.setting.reference, note: dossier.elements.setting.note } : null,
    dossier.elements?.tension ? { title: "کشمکش", reference: dossier.elements.tension.reference, note: dossier.elements.tension.note } : null,
    dossier.elements?.resolution ? { title: "فرجام", reference: dossier.elements.resolution.reference, note: dossier.elements.resolution.note } : null,
  ].filter(Boolean);
  const panels = {
    verses: `<section class="detail-panel"><p class="eyebrow">همهٔ آیات داستان</p><h3>متن کاملِ بازهٔ روایی</h3><p class="reading-notice">${faNumber(passageCount)} آیهٔ این مسیر در فهرست زیر آمده است. هر آیه را لمس کنید تا پروندهٔ تفصیلی، سیاق و تفاسیر منبع‌دار آن باز شود.</p><div class="story-all-verses">${records.map((record) => `<button class="story-verse-row" type="button" data-story-verse-id="${escapeHTML(record.id)}"><b>${escapeHTML(record.reference)}</b><span lang="ar" dir="rtl">${escapeHTML(record.arabic)}</span><small>${escapeHTML(record.persian)}</small></button>`).join("")}</div></section>`,
    concepts: `<section class="detail-panel"><p class="eyebrow">مفاهیم کلیدی داستان</p><h3>مفهوم‌ها با آیهٔ لنگر</h3><p class="reading-notice">این مفهوم‌ها از صحنه‌ها و گزاره‌های خود روایت استخراج شده‌اند؛ هم‌معناییِ قطعی یا تفسیر نهایی را ادعا نمی‌کنند.</p>${insights(dossier.keyConcepts)}</section>`,
    characters: `<section class="detail-panel"><p class="eyebrow">شخصیت‌ها و نقش‌ها</p><h3>چه کسانی در حرکت روایت نقش دارند؟</h3><div class="story-character-grid">${(dossier.charactersDetailed || []).map((character) => `<article><h4>${escapeHTML(character.name)}</h4><p>${escapeHTML(character.role)}</p>${sourceVerseButton(character.reference, character.reference)}</article>`).join("") || "<p>شخصیت‌ها در حال تکمیل‌اند.</p>"}</div></section>`,
    topics: `<section class="detail-panel"><p class="eyebrow">موضوعات داستان</p><h3>حوزه‌های پژوهشِ قابل پیگیری</h3>${insights(dossier.topics)}</section>`,
    subtleties: `<section class="detail-panel"><p class="eyebrow">نکات و ظرایف داستان</p><h3>به حرکت و ترتیبِ صحنه‌ها دقت کنید.</h3>${insights(dossier.subtleties)}</section>`,
    principles: `<section class="detail-panel"><p class="eyebrow">اصول زندگی در داستان</p><h3>قاعده‌های متن‌محور و پرسشِ کاربرد امروز</h3><p class="reading-notice">اصل‌ها آیه‌لنگر دارند؛ کاربست امروز پرسش پژوهشی است، نه نسخه یا حکمِ آماده.</p>${insights(dossier.lifePrinciples)}<div class="story-application-list"><h4>پرسش‌های کاربست امروز</h4>${(dossier.applications || []).map(([area, question]) => `<article><h4>${escapeHTML(area)}</h4><p>${escapeHTML(question)}</p></article>`).join("")}</div></section>`,
    wonders: `<section class="detail-panel"><p class="eyebrow">شگفتی‌های داستان</p><h3>رخدادهای برجسته در متن</h3><p class="reading-notice">«شگفتی» نام‌گذاریِ یک رخداد برجستهٔ روایت است؛ شرح تفسیری و اعتقادی آن باید در منابع آیه بررسی شود.</p>${insights(dossier.wonders)}</section>`,
    narratology: `<section class="detail-panel"><p class="eyebrow">روایت‌شناسی داستان</p><h3>آغاز، کشمکش، چرخش و فرجام</h3><p>این نقشه به خواننده کمک می‌کند ساختِ روایت را از حافظه یا خلاصه‌گویی جدا کند.</p>${insights(narratologyItems)}</section>`,
    elements: `<section class="detail-panel"><p class="eyebrow">عناصر داستان</p><h3>صحنه، شخصیت، کشمکش و فرجام</h3>${insights(elementItems)}<div class="story-character-grid"><h4>بازیگران و کارکرد روایی</h4>${(dossier.elements?.characters || []).map((character) => `<article><h4>${escapeHTML(character.name)}</h4><p>${escapeHTML(character.role)}</p>${sourceVerseButton(character.reference, character.reference)}</article>`).join("")}</div></section>`,
    semiotics: `<section class="detail-panel"><p class="eyebrow">نشانه‌شناسی داستان</p><h3>نشانه‌های رواییِ قابل مشاهده</h3><p class="reading-notice">این بخش، عنصرِ تکرارشونده یا برجسته در خودِ متن را نشان می‌دهد؛ معنای نهاییِ نشانه را از پیش تعیین نمی‌کند.</p>${insights(dossier.semiotics)}</section>`,
  };
  $("#story-panels").innerHTML = panels[state.storyTab] || panels.verses;
}

function openStory(id, shouldNavigate = true) {
  const story = state.stories.find((item) => item.id === id);
  if (!story) return;
  state.selectedStory = story;
  state.storyTab = "verses";
  renderStory();
  if (shouldNavigate) navigate("story", id);
  else showScreen("story", id);
}

function openStoryPassages() {
  const story = state.selectedStory;
  if (!story) return;
  const ids = storyPassageIds(story);
  state.query = story.title;
  state.concept = null;
  state.terms = [];
  state.matches = [...ids].map((id) => state.recordById.get(id)).filter(Boolean).map((record) => resultVerse(record, [{ label: "آیهٔ مسیر روایی", type: "exact", source: "پروندهٔ داستان", origin: story.note }]));
  state.shown = PAGE_SIZE;
  state.filter = "all";
  state.contextVerseId = state.matches[0]?.id || null;
  renderResults();
  navigate("results");
}

function showScreen(name, verseId = null) {
  state.screen = name;
  $("#search-screen").hidden = name !== "search";
  $("#library-screen").hidden = name !== "library";
  $("#surah-screen").hidden = name !== "surah";
  $("#story-screen").hidden = name !== "story";
  $("#results-screen").hidden = name !== "results";
  $("#detail-screen").hidden = name !== "detail";
  if (name === "detail" && verseId && state.selected?.id !== verseId) openVerse(verseId, false);
  window.scrollTo({ top: 0, behavior: "auto" });
}

function navigate(name, verseId = null) {
  const hashMap = { search: "", results: "#results", library: `#library/${state.libraryMode || ""}`, surah: `#surah/${verseId || state.selectedSurah?.number || ""}`, story: `#story/${verseId || state.selectedStory?.id || ""}` };
  const hash = name === "detail" ? `#verse/${verseId || state.selected?.id || ""}` : hashMap[name];
  history.pushState({ screen: name, verseId }, "", `${location.pathname}${hash}`);
  showScreen(name, verseId);
}

function restoreFromHistory() {
  const hash = location.hash;
  if (hash.startsWith("#library/")) {
    const mode = decodeURIComponent(hash.slice(9));
    if (["surahs", "stories", "topics"].includes(mode)) {
      openLibrary(mode, false);
      return;
    }
  }
  if (hash.startsWith("#surah/")) {
    const surah = Number(hash.slice(7));
    if (Number.isInteger(surah) && surahRecords(surah).length) {
      openSurah(surah, false);
      return;
    }
  }
  if (hash.startsWith("#story/")) {
    const storyId = decodeURIComponent(hash.slice(7));
    if (state.stories.some((story) => story.id === storyId)) {
      openStory(storyId, false);
      return;
    }
  }
  if (hash.startsWith("#verse/") && state.matches.length) {
    const id = decodeURIComponent(hash.slice(7));
    if (state.matches.some((item) => item.id === id)) {
      openVerse(id, false);
      showScreen("detail");
      return;
    }
  }
  if (hash === "#results" && state.matches.length) {
    showScreen("results");
    return;
  }
  showScreen("search");
}

async function copyDonationCardNumber(event) {
  const button = event.currentTarget;
  const status = $("#donation-status");
  const cardNumber = button.dataset.cardNumber || "6219861057113903";
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(cardNumber);
    } else {
      const temporary = document.createElement("textarea");
      temporary.value = cardNumber;
      temporary.setAttribute("readonly", "");
      temporary.style.position = "fixed";
      temporary.style.insetInlineStart = "-9999px";
      document.body.appendChild(temporary);
      temporary.select();
      const copied = document.execCommand?.("copy");
      temporary.remove();
      if (!copied) throw new Error("Clipboard unavailable");
    }
    status.textContent = "شمارهٔ کارت کپی شد؛ واریز هر مبلغ کاملاً به انتخاب شماست.";
  } catch {
    status.textContent = "کپی خودکار انجام نشد؛ شماره را لمس طولانی و دستی کپی کنید.";
  }
}

$("#copy-donation-card")?.addEventListener("click", copyDonationCardNumber);

$("#concept-form").addEventListener("submit", (event) => {
  event.preventDefault();
  searchResearchFields();
});

$("#starter-list")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-concept]");
  if (button) return runStarter(button.dataset.concept);
  if (event.target.closest("[data-open-topic-library]")) openLibrary("topics");
});

$("#open-topic-library").addEventListener("click", () => openLibrary("topics"));
$("#open-surah-library").addEventListener("click", () => openLibrary("surahs"));
$("#open-story-library").addEventListener("click", () => openLibrary("stories"));
$("#library-list").addEventListener("click", (event) => {
  const topic = event.target.closest("[data-topic-concept]");
  if (topic) {
    const concept = state.concepts.find((item) => item.id === topic.dataset.topicConcept);
    if (concept) return runStarter(concept.aliases[0] || concept.title);
  }
  const surah = event.target.closest("[data-surah]");
  if (surah) return openSurah(surah.dataset.surah);
  const story = event.target.closest("[data-story]");
  if (story) openStory(story.dataset.story);
});
$("#surah-open-verses").addEventListener("click", openSurahVerses);
$("#surah-panels").addEventListener("click", (event) => {
  const referenceButton = event.target.closest("[data-open-surah-verse]");
  if (referenceButton) openSurahReference(referenceButton.dataset.openSurahVerse);
});
$$("[data-surah-tab]").forEach((button) => button.addEventListener("click", () => {
  state.surahTab = button.dataset.surahTab;
  renderSurah();
}));
$("#story-open-passages").addEventListener("click", openStoryPassages);
$$("[data-story-tab]").forEach((button) => button.addEventListener("click", () => {
  state.storyTab = button.dataset.storyTab;
  renderStory();
}));
$("#story-panels").addEventListener("click", (event) => {
  const reference = event.target.closest("[data-story-verse-id]");
  if (!reference) return;
  const id = reference.dataset.storyVerseId;
  const story = state.selectedStory;
  if (!story) return;
  const record = state.recordById.get(id);
  if (!record) return;
  state.query = story.title;
  state.concept = null;
  state.terms = [];
  state.matches = [resultVerse(record, [{ label: "آیهٔ لنگرِ داستان", type: "exact", source: "پروندهٔ داستان", origin: story.title }])];
  state.shown = PAGE_SIZE;
  state.filter = "all";
  openVerse(id);
});

$("#verse-list").addEventListener("submit", (event) => {
  const form = event.target.closest("[data-proposal-form]");
  if (!form) return;
  event.preventDefault();
  submitVerseProposal(form);
});

$("#verse-list").addEventListener("click", (event) => {
  const deleteButton = event.target.closest("[data-delete-proposal]");
  if (deleteButton) return deleteVerseProposal(deleteButton.dataset.deleteProposal);
  const inlineTab = event.target.closest("[data-inline-tab]");
  if (inlineTab) {
    state.inlineStudy = { verseId: inlineTab.dataset.inlineVerseId, tab: inlineTab.dataset.inlineTab };
    renderVerseList();
    return;
  }
  const openButton = event.target.closest("[data-open-verse]");
  if (openButton) openVerse(openButton.dataset.openVerse);
});

$("#context-study")?.addEventListener("click", (event) => {
  const selector = event.target.closest("[data-context-study-id]");
  if (!selector) return;
  state.contextVerseId = selector.dataset.contextStudyId;
  renderContextStudy();
});

$("#load-more").addEventListener("click", () => {
  state.shown += PAGE_SIZE;
  renderVerseList();
});

$$(".result-filters button").forEach((button) => button.addEventListener("click", () => {
  state.filter = button.dataset.filter;
  state.shown = PAGE_SIZE;
  renderResults();
}));

$$("#detail-screen [data-detail-tab]").forEach((button) => button.addEventListener("click", () => {
  state.detailTab = button.dataset.detailTab;
  renderDetail();
}));

$("#detail-panels").addEventListener("input", (event) => {
  const fieldNote = event.target.closest("[data-field-note]");
  if (fieldNote) saveFieldNote(fieldNote);
});

$("#detail-panels").addEventListener("submit", (event) => {
  const form = event.target.closest("[data-proposal-form]");
  if (!form) return;
  event.preventDefault();
  submitVerseProposal(form);
});

$("#detail-panels").addEventListener("click", (event) => {
  const tafsirButton = event.target.closest("[data-load-tafsir]");
  if (tafsirButton) return loadDeferredTafsir(tafsirButton.dataset.loadTafsir);
  const deleteButton = event.target.closest("[data-delete-proposal]");
  if (deleteButton) return deleteVerseProposal(deleteButton.dataset.deleteProposal);
  const contextButton = event.target.closest("[data-context-id]");
  if (contextButton) return openVerse(contextButton.dataset.contextId);
  const relatedButton = event.target.closest("[data-related-id]");
  if (relatedButton) return openVerse(relatedButton.dataset.relatedId);
  if (event.target.closest("#save-note")) saveNote();
});

$$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));
$("#brand-home").addEventListener("click", () => navigate("search"));
$("#save-verse").addEventListener("click", saveCurrentVerse);

$("#open-method").addEventListener("click", () => $("#method-dialog").showModal());
$("#open-sources").addEventListener("click", () => $("#sources-dialog").showModal());
$("#open-admin").addEventListener("click", () => {
  $("#admin-dialog").showModal();
  $("#admin-token").value = sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
  if (sessionStorage.getItem(ADMIN_TOKEN_KEY)) loadAdminProposals();
});
$("#admin-close").addEventListener("click", () => $("#admin-dialog").close());
$("#admin-load").addEventListener("click", loadAdminProposals);
$("#admin-refresh").addEventListener("click", loadAdminProposals);
$("#admin-logout").addEventListener("click", () => {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  $("#admin-token").value = "";
  $("#admin-proposals").replaceChildren();
  $("#admin-status").textContent = "از پنل مدیر خارج شدید.";
});
$("#admin-proposals").addEventListener("click", (event) => {
  const card = event.target.closest("[data-admin-proposal-id]");
  if (!card) return;
  if (event.target.closest("[data-admin-save]")) moderateAdminProposal(card, false);
  if (event.target.closest("[data-admin-delete]")) {
    if (window.confirm("این پیشنهاد برای همۀ کاربران حذف شود؟")) moderateAdminProposal(card, true);
  }
});
window.addEventListener("popstate", restoreFromHistory);
window.addEventListener("online", refreshPublicProposals);

if ("serviceWorker" in navigator && /^(https?:)$/.test(location.protocol)) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}

loadData().then(() => {
  if (!location.hash) history.replaceState({ screen: "search" }, "", location.pathname);
  restoreFromHistory();
}).catch((error) => {
  $("#search-status").textContent = error.message || "بارگیری داده‌ها ناموفق بود.";
});
