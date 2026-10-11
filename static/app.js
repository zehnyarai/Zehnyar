const CORPUS_URL = "static/offline-corpus.json";
const LEXICON_URL = "static/concept-lexicon.json";
const STORY_INDEX_URL = "static/story-index.json";
const TOPIC_CATALOG_URL = "static/topic-catalog.json";
const NOTEBOOK_KEY = "zehnyar-verse-notebook-v2";
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
  stories: [],
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
  selected: null,
  detailTab: "notes",
  searchTranslations: false,
  notebook: loadNotebook(),
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
  const [corpusResponse, lexiconResponse, storyResponse, catalogResponse] = await Promise.all([fetch(CORPUS_URL), fetch(LEXICON_URL), fetch(STORY_INDEX_URL), fetch(TOPIC_CATALOG_URL)]);
  if (!corpusResponse.ok || !lexiconResponse.ok || !storyResponse.ok || !catalogResponse.ok) throw new Error("پیکرهٔ محلی یا فهرست پژوهش در دسترس نیست.");
  const corpus = await corpusResponse.json();
  state.lexicon = await lexiconResponse.json();
  const catalog = await catalogResponse.json();
  state.concepts = [...(state.lexicon.concepts || []), ...(catalog.concepts || [])];
  state.topicCategories = catalog.categories || [];
  state.stories = (await storyResponse.json()).stories || [];
  state.corpus = corpus.verses.map(recordFromTuple);
  state.recordById = new Map(state.corpus.map((record) => [record.id, record]));
  $("#result-corpus").textContent = `${faNumber(state.corpus.length)} آیه`;
  renderStarters();
}

function renderStarters() {
  const priority = ["محبت و عشق", "عدالت", "رحمت", "خانواده", "علم و اندیشه", "آزادی و اختیار", "دعا و عبادت", "توبه"];
  const concepts = [...state.concepts].sort((a, b) => {
    const aIndex = priority.indexOf(a.title);
    const bIndex = priority.indexOf(b.title);
    return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex);
  });
  const featured = concepts.slice(0, 12);
  $("#starter-list").innerHTML = `${featured.map((concept) => `<button class="starter" type="button" data-concept="${escapeHTML(concept.aliases[0])}">${escapeHTML(concept.title)}</button>`).join("")}<button class="starter starter-catalog" type="button" data-open-topic-library="true">همهٔ ${faNumber(concepts.length)} مسیر موضوعی ←</button>`;
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
  return { equivalent: "معادل قرآنی", related: "مفهوم مرتبط", exact: "عبارت دقیق" }[type] || "شاهد";
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
  const root = $("#root-query").value.trim();
  const usage = $("#usage-query").value.trim();
  const keywords = $("#keyword-query").value.trim();
  const synonyms = $("#synonym-query").value.trim();
  const status = $("#search-status");
  const primary = usage || synonyms || keywords || root;
  if (!primary) {
    status.textContent = "حداقل یکی از چهار مسیر جست‌وجو را وارد کنید.";
    $("#usage-query").focus();
    return;
  }

  const usageConcept = resolveConcept(usage);
  const synonymConcept = resolveConcept(synonyms);
  const concept = usageConcept || synonymConcept || resolveConcept(primary);
  const splitArabic = (value, label, type, origin, compact = false) => value.split(/[،,]/).map((item) => item.trim()).filter(Boolean).map((item) => ({
    value: compact ? normalize(item).replaceAll(" ", "") : normalize(item), label: `${label}: ${item}`, type, scope: "arabic", origin,
  }));
  const terms = [
    // ریشه‌ها گاهی با فاصله وارد می‌شوند («ح ب ب»). پیکره فاصلهٔ میان حروف ریشه ندارد.
    ...splitArabic(root, "ریشه / صورت", "exact", "ریشه یا صورتِ واردشده", true),
    ...splitArabic(keywords, "کلیدواژه", "exact", "کلیدواژهٔ واردشده"),
  ];
  if (usageConcept) {
    (usageConcept.equivalents || []).forEach(([term, label]) => terms.push({ value: normalize(term), label, type: "equivalent", scope: "arabic", origin: "کاربرد قرآنیِ واژه‌نامه" }));
  }
  if (synonymConcept) {
    (synonymConcept.related || []).forEach(([term, label]) => terms.push({ value: normalize(term), label, type: "related", scope: "arabic", origin: "پیوند مترادف/هم‌خانوادهٔ واژه‌نامه" }));
    if (!usageConcept) (synonymConcept.equivalents || []).forEach(([term, label]) => terms.push({ value: normalize(term), label, type: "equivalent", scope: "arabic", origin: "معادل قرآنیِ واژه‌نامه" }));
  }
  if (!terms.length && probablyArabic(primary)) {
    terms.push({ value: normalize(primary), label: "عبارت عربیِ کاربر", type: "exact", scope: "arabic", origin: "عبارتِ کاربر" });
  }
  if ($("#translation-option").checked) {
    terms.push({ value: normalize(primary), label: "عبارت فارسیِ کاربر", type: "exact", scope: "persian", origin: "جست‌وجوی دقیق در ترجمه" });
  }
  state.terms = uniqueTerms(terms);
  if (!state.terms.length) {
    status.textContent = "برای این مفهوم هنوز مسیر عربیِ بازبینی‌شده‌ای نیست. یک ریشه، کلیدواژه یا مترادف عربی وارد کنید.";
    return;
  }
  state.query = primary;
  state.concept = concept;
  state.matches = state.corpus.map((record) => evaluateRecord(record, state.terms)).filter(Boolean)
    .sort((a, b) => b.score - a.score || a.surah - b.surah || a.ayah - b.ayah);
  state.shown = PAGE_SIZE;
  state.filter = "all";
  state.contextVerseId = state.matches[0]?.id || null;
  state.selected = null;
  status.textContent = "";
  renderResults();
  navigate("results");
}

function runStarter(query) {
  $("#usage-query").value = query;
  $("#synonym-query").value = "";
  $("#root-query").value = "";
  $("#keyword-query").value = "";
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
  $$(".result-filters button").forEach((button) => {
    const active = button.dataset.filter === state.filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  renderContextStudy();
  renderVerseList();
}

function verseCard(verse) {
  const primaryEvidence = verse.evidence.slice(0, 2).map((item) => `${item.label} · ${item.source}`).join("، ");
  return `<button class="verse-card" type="button" data-verse-id="${escapeHTML(verse.id)}">
    <span class="verse-head"><span class="verse-reference">${escapeHTML(verse.reference)} · ${escapeHTML(verse.revelation)}</span><span class="verse-type ${verse.type}">${typeLabel(verse.type)}</span></span>
    <span class="verse-arabic" lang="ar" dir="rtl">${escapeHTML(verse.arabic)}</span>
    <span class="verse-persian">${escapeHTML(verse.persian)}</span>
    <span class="verse-match"><b>واژهٔ شاهد:</b> ${escapeHTML(primaryEvidence)} <i class="open-cue" aria-hidden="true">←</i></span>
  </button>`;
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
  $("#result-progress").textContent = state.filter === "context"
    ? `خوانش سیاق برای ${faNumber(filtered.length)} آیه در دسترس است؛ آیهٔ موردنظر را از نوار بالا انتخاب کنید.`
    : `${faNumber(visible.length)} از ${faNumber(filtered.length)} آیه در این لایه · ${faNumber(new Set(state.matches.map((item) => item.surah)).size)} سوره در کل مسیر`;
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

function detailPanelNotes(verse) {
  const distributions = evidenceDistribution(verse);
  const lexicalRange = distributions.map((item) => item.count ? `${item.label}: ${faNumber(item.count)} آیه / ${faNumber(item.surahs)} سوره` : `${item.label}: مسیر غیرواژگانی`).join("؛ ");
  return `<section class="detail-panel"><p class="eyebrow">نکات آیه ـ دادهٔ قابل بازبینی</p><h3>این آیه دقیقاً از چه مسیرى وارد پژوهش شد؟</h3>
    <p class="reading-notice">«صورتِ بازیابی» با «معنای نهایی» یکی نیست. این کارت محلِ دادهٔ دقیق و مرزِ استنتاج است، نه تفسیرِ خودکار.</p>
    <ul class="study-list">
      <li><b>شناسهٔ متن</b>${escapeHTML(verse.reference)} · ${escapeHTML(verse.revelation)} · آیهٔ ${faNumber(verse.ayah)} از سورهٔ ${faNumber(verse.surah)}.</li>
      <li><b>واژه/مسیر شاهد</b>${escapeHTML(verse.evidence.map((item) => `${item.label} (${item.source})`).join("، "))}</li>
      <li><b>دامنهٔ مشاهده‌پذیر</b>${escapeHTML(lexicalRange || "برای این مسیر، آمار واژگانیِ مستقلی ثبت نشده است.")}</li>
      <li><b>سطح ارتباط</b>${escapeHTML(typeLabel(verse.type))}. ${verse.type === "related" ? "این پیوند برای مقایسه است و هم‌معنایی قطعی یا مقصد سوره را ثابت نمی‌کند." : "تطابق در متن عربی یا عبارت انتخاب‌شده ثبت شده است."}</li>
      <li><b>کنترل خوانش</b>فاعل/مفعول یا مخاطب، نفی و اثبات، قیدها و نسبتِ جمله با پیش و پس را از خودِ متن جداگانه ثبت کنید.</li>
    </ul></section>`;
}

function detailPanelFoundations(verse) {
  const evidenceKinds = [...new Set(verse.evidence.map((item) => typeLabel(item.type)))].join("، ");
  const hasArabicWitness = verse.evidence.some((item) => item.scope !== "persian" && item.value);
  const contextSize = getContext(verse).length;
  return `<section class="detail-panel"><p class="eyebrow">اصول و مبانیِ خواندن آیه</p><h3>چه چیزهایی باید پیش از هر برداشت کنترل شوند؟</h3>
    <ul class="study-list"><li><b>پایهٔ متن</b>${hasArabicWitness ? "صورتِ عربیِ شاهد در پیکره دیده شده است؛ ترجمه فقط برای خوانش فارسیِ همراه آن است." : "این مسیر از ترجمه یا پروندهٔ روایی آمده است؛ برای تحلیل واژه، متن عربی را جداگانه بررسی کنید."}</li><li><b>پایهٔ بازیابی</b>این آیه با سطحِ «${escapeHTML(evidenceKinds)}» وارد مسیر شده است. سطحِ بازیابی، ادعای معنای نهاییِ آیه نیست.</li><li><b>پایهٔ سیاق نزدیک</b>${faNumber(contextSize)} آیه در پنجرهٔ پیش/خود/پسِ همین سوره در دسترس است. پیوستگی جمله‌ها را پیش از تعمیم بررسی کنید.</li><li><b>پایهٔ زبان</b>ریشه، صورت صرفی، نقش نحوی و مرجع ضمیر باید با منبع زبان‌شناختیِ معتبر کنترل شوند؛ پیکرهٔ فعلی تحلیل صرفیِ ادعایی تولید نمی‌کند.</li><li><b>پایهٔ اختلاف دیدگاه</b>هر داوری تفسیری به منبع، مؤلف، جلد و صفحه نیاز دارد؛ آن را در یادداشت پژوهش ثبت کنید.</li></ul></section>`;
}

function detailPanelFramework(verse) {
  const direct = verse.evidence.filter((item) => item.type !== "related");
  const equivalents = state.terms.filter((item) => item.type === "equivalent");
  const related = state.terms.filter((item) => item.type === "related");
  const directLabel = direct.map((item) => item.label).join("، ") || "شاهدِ مستقیمِ واژگانی در این کارت ثبت نشده است";
  return `<section class="detail-panel"><p class="eyebrow">چارچوب معنایی ـ لایه‌های جدا</p><h3>ظرفیت معنایی را با لایه‌هایش بخوانید، نه با یک برچسب.</h3>
    <p>پرسشِ پایه: <b>${escapeHTML(state.concept?.title || state.query)}</b>. در این آیه، نقطهٔ شروعِ قابل مشاهده <b>${escapeHTML(directLabel)}</b> است.</p>
    <div class="semantic-columns"><div class="semantic-box"><h4>لایهٔ متن و معادل‌ها</h4>${equivalents.map((item) => `<span>${escapeHTML(item.label)}</span>`).join("") || `<span>${escapeHTML(directLabel)}</span>`}</div><div class="semantic-box related"><h4>لایهٔ پیوندهای نیازمند آزمون</h4>${related.map((item) => `<span>${escapeHTML(item.label)}</span>`).join("") || "<span>در این جست‌وجو پیوند مرتبطی فعال نشده است.</span>"}</div></div>
    <ul class="study-list"><li><b>لایهٔ اول: دلالت در جمله</b>واژه در این جمله به چه چیز، کنش یا نسبتی اشاره می‌کند؟ پاسخ باید با ساختار خودِ آیه سنجیده شود.</li><li><b>لایهٔ دوم: توزیع قرآنی</b>مواضع دیگرِ همان صورت را مقایسه کنید؛ اشتراکِ صورت به‌تنهایی اشتراکِ کارکرد را ثابت نمی‌کند.</li><li><b>لایهٔ سوم: پیوند مفهومی</b>هر پیوند مرتبط فقط یک فرضیهٔ پژوهش است تا با سیاق و منبع تفسیری آزموده شود.</li></ul></section>`;
}

function detailPanelMessages(verse) {
  const prompts = [...promptsForVerse(), ...closeReadingPrompts(verse)].filter((item, index, items) => items.indexOf(item) === index);
  return `<section class="detail-panel"><p class="eyebrow">پیام‌های قابل بررسی</p><h3>از دادهٔ آیه به پرسشِ پیام برسید، نه به یک جمع‌بندیِ آماده.</h3>
    <p class="reading-notice">این‌ها پرسش‌های قابل پیگیری‌اند، نه پیام‌های منسوب به قرآن. هر پاسخ تفسیری باید به متن، سیاق و منبعِ دقیق تکیه کند.</p>
    <ul class="study-list">${prompts.map((prompt, index) => `<li><b>پرسش ${faNumber(index + 1)}</b>${escapeHTML(prompt)}</li>`).join("")}<li><b>ثبت نتیجهٔ موقت</b>اگر پاسخی یافتید، دلیلِ لفظی، آیه‌های مقایسه‌ای و مأخذ تفسیری را در «یادداشت من» همراه با جلد و صفحه ثبت کنید.</li></ul></section>`;
}

function detailPanelContext(verse) {
  const context = getContext(verse);
  return `<section class="detail-panel"><p class="eyebrow">آیه در سیاق سوره</p><h3>پیش و پسِ آیه را کنار هم بخوانید.</h3><p>پنجرهٔ خطیِ زیر جای مطالعهٔ کامل سوره را نمی‌گیرد، اما دادهٔ لازم برای پرهیز از بریده‌خوانی را نشان می‌دهد. برای جزئیاتِ توزیع و پرسش‌ها، «فهم آیه در سیاق» در صفحهٔ پیشین را باز کنید.</p>
    <div class="context-grid">${context.map((item) => `<button class="context-verse ${item.id === verse.id ? "current" : ""}" data-context-id="${escapeHTML(item.id)}" type="button"><b>${escapeHTML(item.reference)}${item.id === verse.id ? " · آیهٔ پژوهش" : ""}</b><p class="context-arabic" lang="ar" dir="rtl">${escapeHTML(item.arabic)}</p><p>${escapeHTML(item.persian)}</p></button>`).join("")}</div></section>`;
}

function detailPanelQuran(verse) {
  const sameSurah = state.matches.filter((item) => item.surah === verse.surah && item.id !== verse.id).slice(0, 5);
  const surahs = new Set(state.matches.map((item) => item.surah)).size;
  const distributions = evidenceDistribution(verse).filter((item) => item.count);
  return `<section class="detail-panel"><p class="eyebrow">آیه در نسبت با کل قرآن</p><h3>جای این آیه در مسیرِ همین پژوهش</h3>
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
  const panels = {
    notes: detailPanelNotes,
    foundations: detailPanelFoundations,
    framework: detailPanelFramework,
    messages: detailPanelMessages,
    context: detailPanelContext,
    quran: detailPanelQuran,
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

function openStory(id) {
  const story = state.stories.find((item) => item.id === id);
  if (!story) return;
  const ids = new Set();
  story.passages.forEach((passage) => {
    for (let ayah = passage.start; ayah <= passage.end; ayah += 1) ids.add(`${passage.surah}:${ayah}`);
  });
  state.query = story.title;
  state.concept = null;
  state.terms = [];
  state.matches = [...ids].map((id) => state.recordById.get(id)).filter(Boolean).map((record) => resultVerse(record, [{ label: "آیهٔ مسیر روایی", type: "exact", source: "فهرست داستان", origin: story.note }]));
  state.shown = PAGE_SIZE;
  state.filter = "all";
  renderResults();
  navigate("results");
}

function showScreen(name, verseId = null) {
  state.screen = name;
  $("#search-screen").hidden = name !== "search";
  $("#library-screen").hidden = name !== "library";
  $("#surah-screen").hidden = name !== "surah";
  $("#results-screen").hidden = name !== "results";
  $("#detail-screen").hidden = name !== "detail";
  if (name === "detail" && verseId && state.selected?.id !== verseId) openVerse(verseId, false);
  window.scrollTo({ top: 0, behavior: "auto" });
}

function navigate(name, verseId = null) {
  const hashMap = { search: "", results: "#results", library: `#library/${state.libraryMode || ""}`, surah: `#surah/${verseId || state.selectedSurah?.number || ""}` };
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

$("#starter-list").addEventListener("click", (event) => {
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

$("#verse-list").addEventListener("click", (event) => {
  const card = event.target.closest("[data-verse-id]");
  if (card) openVerse(card.dataset.verseId);
});

$("#context-study").addEventListener("click", (event) => {
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
  if (event.target.closest("#save-note")) saveNote();
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
