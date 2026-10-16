const CORPUS_URL = "static/offline-corpus.json";
const LEXICON_URL = "static/concept-lexicon.json";
const STORY_INDEX_URL = "static/story-index.json";
const STORY_DOSSIERS_URL = "static/story-dossiers.json";
const TOPIC_CATALOG_URL = "static/topic-catalog.json";
const TAFSIR_SOURCES_URL = "static/tafsir-sources.json";
const TAFSIR_CATALOG_URL = "static/tafsir-catalog.json";
const NOTEBOOK_KEY = "zehnyar-verse-notebook-v2";
const VERSE_PROPOSALS_KEY = "quran-pazhuheh-verse-proposals-v1";
const PAGE_SIZE = 12;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = {
  screen: "search",
  corpus: [],
  recordById: new Map(),
  lexicon: null,
  concepts: [],
  topicCategories: [],
  tafsirSources: [],
  tafsirRegistry: [],
  tafsirCatalog: [],
  tafsirLoadPromise: null,
  tafsirUnavailableSourceIds: new Set(),
  stories: [],
  storyDossiers: {},
  selectedStory: null,
  storyTab: "verses",
  libraryMode: null,
  selectedSurah: null,
  surahTab: "notes",
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

function loadVerseProposals() {
  try {
    const saved = JSON.parse(localStorage.getItem(VERSE_PROPOSALS_KEY) || "[]");
    return Array.isArray(saved) ? saved.filter((item) => item && item.verseId && item.kind && item.claim && item.witness) : [];
  } catch {
    return [];
  }
}

function persistVerseProposals() {
  localStorage.setItem(VERSE_PROPOSALS_KEY, JSON.stringify(state.verseProposals));
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

async function loadData() {
  const [corpusResponse, lexiconResponse, storyResponse, storyDossiersResponse, catalogResponse, tafsirRegistryResponse, tafsirCatalogResponse] = await Promise.all([
    fetch(CORPUS_URL), fetch(LEXICON_URL), fetch(STORY_INDEX_URL), fetch(STORY_DOSSIERS_URL), fetch(TOPIC_CATALOG_URL), fetch(TAFSIR_SOURCES_URL), fetch(TAFSIR_CATALOG_URL),
  ]);
  if (!corpusResponse.ok || !lexiconResponse.ok || !storyResponse.ok || !storyDossiersResponse.ok || !catalogResponse.ok || !tafsirRegistryResponse.ok || !tafsirCatalogResponse.ok) {
    throw new Error("پیکرهٔ محلی یا فهرست پژوهش در دسترس نیست.");
  }
  const corpus = await corpusResponse.json();
  state.lexicon = await lexiconResponse.json();
  const catalog = await catalogResponse.json();
  const tafsirRegistry = await tafsirRegistryResponse.json();
  const tafsirCatalog = await tafsirCatalogResponse.json();
  state.tafsirCatalog = tafsirCatalog.collections || [];
  state.concepts = [...(state.lexicon.concepts || []), ...(catalog.concepts || [])];
  state.topicCategories = catalog.categories || [];
  state.stories = (await storyResponse.json()).stories || [];
  state.storyDossiers = (await storyDossiersResponse.json()).dossiers || {};
  state.tafsirRegistry = tafsirRegistry.sources || [];
  state.tafsirSources = await loadTafsirSources(state.tafsirRegistry.filter((source) => source.loadPriority !== "on-demand"));
  state.corpus = corpus.verses.map(recordFromTuple);
  state.recordById = new Map(state.corpus.map((record) => [record.id, record]));
  $("#result-corpus").textContent = `${faNumber(state.corpus.length)} آیه`;
  renderStarters();
}

async function loadTafsirSources(sources) {
  const results = await Promise.allSettled(sources.map(async (source) => {
    const response = await fetch(source.file);
    if (!response.ok) throw new Error(`بارگیری ${source.title} ناموفق بود.`);
    const payload = await response.json();
    return { ...source, verses: payload.verses || {}, contents: payload.contents || {}, ayahMapping: payload.ayahMapping || {}, edition: payload.edition || {} };
  }));
  results.forEach((result, index) => {
    if (result.status === "rejected" && sources[index]) state.tafsirUnavailableSourceIds.add(sources[index].id);
  });
  return results.filter((result) => result.status === "fulfilled").map((result) => result.value);
}

function pendingTafsirSources() {
  const loaded = new Set(state.tafsirSources.map((source) => source.id));
  return state.tafsirRegistry.filter((source) => source.loadPriority === "on-demand" && !loaded.has(source.id) && !state.tafsirUnavailableSourceIds.has(source.id));
}

function ensureExtendedTafsirSources() {
  const pending = pendingTafsirSources();
  if (!pending.length) return Promise.resolve();
  if (!state.tafsirLoadPromise) {
    state.tafsirLoadPromise = loadTafsirSources(pending).then((sources) => {
      state.tafsirSources.push(...sources);
    }).finally(() => {
      state.tafsirLoadPromise = null;
    });
  }
  return state.tafsirLoadPromise;
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

function inlineTafsirEvidence(verse, maximum = 460) {
  const entry = primaryTafsirEntry(verse);
  if (!entry) return `<aside class="inline-tafsir-evidence unavailable"><b>شاهد تفسیریِ این آیه</b><p>متن تفسیریِ منبع‌دار در این نشست بارگیری نشد. برای تکمیل این بخش، اتصال یا دادهٔ آفلاین را بررسی کنید.</p></aside>`;
  const citation = `${entry.source.title}، ${entry.source.author}، نسخهٔ ${entry.source.version}`;
  return `<aside class="inline-tafsir-evidence"><b>شاهد تفسیریِ آیه — نقلِ بدون بازنویسی</b><p>«${escapeHTML(compactSourceText(entry.text, maximum))}»</p><small>${escapeHTML(citation)} · <a href="${escapeHTML(entry.source.sourceUrl)}" target="_blank" rel="noreferrer">منبع ↗</a></small></aside>`;
}

const ARABIC_STOPWORDS = new Set([
  "و", "ف", "ثم", "او", "ام", "بل", "لكن", "لا", "ما", "لم", "لن", "ان", "اذا", "اذ", "من", "الى", "عن", "على", "في", "ب", "ل", "ك", "هو", "هی", "هم", "هن", "انت", "انتم", "انا", "نحن", "هذا", "هذه", "ذلك", "تلك", "الذي", "التي", "الذين", "اللاتي", "كل", "قد", "كان", "كانت", "يكون", "يكونون", "ليس", "الا", "بسم"
]);
const PERSIAN_STOPWORDS = new Set([
  "و", "یا", "از", "به", "در", "با", "بر", "که", "را", "این", "آن", "برای", "تا", "اگر", "اما", "نیز", "هم", "است", "بود", "شد", "می", "شود", "شده", "خود", "همه", "هر", "یک", "ای", "اینان", "آنان", "او", "آنها", "ما", "شما", "من"
]);
const COMMAND_FORMS = new Set([
  "قل", "اعبدوا", "اتقوا", "انفقوا", "اقيموا", "اقیموا", "اتوا", "آتوا", "اذكروا", "اتبعوا", "استغفروا", "توبوا", "اصبروا", "اصبر", "اوفوا", "قولوا", "خذوا", "كلوا", "اشربوا", "انظروا", "اعلموا", "اعملوا", "ادعوا", "اسجدوا", "اركعوا", "احسنوا", "اعدلوا", "كونوا", "کونوا", "امنوا", "آمنوا"
]);
const COGNITIVE_SCHEMAS = [
  { title: "مسیر و حرکت", terms: ["صراط", "سبيل", "سبیل", "طريق", "طریق", "هدى", "هدی", "اهتدى", "اهتدی", "ضل", "رجع", "سار"] },
  { title: "نور و تاریکی", terms: ["نور", "ظلمات", "ظلمة", "نار"] },
  { title: "درون و ظرف", terms: ["في", "فیه", "صدور", "قلب", "قلوب", "بطن"] },
  { title: "تراز و سنجش", terms: ["ميزان", "میزان", "وزن", "قسط", "عدل"] },
  { title: "بالا و پایین", terms: ["فوق", "تحت", "رفع", "نزل", "سماء", "ارض"] },
  { title: "دادوستد و سود/زیان", terms: ["اشترى", "اشتری", "باع", "تجارة", "تجاره", "ربح", "خسر"] },
];

function verseArabicTokens(verse) {
  const rawTokens = String(verse.arabic || "").match(/[\u0621-\u063a\u0641-\u064a\u0671\u067e\u0686\u06a9\u06af\u06cc]+/g) || [];
  const seen = new Set();
  return rawTokens.map((raw) => ({ raw, key: normalize(raw) })).filter(({ key }) => {
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function translationClauses(verse) {
  const clauses = String(verse.persian || "").replace(/[\[\]]/g, "").split(/[؛.!؟،]/).map((item) => item.trim()).filter((item) => item.length >= 8);
  return [...new Set(clauses)].slice(0, 9);
}

function substantiveArabicTerms(verse, maximum = 6) {
  return verseArabicTokens(verse).filter(({ key }) => key.length >= 3 && !ARABIC_STOPWORDS.has(key)).slice(0, maximum);
}

function studyCapacity(verse, base = 10, extended = 14) {
  return verseArabicTokens(verse).length > 32 || String(verse.persian || "").length > 230 ? extended : base;
}

function sourceExcerptForVerse(verse, maximum = 620) {
  const entry = primaryTafsirEntry(verse);
  if (!entry) return null;
  return {
    text: compactSourceText(entry.text, maximum),
    source: `${entry.source.title}، نسخهٔ ${entry.source.version}`,
  };
}

function structuralMarkers(verse) {
  const words = verseArabicTokens(verse);
  const keys = words.map((item) => item.key);
  const originalFor = (key) => words.find((item) => item.key === key || item.key.endsWith(key))?.raw || key;
  const markers = [];
  const callIndex = keys.findIndex((key) => key === "یا" || key.startsWith("یاایها"));
  if (callIndex >= 0) {
    const addressee = words.slice(callIndex, callIndex + 3).map((item) => item.raw).join(" ");
    markers.push({
      kind: "address",
      text: `صورتِ خطابِ «${addressee}» در متن دیده می‌شود؛ مخاطب را باید از همین عبارت و سیاقِ سوره بازشناخت.`,
      evidence: `شاهد عربی: ${addressee}`,
    });
  }
  const speech = keys.find((key) => ["قل", "قال", "قالوا", "قالت"].includes(key));
  if (speech) markers.push({
    kind: "speech",
    text: `صورتِ گفتار/ابلاغِ «${originalFor(speech)}» در آیه وجود دارد؛ متنِ پس از آن را باید بخشی از گفتار یا ابلاغ دانست، نه افزودهٔ پژوهشگر.`,
    evidence: `شاهد عربی: ${originalFor(speech)}`,
  });
  const commands = words.filter(({ key }) => [...COMMAND_FORMS].some((form) => key === form || (key.length > form.length + 1 && key.endsWith(form)))).slice(0, 3);
  if (commands.length) markers.push({
    kind: "command",
    words: commands.map((item) => item.raw),
    text: `در سطحِ صورتِ زبانی، واژهٔ «${commands.map((item) => item.raw).join("، ")}» با الگوی فعلِ امرِ شناخته‌شده تطبیق دارد؛ مخاطب و دامنهٔ آن باید با ترجمه و سیاق کنترل شود.`,
    evidence: `شاهد عربی: ${commands.map((item) => item.raw).join("، ")}`,
  });
  const negative = words.find(({ key }) => key === "لا" || key === "لم" || key === "لن" || key === "ما");
  if (negative) markers.push({
    kind: "negative",
    text: `صورتِ «${negative.raw}» در آیه، نفی یا مرزبندی را وارد جمله می‌کند؛ اینکه نهیِ عملی است یا نفیِ خبری، باید از ساختمان جمله و تفسیر سنجیده شود.`,
    evidence: `شاهد عربی: ${negative.raw}`,
  });
  const condition = words.find(({ key }) => ["ان", "اذا", "من", "لو", "لولا"].includes(key));
  if (condition) markers.push({
    kind: "condition",
    text: `نشانگرِ «${condition.raw}» امکانِ رابطهٔ شرط/زمینه و نتیجه را در آیه مطرح می‌کند؛ دو سوی رابطه باید در همین آیه یا سیاق نزدیک خوانده شوند.`,
    evidence: `شاهد عربی: ${condition.raw}`,
  });
  const contrast = words.find(({ key }) => ["الا", "بل", "لكن", "لکن"].includes(key));
  if (contrast) markers.push({
    kind: "contrast",
    text: `واژهٔ «${contrast.raw}» در متن، استثنا یا تقابل را برجسته می‌کند؛ بخشِ پیش و پس از آن را نباید از هم جدا خواند.`,
    evidence: `شاهد عربی: ${contrast.raw}`,
  });
  return markers;
}

function nearbyContextItem(verse) {
  const context = getContext(verse);
  const currentIndex = context.findIndex((item) => item.id === verse.id);
  const before = context[currentIndex - 1];
  const after = context[currentIndex + 1];
  if (!before && !after) return null;
  const pieces = [];
  if (before) pieces.push(`پیش از آیه: ${before.reference} — «${compactSourceText(before.persian, 150)}»`);
  if (after) pieces.push(`پس از آیه: ${after.reference} — «${compactSourceText(after.persian, 150)}»`);
  return { text: pieces.join("؛ "), evidence: "شاهد: پنجرهٔ پیش/خود/پسِ همین سوره" };
}

function numberedNoteItems(verse) {
  const clauses = translationClauses(verse);
  const terms = substantiveArabicTerms(verse);
  const markers = structuralMarkers(verse);
  const items = clauses.map((clause) => ({
    text: `در ترجمهٔ فارسیِ آیه، این گزاره آمده است: «${clause}».`,
    evidence: `شاهد: ترجمهٔ فارسیِ ${verse.reference}`,
  }));
  if (terms.length) items.push({
    text: `واژه‌های قابل مشاهده در متن عربی: «${terms.map((item) => item.raw).join("»، «")}». این‌ها نقطهٔ شروعِ بررسیِ واژگانی‌اند، نه فهرستِ معنای نهایی.`,
    evidence: `شاهد عربی: ${terms.map((item) => item.raw).join("، ")}`,
  });
  markers.forEach((marker) => items.push({ text: marker.text, evidence: marker.evidence }));
  const context = nearbyContextItem(verse);
  if (context) items.push(context);
  const source = sourceExcerptForVerse(verse);
  if (source) items.push({
    text: `نقلِ تفسیریِ بدون بازنویسی: «${source.text}»`,
    evidence: `منبع: ${source.source}`,
  });
  return items.slice(0, studyCapacity(verse));
}

function numberedMessageItems(verse) {
  const clauses = translationClauses(verse);
  const markers = structuralMarkers(verse);
  const items = clauses.map((clause) => ({
    text: `گزارهٔ صریحِ آیه برای خوانش پیام: «${clause}».`,
    evidence: `شاهد: ترجمهٔ فارسیِ ${verse.reference}`,
  }));
  markers.filter((marker) => ["address", "speech", "command", "negative", "condition", "contrast"].includes(marker.kind)).forEach((marker) => {
    items.push({ text: `جهتِ پیام در سطحِ ساختار متن: ${marker.text}`, evidence: marker.evidence });
  });
  const context = nearbyContextItem(verse);
  if (context) items.push({ text: `برای محدودکردنِ پیام به سیاق نزدیک: ${context.text}`, evidence: context.evidence });
  const source = sourceExcerptForVerse(verse, 460);
  if (source) items.push({ text: `شرحِ منبع‌دارِ مرتبط با خوانش پیام: «${source.text}»`, evidence: `منبع: ${source.source}` });
  return items.slice(0, studyCapacity(verse));
}

function numberedPrincipleItems(verse) {
  const markers = structuralMarkers(verse);
  const clauses = translationClauses(verse);
  const items = [];
  markers.filter((marker) => marker.kind === "command").forEach((marker) => {
    items.push({
      text: `این اصل فقط در حدّ صورتِ آیه ثبت می‌شود: ${marker.text} ترجمهٔ آیه را کنار این صورت بخوانید: «${clauses[0] || verse.persian}».`,
      evidence: `${marker.evidence} · شاهد ترجمه: ${verse.reference}`,
    });
  });
  markers.filter((marker) => marker.kind === "negative").forEach((marker) => {
    items.push({
      text: `اصلِ احتیاط در خوانش: ${marker.text} تا نوعِ «لا/لم/لن/ما» روشن نشده، آن را بی‌دلیل به یک قاعدهٔ رفتاریِ عام تبدیل نکنید.`,
      evidence: marker.evidence,
    });
  });
  markers.filter((marker) => marker.kind === "condition").forEach((marker) => {
    items.push({
      text: `اصلِ توجه به شرط و نتیجه: ${marker.text} در کاربرد زندگی، تنها همان رابطهٔ تصریح‌شده را ثبت کنید و قیدهای آن را حذف نکنید.`,
      evidence: marker.evidence,
    });
  });
  if (!items.length) items.push({
    text: "فیلتر متن‌پایهٔ برنامه در این تک‌آیه صورتِ روشنِ امر، نفی/نهی یا شرطِ قابل تبدیل به «اصل زندگی» نیافت؛ برای پرهیز از ساختنِ اصلِ بی‌شاهد، جایگاه‌های باقی‌مانده خالی می‌مانند.",
    evidence: `شاهد بررسی‌شده: متن عربی و ترجمهٔ ${verse.reference}`,
  });
  const source = sourceExcerptForVerse(verse, 420);
  if (source) items.push({
    text: `برای آزمونِ هر اصل، این نقلِ منبع‌دار را نیز بخوانید: «${source.text}»`,
    evidence: `منبع: ${source.source}`,
  });
  return items.slice(0, 20);
}

function numberedStudyList(items, label, capacity, className = "") {
  return `<div class="numbered-study-list ${className}" aria-label="${escapeHTML(label)}">${items.map((item, index) => `<article><h4>${escapeHTML(label)} ${faNumber(index + 1)}</h4><p>${escapeHTML(item.text)}</p>${item.evidence ? `<small>${escapeHTML(item.evidence)}</small>` : ""}</article>`).join("")}</div><p class="study-capacity">${faNumber(items.length)} موردِ متن‌پایه از ظرفیتِ ${faNumber(capacity)} ${escapeHTML(label)} نمایش داده شد. خانه‌های باقی‌مانده فقط با شاهدِ دقیقِ آیه یا منبع تکمیل می‌شوند.</p>`;
}

function inlineStudyBody(verse, tab) {
  const source = inlineTafsirEvidence(verse, 420);
  if (tab === "notes") return `<p class="inline-study-intro">هر نکته به ترجمه، ساختِ لفظی، سیاق نزدیک یا نقلِ دقیقِ یک منبع تکیه دارد؛ مواردی که شاهد ندارند عمداً تولید نمی‌شوند.</p>${numberedStudyList(numberedNoteItems(verse).slice(0, 5), "نکته", studyCapacity(verse), "compact")}${source}`;
  if (tab === "messages") return `<p class="inline-study-intro">پیام‌ها فقط گزاره‌ها و جهت‌های قابل مشاهدهٔ همین آیه‌اند؛ آن‌ها فتوا یا جانشینِ تفسیر نیستند.</p>${numberedStudyList(numberedMessageItems(verse).slice(0, 5), "پیام", studyCapacity(verse), "compact")}${source}`;
  return `<p class="inline-study-intro">اصل‌ها تنها از صورتِ صریحِ امر، نفی/نهی یا شرط ساخته می‌شوند. برای جلوگیری از تعمیمِ بی‌شاهد، ظرفیتِ خالی به‌صورت خودکار پُر نمی‌شود.</p>${numberedStudyList(numberedPrincipleItems(verse).slice(0, 5), "اصل", 20, "compact")}${source}`;
}
function meaningfulTokens(value = "") {
  return [...new Set(normalize(value).split(" ").filter((token) => token.length >= 3 && !ARABIC_STOPWORDS.has(token) && !PERSIAN_STOPWORDS.has(token)))];
}

function proposalEvidenceText(verse) {
  return `${verse.arabic} ${verse.persian} ${tafsirEntries(verse).map((entry) => entry.text).join(" ")}`;
}

function validateVerseProposal(verse, claim, witness) {
  const cleanClaim = String(claim || "").trim();
  const cleanWitness = String(witness || "").trim();
  if (cleanClaim.length < 18) return { accepted: false, reason: "متنِ پیشنهاد باید دست‌کم ۱۸ نویسه داشته باشد تا قابل ارزیابی باشد." };
  if (cleanWitness.length < 3) return { accepted: false, reason: "برای بررسی، یک عبارتِ دقیق از آیه، ترجمه یا تفسیرِ فعال وارد کنید." };
  const evidence = normalize(proposalEvidenceText(verse));
  const normalizedWitness = normalize(cleanWitness);
  if (!normalizedWitness || !evidence.includes(normalizedWitness)) {
    return { accepted: false, reason: "رد شد: عبارتِ شاهد، به‌صورت دقیق در متن آیه، ترجمه یا تفاسیرِ بارگیری‌شدهٔ همین آیه یافت نشد." };
  }
  const evidenceTerms = new Set(meaningfulTokens(proposalEvidenceText(verse)));
  const overlap = meaningfulTokens(cleanClaim).filter((token) => evidenceTerms.has(token));
  if (!overlap.length) {
    return { accepted: false, reason: "رد شد: متنِ پیشنهاد هیچ واژهٔ محتواییِ مشترک با شاهدهای همین آیه ندارد. یک واژهٔ آیه/ترجمه را در توضیح بیاورید." };
  }
  return { accepted: true, overlap };
}

function verseProposalsFor(verse, kind) {
  return state.verseProposals.filter((item) => item.verseId === verse.id && item.kind === kind);
}

function proposalKindLabel(kind) {
  return { notes: "نکته", principles: "اصل", messages: "پیام" }[kind] || "پیشنهاد";
}

function proposalContributionForm(verse, kind) {
  const label = proposalKindLabel(kind);
  const accepted = verseProposalsFor(verse, kind);
  const saved = accepted.length ? `<div class="user-proposal-list">${accepted.map((item, index) => `<article><h4>${escapeHTML(label)} کاربر ${faNumber(index + 1)}</h4><p>${escapeHTML(item.claim)}</p><small>شاهدِ پذیرفته‌شده: «${escapeHTML(item.witness)}» · فقط روی همین دستگاه ذخیره شده است.</small><button type="button" data-delete-proposal="${escapeHTML(item.id)}">حذف</button></article>`).join("")}</div>` : "";
  return `<section class="proposal-workspace"><p class="eyebrow">پیشنهادِ پژوهشگر</p><h4>${escapeHTML(label)} متن‌پایهٔ خود را اضافه کنید</h4><p>فیلتر محلی فقط وقتی پیشنهاد را می‌پذیرد که «شاهدِ دقیق» در متن عربی، ترجمه یا تفسیرِ همین آیه یافت شود و توضیح شما دست‌کم یک واژهٔ محتواییِ مشترک داشته باشد. این پذیرش، داوری تفسیری یا تأیید علمی نیست.</p>${saved}<form data-proposal-form data-proposal-kind="${escapeHTML(kind)}" data-proposal-verse-id="${escapeHTML(verse.id)}"><label>متن ${escapeHTML(label)}<textarea name="claim" maxlength="1600" required placeholder="صورت‌بندیِ پیشنهادیِ خود را بنویسید؛ یک واژهٔ آیه یا ترجمه را نیز در متن بیاورید."></textarea></label><label>شاهدِ دقیق از آیه، ترجمه یا تفسیر فعال<input name="witness" maxlength="600" required placeholder="برای نمونه، یک عبارتِ کوتاه را عیناً وارد کنید" /></label><button type="submit">بررسی و ثبتِ محلی</button><output class="proposal-status" aria-live="polite"></output></form></section>`;
}

function submitVerseProposal(form) {
  const verse = state.selected;
  const status = form.querySelector(".proposal-status");
  if (!verse || form.dataset.proposalVerseId !== verse.id) return;
  const claim = form.querySelector("[name=claim]")?.value || "";
  const witness = form.querySelector("[name=witness]")?.value || "";
  const validation = validateVerseProposal(verse, claim, witness);
  if (!validation.accepted) {
    status.textContent = validation.reason;
    status.dataset.status = "rejected";
    return;
  }
  state.verseProposals.unshift({
    id: `${verse.id}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    verseId: verse.id,
    kind: form.dataset.proposalKind,
    claim: claim.trim().slice(0, 1600),
    witness: witness.trim().slice(0, 600),
    sharedTerms: validation.overlap,
    savedAt: new Date().toISOString(),
  });
  persistVerseProposals();
  renderDetailPanel();
}

function deleteVerseProposal(id) {
  state.verseProposals = state.verseProposals.filter((item) => item.id !== id);
  persistVerseProposals();
  renderDetailPanel();
}

function inlineStudyContent(verse, tab) {
  return `<div class="inline-study-content" data-inline-study="${escapeHTML(tab)}">${inlineStudyBody(verse, tab)}<button class="inline-open-detail" type="button" data-open-verse="${escapeHTML(verse.id)}">پروندهٔ کامل آیه، سیاق و تفاسیر ←</button></div>`;
}

function verseCard(verse) {
  const primaryEvidence = verse.evidence.slice(0, 2).map((item) => `${item.label} · ${item.source}`).join("، ");
  const tabs = [["notes", "نکات مهم آیه"], ["messages", "پیام‌های آیه"], ["principles", "اصول و قواعد زندگی"], ["foundations", "مبانی اندیشهٔ قرآنی"]];
  const expanded = state.inlineStudy.verseId === verse.id;
  return `<article class="verse-card" data-verse-id="${escapeHTML(verse.id)}">
    <div class="verse-inline-tabs" role="tablist" aria-label="مطالعهٔ سریعِ ${escapeHTML(verse.reference)}">${tabs.map(([id, label]) => `<button type="button" data-inline-tab="${id}" data-inline-verse-id="${escapeHTML(verse.id)}" class="${expanded && state.inlineStudy.tab === id ? "active" : ""}" role="tab">${label}</button>`).join("")}</div>
    ${expanded ? inlineStudyContent(verse, state.inlineStudy.tab) : ""}
    <button class="verse-open" type="button" data-open-verse="${escapeHTML(verse.id)}">
      <span class="verse-head"><span class="verse-reference">${escapeHTML(verse.reference)} · ${escapeHTML(verse.revelation)}</span><span class="verse-type ${verse.type}">${typeLabel(verse.type)}</span></span>
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
    const directEntry = source.verses?.[surah]?.[ayah];
    const contentId = source.ayahMapping?.[surah]?.[ayah];
    const entry = directEntry || source.contents?.[String(contentId)];
    return entry?.text ? { source, text: entry.text, footnotes: entry.footnotes || "", referenceRange: entry.referenceRange || "" } : null;
  }).filter(Boolean);
}

function tafsirCitation(source) {
  return `${source.title}، ${source.author}، نسخهٔ ${source.version}، ${source.source}`;
}

function sourceEvidenceNotice(verse) {
  const entries = tafsirEntries(verse);
  return entries.length ? `<p class="source-availability">برای این آیه ${faNumber(entries.length)} متن تفسیریِ منبع‌دار موجود است؛ هنگام نتیجه‌گیری، آن‌ها را در تب «تفاسیر منبع‌دار» با انتساب کامل مقایسه کنید.</p>` : "";
}

function tafsirCatalogCards() {
  const requested = state.tafsirCatalog.find((collection) => collection.id === "requested-comparative");
  if (!requested?.items?.length) return "";
  return `<section class="tafsir-catalog"><p class="eyebrow">فهرستِ مقایسه‌ایِ درخواستی</p><h3>${escapeHTML(requested.title)}</h3><p class="reading-notice">متنِ دیجیتالِ یک اثر فقط وقتی ذیل آیه نشان داده می‌شود که نسخهٔ دقیق، انتساب و مجوز یا شرایط بازنشرِ آن ثبت شده باشد. «موجود بودن در اینترنت» به‌تنهایی مجوز کپی یا انتسابِ متن نیست.</p><div class="tafsir-catalog-grid">${requested.items.map((item) => { const active = item.status === "available"; return `<article class="tafsir-catalog-card ${active ? "available" : ""}"><h4>${escapeHTML(item.title)}</h4><p>${escapeHTML(item.author)}</p><small>${escapeHTML(item.language)} · ${escapeHTML(item.era)}</small><b>${active ? "متن آیه‌به‌آیه فعال" : item.status === "needs-permission" ? "نیازمند اجازهٔ بازنشر" : "نیازمند نسخهٔ محقق و بازبینی‌شده"}</b><span>${active ? "متن کاملِ این اثر در کارت‌های تفسیریِ بالای همین بخش قابل خواندن است." : "برای این آیه هنوز متنِ مجاز و نسخه‌دارِ این اثر وارد نشده است."}</span><em>${escapeHTML(item.basis)}</em></article>`; }).join("")}</div></section>`;
}

function detailPanelTafsir(verse) {
  const entries = tafsirEntries(verse);
  const catalogue = tafsirCatalogCards();
  const pending = pendingTafsirSources();
  const loading = pending.length ? `<p class="source-availability">در حال آماده‌کردنِ ${faNumber(pending.length)} تفسیرِ کاملِ تکمیلی برای این آیه هستیم؛ متن‌های سبک‌تر هم‌اکنون در دسترس‌اند.</p>` : "";
  if (!entries.length) return `<section class="detail-panel tafsir-panel"><p class="eyebrow">منابع تفسیری</p><h3>متن منبع‌دارِ فعال موقتاً بارگیری نشد.</h3><p>هستهٔ جست‌وجو همچنان محلی است؛ با اتصال بعدی، متنِ بدون‌ویرایشِ منابع دوباره بارگیری می‌شود.</p>${loading}${catalogue}</section>`;
  return `<section class="detail-panel tafsir-panel"><p class="eyebrow">تفاسیرِ منبع‌دارِ آیه</p><h3>متنِ کامل، انتساب، نسخه و پیوندِ دقیق</h3><p class="reading-notice">متن‌های فعال زیر بدون خلاصه‌سازی یا بازنویسیِ قرآن‌پژوهه نمایش داده می‌شوند. اختلاف زبان و اثر به‌معنای همسان‌بودنِ تفسیرها نیست؛ برای پژوهش، هر اثر را جداگانه بخوانید.</p>${loading}${entries.map(({ source, text, footnotes, referenceRange }) => `<details class="source-card" ${source.id === "fa_qe_persian_mokhtasar" ? "open" : ""}><summary class="source-card-head"><div><h4>${escapeHTML(source.title)}</h4><p>${escapeHTML(source.author)}</p></div><a href="${escapeHTML(source.sourceUrl)}" target="_blank" rel="noreferrer">منبع ↗</a></summary><p class="source-citation">${escapeHTML(tafsirCitation(source))}${referenceRange ? ` · توضیحِ منبع برای بازهٔ ${escapeHTML(referenceRange)}` : ""}</p><div class="source-text" lang="${escapeHTML(source.language)}" dir="rtl">${escapeHTML(text)}</div>${footnotes ? `<div class="source-footnotes"><b>پانویسِ منبع</b>${escapeHTML(footnotes)}</div>` : ""}</details>`).join("")}${catalogue}</section>`;
}

function detailPanelNotes(verse) {
  const items = numberedNoteItems(verse);
  return `<section class="detail-panel numbered-panel"><p class="eyebrow">نکات مهم آیه</p><h3>نکته‌های شماره‌دار با شاهدِ آیه</h3><p class="reading-notice">هر نکته یا به عبارتِ ترجمه، واژه/ساختِ قابل مشاهدهٔ عربی، سیاق نزدیک یا نقلِ دقیقِ منبع تکیه دارد. برنامه برای پُر کردنِ تعداد، نکتهٔ بی‌شاهد نمی‌سازد.</p>${numberedStudyList(items, "نکته", studyCapacity(verse))}${proposalContributionForm(verse, "notes")}</section>`;
}

function detailPanelFoundations(verse) {
  const items = numberedPrincipleItems(verse);
  return `<section class="detail-panel numbered-panel"><p class="eyebrow">اصول زندگی و مبانی</p><h3>اصل‌های شماره‌دارِ متن‌پایه</h3><p class="reading-notice">ظرف این بخش تا ۲۰ اصل است؛ فقط جایی که صورتِ امر، نفی/نهی یا شرط در خود آیه دیده می‌شود، اصل نوشته می‌شود. گزارش‌های روایی و خبری به‌زور به دستورِ زندگی تبدیل نمی‌شوند.</p>${numberedStudyList(items, "اصل", 20)}${proposalContributionForm(verse, "principles")}</section>`;
}

function quranWordOccurrence(word) {
  if (!word?.key) return 0;
  return state.corpus.filter((record) => record.arabicNormalized.split(" ").includes(word.key)).length;
}

function frameAddressee(verse) {
  const words = verseArabicTokens(verse);
  const at = words.findIndex((word) => word.key === "یا" || word.key.startsWith("یاایها"));
  return at >= 0 ? words.slice(at, at + 3).map((word) => word.raw).join(" ") : "در همین تک‌آیه با نشانگرِ خطابِ صریح مشخص نشده است";
}

function schemaMatches(verse) {
  const words = verseArabicTokens(verse);
  return COGNITIVE_SCHEMAS.map((schema) => ({
    ...schema,
    hits: words.filter((word) => schema.terms.some((term) => word.key === normalize(term) || word.key.includes(normalize(term)))).map((word) => word.raw),
  })).filter((schema) => schema.hits.length);
}

function semanticModelCards(verse) {
  const terms = substantiveArabicTerms(verse, 7);
  const primary = terms[0];
  const markers = structuralMarkers(verse);
  const frameType = markers.some((marker) => marker.kind === "command") ? "دعوت/دستور در سطح صورتِ زبانی"
    : markers.some((marker) => marker.kind === "speech") ? "گفتار یا ابلاغ"
      : markers.some((marker) => marker.kind === "condition") ? "رابطهٔ شرط و زمینه"
        : "گزارش یا توصیف؛ تشخیصِ تفسیریِ ژانر در اینجا ادعا نمی‌شود";
  const schemas = schemaMatches(verse);
  const source = sourceExcerptForVerse(verse, 360);
  const izutsu = primary
    ? `<ul><li><b>واژهٔ بررسی:</b> «${escapeHTML(primary.raw)}»؛ این برچسب «کانون قطعی» نیست، بلکه نقطهٔ شروعِ تحلیل است.</li><li><b>هم‌نشین‌های درون‌آیه:</b> ${escapeHTML(terms.slice(1).map((item) => `«${item.raw}»`).join("، ") || "واژهٔ محتواییِ دیگری با فیلتر سطحی جدا نشد.")}</li><li><b>توزیع قابل شمارش:</b> صورتِ نرمال‌شدهٔ این واژه در ${faNumber(quranWordOccurrence(primary))} آیه از پیکرهٔ محلی دیده می‌شود؛ کاربردهای آن باید جداگانه مقایسه شوند.</li><li><b>تقابل/مرزبندی در خود آیه:</b> ${escapeHTML(markers.filter((item) => ["negative", "contrast"].includes(item.kind)).map((item) => item.evidence).join("؛ ") || "تقابلِ صریحی با فیلتر سطحی ثبت نشد.")}</li></ul>`
    : `<p>برای مدل ایزوتسو، واژهٔ محتواییِ قابل اتکایی با فیلتر سطحی جدا نشد؛ از نسبت‌دادنِ میدان معناییِ آماده به این آیه خودداری می‌شود.</p>`;
  const fillmore = `<ul><li><b>نوعِ صحنهٔ زبانی:</b> ${escapeHTML(frameType)}</li><li><b>مخاطبِ صریح:</b> ${escapeHTML(frameAddressee(verse))}</li><li><b>کنش/رابطهٔ قابل مشاهده:</b> ${escapeHTML(markers.map((item) => item.evidence).join("؛ ") || "در این لایه فقط متن و ترجمه ثبت شده‌اند؛ نقش‌های پنهان استنباط نمی‌شوند.")}</li><li><b>موضوعِ گفتار:</b> ${escapeHTML(translationClauses(verse)[0] || verse.persian)}</li></ul>`;
  const cognitive = schemas.length
    ? `<ul>${schemas.map((schema) => `<li><b>${escapeHTML(schema.title)}:</b> واژه‌های ورودیِ مدل در آیه: ${escapeHTML(schema.hits.map((word) => `«${word}»`).join("، "))}. این فقط فعال‌شدنِ طرحواره بر پایهٔ واژه است؛ استعاره یا نتیجهٔ اعتقادیِ نهایی نیست.</li>`).join("")}</ul>`
    : `<p>در واژه‌های این آیه، یکی از طرحواره‌های از پیش تعریف‌شدهٔ مسیر، نور/تاریکی، ظرف، تراز، بالا/پایین یا دادوستد به‌صورت لفظی نیامد؛ مدل شناختی در این مرحله خالی می‌ماند تا تصویرسازیِ بدون شاهد تولید نشود.</p>`;
  const sourceFootnote = source ? `<p class="semantic-source"><b>نقلِ کنترل:</b> «${escapeHTML(source.text)}»<small>${escapeHTML(source.source)}</small></p>` : "";
  return `<div class="semantic-model-grid"><section class="semantic-model-card"><p class="eyebrow">مدل ایزوتسو</p><h4>واژهٔ بررسی، هم‌نشینی و توزیع</h4>${izutsu}</section><section class="semantic-model-card"><p class="eyebrow">مدل فیلمور</p><h4>قابِ رویداد و نقش‌های آشکار</h4>${fillmore}</section><section class="semantic-model-card"><p class="eyebrow">معناشناسی شناختی</p><h4>طرحواره‌های تصویریِ لفظاً فعال</h4>${cognitive}</section></div>${sourceFootnote}`;
}

function detailPanelFramework(verse) {
  return `<section class="detail-panel semantic-framework-panel"><p class="eyebrow">چارچوب معنایی</p><h3>سه مدلِ معناشناختی با دادهٔ همین آیه</h3><p class="reading-notice">این بخش نتیجهٔ تفسیریِ قطعی نیست. هر مدل فقط داده‌های قابل مشاهدهٔ آیه را در قالبِ خودش سازمان می‌دهد: واژه و هم‌نشینی در ایزوتسو، صحنه و نقش در فیلمور، و طرحوارهٔ لفظاً فعال در معناشناسی شناختی.</p>${semanticModelCards(verse)}</section>`;
}

function detailPanelMessages(verse) {
  const items = numberedMessageItems(verse);
  return `<section class="detail-panel numbered-panel"><p class="eyebrow">پیام‌های آیه</p><h3>پیام‌های شماره‌دار، مقید به نص و سیاق</h3><p class="reading-notice">پیام‌ها از گزاره‌های صریحِ ترجمه، جهتِ گفتارِ عربی، سیاق نزدیک و نقلِ منبع استخراج می‌شوند. نتیجه‌ای که در این شواهد نیست، به آیه افزوده نمی‌شود.</p>${numberedStudyList(items, "پیام", studyCapacity(verse))}${proposalContributionForm(verse, "messages")}</section>`;
}
function detailPanelContext(verse) {
  const context = getContext(verse);
  return `<section class="detail-panel"><p class="eyebrow">آیه در سیاق سوره</p><h3>پیش و پسِ آیه را کنار هم بخوانید.</h3>${sourceEvidenceNotice(verse)}<p>پنجرهٔ خطیِ زیر جای مطالعهٔ کامل سوره را نمی‌گیرد، اما دادهٔ لازم برای پرهیز از بریده‌خوانی را نشان می‌دهد. برای جزئیاتِ توزیع و پرسش‌ها، «فهم آیه در سیاق» در صفحهٔ پیشین را باز کنید.</p>
    <div class="context-grid">${context.map((item) => `<button class="context-verse ${item.id === verse.id ? "current" : ""}" data-context-id="${escapeHTML(item.id)}" type="button"><b>${escapeHTML(item.reference)}${item.id === verse.id ? " · آیهٔ پژوهش" : ""}</b><p class="context-arabic" lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><p>${escapeHTML(item.persian)}</p></button>`).join("")}</div></section>`;
}

function detailPanelQuran(verse) {
  const sameSurah = state.matches.filter((item) => item.surah === verse.surah && item.id !== verse.id).slice(0, 5);
  const surahs = new Set(state.matches.map((item) => item.surah)).size;
  const distributions = evidenceDistribution(verse).filter((item) => item.count);
  return `<section class="detail-panel"><p class="eyebrow">آیه در نسبت با کل قرآن</p><h3>جای این آیه در مسیرِ همین پژوهش</h3>
    ${sourceEvidenceNotice(verse)}
    <ul class="study-list"><li><b>پوشش پرسش فعلی</b>${faNumber(state.matches.length)} آیه در ${faNumber(surahs)} سوره، بر پایهٔ واژه‌های فعالِ همین جست‌وجو بازیابی شده‌اند.</li>${distributions.map((item) => `<li><b>توزیعِ «${escapeHTML(item.label)}»</b>${faNumber(item.count)} آیه در ${faNumber(item.surahs)} سوره؛ مواضع نخست: ${escapeHTML(item.references.join("، "))}${item.count > item.references.length ? " …" : ""}</li>`).join("")}<li><b>مرز نتیجه</b>این شمارش، اهمیت تفسیری یا همهٔ ارتباط‌های ممکن میان آیات را رتبه‌بندی نمی‌کند؛ سیاق و منابع تفسیریِ ارجاع‌دار لازم‌اند.</li></ul>
    ${sameSurah.length ? `<div class="related-verses">${sameSurah.map((item) => `<button class="related-verse" type="button" data-related-id="${escapeHTML(item.id)}">${escapeHTML(item.reference)} · ${escapeHTML(item.evidence[0]?.label || "شاهد")}</button>`).join("")}</div>` : "<p>در مسیر فعلی، شاهدِ دیگری از همین سوره بازیابی نشده است.</p>"}</section>`;
}

function detailPanelNotebook(verse) {
  const saved = state.notebook.find((item) => item.id === verse.id);
  return `<section class="detail-panel"><p class="eyebrow">دفتر پژوهش، فقط روی همین دستگاه</p><h3>یادداشت و منبع خود را ثبت کنید.</h3><p>برای تفسیر یا منبع بیرونی، نام اثر، مؤلف، جلد و صفحه را دقیق بنویسید.</p>
    <textarea id="verse-note" class="note-area" placeholder="برداشت موقت، پرسش، یا ارجاع منبع…">${escapeHTML(saved?.note || "")}</textarea>
    <div class="note-actions"><button id="save-note" type="button">ذخیرهٔ یادداشت</button><span id="note-status"></span></div></section>`;
}

function renderDetailPanel() {
  const verse = state.selected;
  if (!verse) return;
  if (state.detailTab === "tafsir" && pendingTafsirSources().length) {
    ensureExtendedTafsirSources().then(() => {
      if (state.detailTab === "tafsir" && state.selected?.id === verse.id) renderDetailPanel();
    });
  }
  const panels = {
    notes: detailPanelNotes,
    foundations: detailPanelFoundations,
    framework: detailPanelFramework,
    messages: detailPanelMessages,
    context: detailPanelContext,
    quran: detailPanelQuran,
    tafsir: detailPanelTafsir,
    notebook: detailPanelNotebook,
  };
  $("#detail-panels").innerHTML = (panels[state.detailTab] || detailPanelNotes)(verse);
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

function topicHitsForSurah(surah, layer) {
  const records = surahRecords(surah);
  return state.concepts.map((concept) => {
    const terms = layer === "direct" ? concept.equivalents : concept.related;
    const count = records.filter((record) => (terms || []).some(([term]) => record.arabicNormalized.includes(normalize(term)))).length;
    return { title: concept.title, count };
  }).filter((item) => item.count).sort((a, b) => b.count - a.count || a.title.localeCompare(b.title, "fa"));
}

function openLibrary(mode, shouldNavigate = true) {
  state.libraryMode = mode;
  const surahs = [...new Map(state.corpus.map((record) => [record.surah, record])).values()];
  if (mode === "surahs") {
    $("#library-title").textContent = "پژوهش در ۱۱۴ سوره";
    $("#library-description").textContent = "هر سوره یک پروندهٔ مستقل دارد: نکات متن‌محور، پرسش‌های پیام، موضوعات صریحِ واژگانی و پیوندهای مرتبط. این برچسب‌ها جای تفسیر منبع‌دار را نمی‌گیرند.";
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
  state.surahTab = "notes";
  renderSurah();
  if (shouldNavigate) navigate("surah", String(surahNumber));
  else showScreen("surah", String(surahNumber));
}

function surahTopicList(items, empty) {
  return items.length ? `<div class="topic-hit-list">${items.map((item) => `<span><b>${escapeHTML(item.title)}</b> · ${faNumber(item.count)} آیه</span>`).join("")}</div>` : `<p>${escapeHTML(empty)}</p>`;
}

function renderSurah() {
  const surah = state.selectedSurah;
  if (!surah) return;
  const direct = topicHitsForSurah(surah.number, "direct");
  const related = topicHitsForSurah(surah.number, "related");
  $("#surah-reference").textContent = `سورهٔ ${faNumber(surah.number)} · ${surah.revelation} · ${faNumber(surah.verses)} آیه`;
  $("#surah-title").textContent = surah.name;
  $("#surah-description").textContent = "این پروندهٔ نخستین، موضوع‌ها را فقط بر پایهٔ حضور واژه‌های عربیِ واژه‌نامه نشان می‌دهد. لایهٔ پیام و نکتهٔ تفسیری پس از ورود منابعِ چندگانه با ارجاع دقیق تکمیل می‌شود.";
  $$("[data-surah-tab]").forEach((button) => button.classList.toggle("active", button.dataset.surahTab === state.surahTab));
  const panels = {
    notes: `<section class="detail-panel"><p class="eyebrow">نکات سوره</p><h3>پروندهٔ متن‌محورِ سورهٔ ${escapeHTML(surah.name)}</h3><ul class="study-list"><li><b>شناسهٔ متن</b>${faNumber(surah.verses)} آیه و طبقه‌بندیِ ${escapeHTML(surah.revelation)} در فرادادهٔ پیکره ثبت شده است.</li><li><b>روش این پرونده</b>موضوع‌ها از تطابق واژه‌های عربیِ شفاف به‌دست می‌آیند؛ هنوز «نکتهٔ تفسیری» یا «مقصد سوره» به‌صورت بی‌منبع به سوره نسبت داده نشده است.</li></ul></section>`,
    messages: `<section class="detail-panel"><p class="eyebrow">پیام‌های قابل بررسی</p><h3>پرسش‌های پژوهشگر برای خواندن سوره</h3><ul class="study-list"><li><b>پرسش ساختاری</b>آغاز، گره‌ها و پایان سوره چه نسبتی با یکدیگر دارند؟</li><li><b>پرسش واژگانی</b>واژه‌های پرتکرارِ زیر در چه نقش و سیاقی آمده‌اند؟</li><li><b>پرسش منبع</b>برای هر پیام پیشنهادی، کدام منبع تفسیریِ دارای ارجاع از آن پشتیبانی می‌کند؟</li></ul></section>`,
    direct: `<section class="detail-panel"><p class="eyebrow">فهرست موضوعیِ صریح</p><h3>مفهوم‌هایی با شاهدِ واژگانیِ عربی در این سوره</h3>${surahTopicList(direct, "برای واژه‌نامهٔ فعلی، شاهد صریحی در این سوره ثبت نشده است.")}</section>`,
    related: `<section class="detail-panel"><p class="eyebrow">موضوعات همسو و مرتبط</p><h3>پیوندهایی که باید در سیاق سنجیده شوند</h3><p class="reading-notice">این‌ها موضوعات غیرمستقیم‌اند؛ حضورشان ادعای هم‌معنایی، مقصد سوره یا نتیجهٔ تفسیری نیست.</p>${surahTopicList(related, "برای واژه‌نامهٔ فعلی، پیوند مرتبطی در این سوره ثبت نشده است.")}</section>`,
  };
  $("#surah-panels").innerHTML = panels[state.surahTab];
}

function resultVerse(record, evidence, type = "exact") {
  return { ...record, evidence, type, score: 0 };
}

function openSurahVerses() {
  const surah = state.selectedSurah;
  if (!surah) return;
  state.query = `سورهٔ ${surah.name}`;
  state.concept = null;
  state.terms = [];
  state.matches = surahRecords(surah.number).map((record) => resultVerse(record, [{ label: "آیهٔ این سوره", type: "exact", source: "پیکرهٔ قرآن", origin: "پروندهٔ سوره" }]));
  state.shown = PAGE_SIZE;
  state.filter = "all";
  renderResults();
  navigate("results");
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

$("#verse-list").addEventListener("click", (event) => {
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

$("#detail-panels").addEventListener("click", (event) => {
  const contextButton = event.target.closest("[data-context-id]");
  if (contextButton) return openVerse(contextButton.dataset.contextId);
  const relatedButton = event.target.closest("[data-related-id]");
  if (relatedButton) return openVerse(relatedButton.dataset.relatedId);
  const deleteProposal = event.target.closest("[data-delete-proposal]");
  if (deleteProposal) return deleteVerseProposal(deleteProposal.dataset.deleteProposal);
  if (event.target.closest("#save-note")) saveNote();
});

$("#detail-panels").addEventListener("submit", (event) => {
  const form = event.target.closest("[data-proposal-form]");
  if (!form) return;
  event.preventDefault();
  submitVerseProposal(form);
});

$$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));
$("#brand-home").addEventListener("click", () => navigate("search"));
$("#save-verse").addEventListener("click", saveCurrentVerse);

$("#open-method").addEventListener("click", () => $("#method-dialog").showModal());
$("#open-sources").addEventListener("click", () => $("#sources-dialog").showModal());
window.addEventListener("popstate", restoreFromHistory);

if ("serviceWorker" in navigator && /^(https?:)$/.test(location.protocol)) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}

loadData().then(() => {
  if (!location.hash) history.replaceState({ screen: "search" }, "", location.pathname);
  restoreFromHistory();
}).catch((error) => {
  $("#search-status").textContent = error.message || "بارگیری داده‌ها ناموفق بود.";
});
