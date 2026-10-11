const CORPUS_URL = "static/offline-corpus.json";
const LEXICON_URL = "static/concept-lexicon.json";
const STORY_INDEX_URL = "static/story-index.json";
const NOTEBOOK_KEY = "zehnyar-verse-notebook-v2";
const PAGE_SIZE = 12;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = {
  screen: "search",
  corpus: [],
  recordById: new Map(),
  lexicon: null,
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
  const [corpusResponse, lexiconResponse, storyResponse] = await Promise.all([fetch(CORPUS_URL), fetch(LEXICON_URL), fetch(STORY_INDEX_URL)]);
  if (!corpusResponse.ok || !lexiconResponse.ok || !storyResponse.ok) throw new Error("پیکرهٔ محلی یا فهرست پژوهش در دسترس نیست.");
  const corpus = await corpusResponse.json();
  state.lexicon = await lexiconResponse.json();
  state.stories = (await storyResponse.json()).stories || [];
  state.corpus = corpus.verses.map(recordFromTuple);
  state.recordById = new Map(state.corpus.map((record) => [record.id, record]));
  $("#result-corpus").textContent = `${faNumber(state.corpus.length)} آیه`;
  renderStarters();
}

function renderStarters() {
  const priority = ["محبت و عشق", "عدالت", "رحمت", "خانواده", "علم و اندیشه", "آزادی و اختیار", "دعا و عبادت", "توبه"];
  const concepts = [...(state.lexicon?.concepts || [])].sort((a, b) => {
    const aIndex = priority.indexOf(a.title);
    const bIndex = priority.indexOf(b.title);
    return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex);
  });
  $("#starter-list").innerHTML = concepts.map((concept) => `<button class="starter" type="button" data-concept="${escapeHTML(concept.aliases[0])}">${escapeHTML(concept.title)}</button>`).join("");
}

function resolveConcept(query) {
  const normalized = normalize(query);
  const matches = (state.lexicon?.concepts || []).flatMap((concept) => (concept.aliases || []).map((alias) => ({ concept, alias: normalize(alias) })))
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
  const splitArabic = (value, label, type, origin) => value.split(/[،,]/).map((item) => item.trim()).filter(Boolean).map((item) => ({
    value: normalize(item), label: `${label}: ${item}`, type, scope: "arabic", origin,
  }));
  const terms = [
    ...splitArabic(root, "ریشه / صورت", "exact", "ریشه یا صورتِ واردشده"),
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
  return state.filter === "all" ? state.matches : state.matches.filter((item) => item.type === state.filter);
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

function renderVerseList() {
  const filtered = resultsByFilter();
  const visible = filtered.slice(0, state.shown);
  const list = $("#verse-list");
  if (!visible.length) {
    list.replaceChildren($("#empty-result-template").content.cloneNode(true));
  } else {
    list.innerHTML = visible.map(verseCard).join("");
  }
  $("#result-progress").textContent = `${faNumber(visible.length)} از ${faNumber(filtered.length)} آیه در این لایه · ${faNumber(new Set(state.matches.map((item) => item.surah)).size)} سوره در کل مسیر`;
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
  const direct = verse.evidence.filter((item) => item.type !== "related");
  return `<section class="detail-panel"><p class="eyebrow">نکات متن‌محور</p><h3>از چه مسیرى این آیه وارد پژوهش شد؟</h3>
    <p class="reading-notice">این بخش، دادهٔ بازیابی و راهنمای خواندن است؛ برداشت تفسیریِ نهایی نیست.</p>
    <ul class="study-list">
      <li><b>واژه‌های شاهد</b>${escapeHTML(verse.evidence.map((item) => `${item.label} (${item.source})`).join("، "))}</li>
      <li><b>سطح ارتباط</b>${escapeHTML(typeLabel(verse.type))}. ${verse.type === "related" ? "این پیوند برای مقایسه است و هم‌معنایی قطعی را نشان نمی‌دهد." : "تطابق در متن عربی یا عبارت انتخاب‌شده ثبت شده است."}</li>
      <li><b>اصل خواندن</b>گوینده، مخاطب، فعل و قیدهای آیه را پیش از استخراج هر پیام مشخص کنید.</li>
    </ul></section>`;
}

function detailPanelFoundations(verse) {
  const evidenceKinds = [...new Set(verse.evidence.map((item) => typeLabel(item.type)))].join("، ");
  return `<section class="detail-panel"><p class="eyebrow">اصول و مبانیِ خواندن آیه</p><h3>پیش از برداشت، پایه‌های بررسی را روشن کنید.</h3>
    <ul class="study-list"><li><b>پایهٔ متن</b>متن عربیِ آیه، نقطهٔ آغاز است؛ ترجمه برای فهم فارسی کمک می‌کند اما جای تحلیلِ واژهٔ عربی را نمی‌گیرد.</li><li><b>پایهٔ بازیابی</b>این آیه با سطحِ «${escapeHTML(evidenceKinds)}» وارد مسیر شده است. سطحِ بازیابی را با معنای نهاییِ آیه یکی نگیرید.</li><li><b>پایهٔ سیاق</b>گوینده، مخاطب، پیوستگی پیش و پس و جایگاه آیه در سوره، پیش از تعمیم‌دادن بررسی می‌شود.</li><li><b>پایهٔ اختلاف دیدگاه</b>هر داوری تفسیری به منبع، مؤلف، جلد و صفحه نیاز دارد؛ در یادداشت پژوهش ثبتش کنید.</li></ul></section>`;
}

function detailPanelFramework(verse) {
  const equivalents = state.terms.filter((item) => item.type === "equivalent");
  const related = state.terms.filter((item) => item.type === "related");
  return `<section class="detail-panel"><p class="eyebrow">چارچوب معنایی و مبانی بررسی</p><h3>مفهوم را به جایِ یک برچسبِ کلی، لایه‌لایه بخوانید.</h3>
    <p>مفهومِ پایه: <b>${escapeHTML(state.concept?.title || state.query)}</b>. واژه‌های زیر مسیرِ بازیابی‌اند و نه معادل‌سازیِ تفسیریِ قطعی.</p>
    <div class="semantic-columns"><div class="semantic-box"><h4>معادل‌های قرآنیِ فعال</h4>${equivalents.map((item) => `<span>${escapeHTML(item.label)}</span>`).join("") || "<span>—</span>"}</div><div class="semantic-box related"><h4>پیوندهای مرتبطِ فعال</h4>${related.map((item) => `<span>${escapeHTML(item.label)}</span>`).join("") || "<span>—</span>"}</div></div>
    <ul class="study-list"><li><b>مبنای اول</b>خودِ واژهٔ عربی، پیش از ترجمه و برداشت، بررسی می‌شود.</li><li><b>مبنای دوم</b>پیوند مرتبط باید در همان سیاق آزموده شود؛ صرفِ حضور یک ریشه، نتیجهٔ مفهومی نمی‌سازد.</li></ul></section>`;
}

function detailPanelMessages(verse) {
  return `<section class="detail-panel"><p class="eyebrow">پیام‌های قابل بررسی</p><h3>پیام را از متن استخراج کنید، نه از یک کارت آماده.</h3>
    <p class="reading-notice">برای حفظ امانت متن، این بخش «پرسشِ استخراج پیام» می‌دهد، نه یک تفسیرِ خودکار و قطعی.</p>
    <ul class="study-list">${promptsForVerse().map((prompt, index) => `<li><b>پرسش ${faNumber(index + 1)}</b>${escapeHTML(prompt)}</li>`).join("")}<li><b>پیوند با این آیه</b>بررسی کنید «${escapeHTML(verse.evidence[0]?.label || state.query)}» در این آیه چه نقشی دارد و چه چیزی را نمی‌توان از آن نتیجه گرفت.</li></ul></section>`;
}

function detailPanelContext(verse) {
  const context = getContext(verse);
  return `<section class="detail-panel"><p class="eyebrow">آیه در سیاق سوره</p><h3>پیش و پسِ آیه را کنار هم بخوانید.</h3><p>این پنجرهٔ خطی جای مطالعهٔ کامل سوره را نمی‌گیرد، اما از بریده‌خوانی جلوگیری می‌کند.</p>
    <div class="context-grid">${context.map((item) => `<button class="context-verse ${item.id === verse.id ? "current" : ""}" data-context-id="${escapeHTML(item.id)}" type="button"><b>${escapeHTML(item.reference)}</b><p>${escapeHTML(item.persian)}</p></button>`).join("")}</div></section>`;
}

function detailPanelQuran(verse) {
  const sameSurah = state.matches.filter((item) => item.surah === verse.surah && item.id !== verse.id).slice(0, 5);
  const surahs = new Set(state.matches.map((item) => item.surah)).size;
  return `<section class="detail-panel"><p class="eyebrow">آیه در نسبت با کل قرآن</p><h3>جای این آیه در مسیرِ همین پژوهش</h3>
    <ul class="study-list"><li><b>پوشش بازیابی</b>${faNumber(state.matches.length)} آیه در ${faNumber(surahs)} سوره، بر پایهٔ واژه‌های فعالِ همین پرسش پیدا شده‌اند.</li><li><b>مرز نتیجه</b>این شمارش، اهمیت تفسیری یا همهٔ ارتباط‌های ممکن میان آیات را رتبه‌بندی نمی‌کند.</li></ul>
    ${sameSurah.length ? `<div class="related-verses">${sameSurah.map((item) => `<button class="related-verse" type="button" data-related-id="${escapeHTML(item.id)}">${escapeHTML(item.reference)} · ${escapeHTML(item.evidence[0]?.label || "شاهد")}</button>`).join("")}</div>` : "<p>در این مسیر، شاهدِ دیگری از همین سوره در فهرست فعلی نیست.</p>"}</section>`;
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
  return (state.lexicon?.concepts || []).map((concept) => {
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
    if (["surahs", "stories"].includes(mode)) {
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
  if (button) runStarter(button.dataset.concept);
});

$("#open-surah-library").addEventListener("click", () => openLibrary("surahs"));
$("#open-story-library").addEventListener("click", () => openLibrary("stories"));
$("#library-list").addEventListener("click", (event) => {
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
