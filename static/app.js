const API_BASE_KEY = "zehnyar-research-api-base-v1";
const NOTEBOOK_KEY = "zehnyar-evidence-notebook-v1";

function apiUrl(path) {
  const base = (localStorage.getItem(API_BASE_KEY) || "").trim().replace(/\/$/, "");
  return base ? `${base}${path}` : path;
}

function updateConnectionLabel() {
  const label = document.querySelector("#connection-label");
  if (!label) return;
  label.textContent = localStorage.getItem(API_BASE_KEY)
    ? "سرور پژوهش متصل"
    : "متن کامل · ۶۲۳۶ آیه";
}
const state = { data: null, filter: "all", limit: 12 };

const $ = (selector) => document.querySelector(selector);
const form = $("#search-form");
const input = $("#query");
const modeSelect = $("#search-mode");
const submit = $("#search-submit");
const resultsList = $("#results-list");
const statusMessage = $("#status-message");
const SVG_NS = "http://www.w3.org/2000/svg";

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

const OFFLINE_CORPUS_URL = "static/offline-corpus.json";
const OFFLINE_FRAMEWORK_URL = "static/offline-framework.json";
let offlineCorpusPromise;

function normalizeForOffline(value = "") {
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

async function offlineCorpus() {
  if (!offlineCorpusPromise) {
    offlineCorpusPromise = fetch(OFFLINE_CORPUS_URL).then((response) => {
      if (!response.ok) throw new Error("offline corpus unavailable");
      return response.json();
    });
  }
  return offlineCorpusPromise;
}

function offlineStructure(matches) {
  const bySurah = new Map();
  const revelation = { "مکی": { total: 0, direct: 0 }, "مدنی": { total: 0, direct: 0 } };
  matches.forEach((item) => {
    const current = bySurah.get(item.surah) || { surah: item.surah, name: item.surah_name, type: item.revelation, total: 0, direct: 0 };
    current.total += 1;
    current.direct += 1;
    bySurah.set(item.surah, current);
    revelation[item.revelation].total += 1;
    revelation[item.revelation].direct += 1;
  });
  return {
    revelation,
    distribution: [...bySurah.values()].sort((a, b) => b.total - a.total || a.surah - b.surah).slice(0, 7),
    clusters: [],
    note: "در حالت آفلاین، این نمودار فقط نتایج بازیابیِ عبارت را توصیف می‌کند.",
  };
}

function offlineGraph(query, matches, structure) {
  const topSurahs = structure.distribution.slice(0, 4);
  const nodes = [
    { id: "topic", label: query, meta: "پرسشِ آفلاین", kind: "topic", weight: 1 },
    { id: "term-0", label: "عبارتِ جست‌وجوشده", meta: `${matches.length} شاهد`, kind: "term", weight: 0.78 },
    ...topSurahs.map((item) => ({ id: `surah-${item.surah}`, label: item.name, meta: `سورهٔ ${item.surah} · ${item.total} شاهد`, kind: "surah", weight: 0.63 })),
    ...matches.slice(0, 2).map((item, index) => ({ id: `verse-${index}`, label: item.reference, meta: item.relation, kind: "verse", weight: 0.45 })),
  ];
  const edges = [
    { source: "topic", target: "term-0", label: `${matches.length} پیوند` },
    ...topSurahs.map((item) => ({ source: "term-0", target: `surah-${item.surah}`, label: `${item.total} آیه` })),
    ...matches.slice(0, 2).map((item, index) => ({ source: "term-0", target: `verse-${index}`, label: "شاهد نمونه" })),
  ];
  return {
    nodes,
    edges,
    layout: "concentric-evidence",
    metrics: { lexical_terms: 1, surah_connections: topSurahs.length, narrative_paths: 0, story_lexical_hits: 0 },
    reading_arc: [
      { stage: "نقطهٔ آغاز", title: "عبارت و شاهد", body: "جست‌وجوی آفلاین فقط عبارت واردشده را در متن عربی و ترجمهٔ فارسی بازیابی می‌کند." },
      { stage: "رشتهٔ واژگانی", title: "واژهٔ مرکزی", body: `عبارتِ جست‌وجوشده: ${query}` },
      { stage: "پراکندگی متن", title: "سوره‌ها", body: `بیشترین تمرکز آفلاین: ${topSurahs.map((item) => item.name).join("، ") || "—"}` },
      { stage: "قوس روایی", title: "نیازمند اتصال", body: "مسیرهای رواییِ بازبینی‌شده در نسخهٔ آنلاین فعال می‌شوند." },
      { stage: "بازگشت به زندگی", title: "تأمل محتاطانه", body: "میان متن، ترجمه و برداشت شخصی تمایز نگه دارید." },
    ],
    notice: "شبکهٔ آفلاین محدود به بازیابیِ عبارت است. برای واژه‌نامهٔ موضوعی، روایت‌ها و تحلیل کامل به سرور پژوهش متصل شوید.",
  };
}

async function offlineAnalyze(query, limit) {
  const corpus = await offlineCorpus();
  const normalizedQuery = normalizeForOffline(query);
  if (!normalizedQuery) throw new Error("عبارت جست‌وجو نمی‌تواند خالی باشد.");
  const records = corpus.verses.map(([surah, ayah, arabic, persian, surah_name, revelation]) => ({ surah, ayah, arabic, persian, surah_name, revelation }));
  const byId = new Map(records.map((record) => [`${record.surah}:${record.ayah}`, record]));
  const matches = records.filter((record) => {
    const ar = normalizeForOffline(record.arabic);
    const fa = normalizeForOffline(record.persian);
    return ar.includes(normalizedQuery) || fa.includes(normalizedQuery);
  }).map((record) => {
    const source = normalizeForOffline(record.arabic).includes(normalizedQuery) && normalizeForOffline(record.persian).includes(normalizedQuery)
      ? "هر دو متن" : normalizeForOffline(record.arabic).includes(normalizedQuery) ? "متن عربی" : "ترجمهٔ فارسی";
    return {
      ...record,
      id: `${record.surah}:${record.ayah}`,
      reference: `${record.surah_name} ${record.surah}:${record.ayah}`,
      score: 1,
      matches: ["عبارتِ جست‌وجوشده"],
      evidence: [{ label: "عبارتِ جست‌وجوشده", term: normalizedQuery, source, origin: "بازیابی آفلاین" }],
      story_context: [],
      relation: "ذکر / ترجمهٔ مستقیم",
    };
  });
  const shown = matches.slice(0, limit);
  const seen = new Set(shown.map((item) => item.id));
  const context = [];
  shown.slice(0, 3).forEach((item) => [-1, 1].forEach((delta) => {
    const neighbor = byId.get(`${item.surah}:${item.ayah + delta}`);
    if (neighbor && !seen.has(`${neighbor.surah}:${neighbor.ayah}`) && context.length < 4) {
      seen.add(`${neighbor.surah}:${neighbor.ayah}`);
      context.push({ ...neighbor, id: `${neighbor.surah}:${neighbor.ayah}`, reference: `${neighbor.surah_name} ${neighbor.surah}:${neighbor.ayah}`, score: 0, matches: ["همسایگی خطی"], evidence: [], story_context: [], relation: "سیاق خطی" });
    }
  }));
  const structure = offlineStructure(matches);
  return {
    query,
    canonical_topic: null,
    mode: { id: "literal", label: "آفلاین: فقط عبارت", description: "بازیابی پایه از پیکرهٔ ذخیره‌شده روی دستگاه" },
    summary: `در حالت آفلاین، ${faNumber(matches.length)} شاهدِ دارای عبارت «${query}» در پیکرهٔ محلی پیدا شد. توسعهٔ موضوعی، تحلیل شبکه‌ای کامل و مسیرهای روایی به اتصال سرور نیاز دارند.`,
    topic_description: "جست‌وجوی پایهٔ آفلاین؛ فقط تطابق عبارت در متن عربی و ترجمهٔ فارسی.",
    questions: ["این عبارت در آیه چه نقش و چه سیاقی دارد؟", "برای گسترش موضوعی و مسیرهای روایی، در زمان اتصال دوباره پژوهش را اجرا کنید."],
    stats: { direct: matches.length, thematic: 0, narrative: 0, story_lexical: 0, surahs: structure.distribution.length, shown: shown.length },
    expansion: [],
    verses: shown,
    context,
    narrative: { paths: [], lexical_story_hits: 0, notice: "مسیرهای روایی در نسخهٔ آنلاین پژوهش در دسترس‌اند." },
    structure,
    graph: offlineGraph(query, matches, structure),
    reflection: { title: "تأمل آفلاین", focus: "خواندن دقیق متن پیش از برداشت", prompts: ["یک موقعیت واقعی را انتخاب کنید و میان متن، ترجمه و برداشت شخصی تمایز بگذارید.", "برای تحلیل واژگانیِ گسترده‌تر و مسیرهای روایی، در حالت آنلاین همین پرسش را دوباره اجرا کنید."], notice: "این بخش تمرین تأمل است، نه حکم شخصی یا تفسیر نهایی." },
    method: { title: "حالت آفلاین", steps: ["پیکرهٔ ذخیره‌شده روی دستگاه جست‌وجو می‌شود.", "فقط عبارتِ واردشده در عربی و ترجمهٔ فارسی تطبیق داده می‌شود.", "تحلیل موضوعی، شبکهٔ کامل و مسیرهای روایی نیازمند سرور پژوهش‌اند."] },
    corpus: { arabic: "Tanzil Uthmani (offline)", persian: "QuranEnc Persian (offline)", total_verses: corpus.verses.length },
    offline: true,
  };
}

function showOfflineNotice() {
  statusMessage.textContent = "اتصال به سرور پژوهش در دسترس نیست؛ جست‌وجوی پایه از پیکرهٔ ذخیره‌شده روی همین دستگاه اجرا شد.";
  statusMessage.classList.add("show", "offline");
}


function loadNotebook() {
  try {
    const saved = JSON.parse(localStorage.getItem(NOTEBOOK_KEY) || "[]");
    return Array.isArray(saved) ? saved.filter((item) => item && item.id && item.reference) : [];
  } catch {
    return [];
  }
}

let notebook = loadNotebook();

function persistNotebook() {
  localStorage.setItem(NOTEBOOK_KEY, JSON.stringify(notebook));
}

function renderNotebook() {
  const count = $("#notebook-count");
  const list = $("#notebook-list");
  count.textContent = faNumber(notebook.length);
  if (!notebook.length) {
    list.innerHTML = '<p class="notebook-empty">هنوز شاهدی ذخیره نشده است.</p>';
    return;
  }
  list.innerHTML = notebook.slice(0, 6).map((item) => `<article class="notebook-item">
    <div><b>${escapeHTML(item.reference)}</b><span lang="ar" dir="rtl">${escapeHTML(item.arabic)}</span>${item.note ? `<small>${escapeHTML(item.note)}</small>` : ""}</div>
    <div class="notebook-item-actions"><button class="notebook-note" data-edit-note="${escapeHTML(item.id)}" type="button">یادداشت</button><button class="notebook-remove" data-remove-note="${escapeHTML(item.id)}" type="button" aria-label="حذف ${escapeHTML(item.reference)}">حذف</button></div>
  </article>`).join("");
  if (notebook.length > 6) {
    list.insertAdjacentHTML("beforeend", `<p class="notebook-empty">و ${faNumber(notebook.length - 6)} شاهد دیگر در دفتر ذخیره شده است.</p>`);
  }
}

function saveVerse(verse) {
  if (notebook.some((item) => item.id === verse.id)) return false;
  notebook.unshift({
    id: verse.id,
    reference: verse.reference,
    arabic: verse.arabic,
    persian: verse.persian,
    query: state.data?.query || "",
    note: "",
    savedAt: new Date().toISOString(),
  });
  persistNotebook();
  renderNotebook();
  return true;
}

function loading() {
  const template = $("#loading-template");
  resultsList.replaceChildren(template.content.cloneNode(true));
  $("#load-more").hidden = true;
  $("#narrative-section").hidden = true;
  submit.disabled = true;
  statusMessage.classList.remove("show", "offline");
}

function showError(message) {
  statusMessage.textContent = message;
  statusMessage.classList.remove("offline");
  statusMessage.classList.add("show");
}

function relationClass(verse) {
  return verse.relation.includes("مستقیم") ? "direct" : "thematic";
}

function renderStats(stats) {
  const items = [
    [stats.direct, "شاهد مستقیم"],
    [stats.thematic, "پیوند واژگانی"],
    [stats.narrative, "مسیر روایی"],
    [stats.story_lexical, "شاهد در روایت"],
    [stats.surahs, "سورهٔ درگیر"],
  ];
  $("#stats").innerHTML = items
    .map(([value, label]) => `<div class="stat"><strong>${faNumber(value)}</strong><span>${escapeHTML(label)}</span></div>`)
    .join("");
}

function verseCard(verse, index, context = false) {
  if (context) {
    return `<article class="context-item">
      <div class="context-ref">${escapeHTML(verse.reference)} · ${escapeHTML(verse.revelation)}</div>
      <p>${escapeHTML(verse.persian)}</p>
    </article>`;
  }
  const evidence = verse.evidence?.length ? verse.evidence : verse.matches.map((label) => ({ label, source: "مسیر بازیابی" }));
  const matchMarkup = evidence
    .map((item) => `<span title="${escapeHTML(item.origin || item.source)}"><b>${escapeHTML(item.label)}</b> · ${escapeHTML(item.source)}</span>`)
    .join("");
  const isSaved = notebook.some((item) => item.id === verse.id);
  const storyMarkup = verse.story_context?.length ? `<span class="story-tag">در روایت: ${escapeHTML(verse.story_context[0])}</span>` : "";
  return `<article class="verse-card" data-verse-id="${escapeHTML(verse.id)}" style="animation-delay:${Math.min(index, 9) * 35}ms">
    <div class="verse-head">
      <span class="reference">${escapeHTML(verse.reference)} <small>· ${escapeHTML(verse.revelation)}</small></span>
      <div class="relation-group"><span class="relation ${relationClass(verse)}">${escapeHTML(verse.relation)}</span>${storyMarkup}</div>
    </div>
    <p class="verse-arabic" lang="ar" dir="rtl">${escapeHTML(verse.arabic)}</p>
    <p class="verse-persian">${escapeHTML(verse.persian)}</p>
    <div class="verse-foot">
      <div class="match-list">${matchMarkup}</div>
      <div class="verse-actions">
        <button class="save-verse ${isSaved ? "saved" : ""}" type="button" data-save="${escapeHTML(verse.id)}" ${isSaved ? "disabled" : ""}>${isSaved ? "در دفتر ✓" : "ذخیره"}</button>
        <button class="copy-verse" type="button" data-copy="${escapeHTML(verse.id)}" aria-label="کپی ارجاع ${escapeHTML(verse.reference)}">کپی شاهد ↗</button>
      </div>
    </div>
  </article>`;
}

function renderVerses() {
  if (!state.data) return;
  const all = state.data.verses;
  const filtered = state.filter === "all"
    ? all
    : all.filter((verse) => relationClass(verse) === state.filter);

  if (!filtered.length) {
    resultsList.innerHTML = `<div class="empty-results"><b>در این لایه شاهدی نمایش داده نشد.</b>فیلتر «همه» را امتحان کنید یا واژهٔ دیگری جست‌وجو کنید.</div>`;
    return;
  }
  resultsList.innerHTML = filtered.map((verse, index) => verseCard(verse, index)).join("");
}

function renderContext(context) {
  const section = $("#context-section");
  if (!context || !context.length) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  $("#context-list").innerHTML = context.map((verse) => verseCard(verse, 0, true)).join("");
}

function renderNarrative(narrative) {
  const section = $("#narrative-section");
  const paths = narrative?.paths || [];
  if (!paths.length) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  $("#narrative-count").textContent = `${faNumber(paths.length)} مسیر · ${faNumber(narrative.lexical_story_hits)} شاهد واژگانی در روایت‌ها`;
  $("#narrative-notice").textContent = narrative.notice || "";
  $("#narrative-list").innerHTML = paths.map((path, index) => {
    const saved = notebook.some((item) => item.id === path.id);
    return `<article class="narrative-card" style="animation-delay:${index * 55}ms">
      <div class="narrative-card-head"><span class="story-name">${escapeHTML(path.story)}</span><span>${escapeHTML(path.reference)} · ${escapeHTML(path.focus)}</span></div>
      <p class="narrative-lens">${escapeHTML(path.lens)}</p>
      <p class="narrative-arabic" lang="ar" dir="rtl">${escapeHTML(path.arabic)}</p>
      <p class="narrative-persian">${escapeHTML(path.persian)}</p>
      <div class="narrative-question"><b>پرسش خوانش:</b> ${escapeHTML(path.question)}</div>
      <button class="save-narrative ${saved ? "saved" : ""}" type="button" data-save-narrative="${escapeHTML(path.id)}" ${saved ? "disabled" : ""}>${saved ? "در دفتر ✓" : "ذخیرهٔ آیهٔ لنگر"}</button>
    </article>`;
  }).join("");
}

function renderStructure(structure) {
  const total = (structure?.revelation?.["مکی"]?.total || 0) + (structure?.revelation?.["مدنی"]?.total || 0);
  $("#structure-total").textContent = `${faNumber(total)} شاهد`;
  const split = structure?.revelation || {};
  $("#revelation-split").innerHTML = ["مکی", "مدنی"].map((type) => {
    const item = split[type] || { total: 0, direct: 0 };
    return `<div class="revelation-stat"><span>${type}</span><b>${faNumber(item.total)}</b><small>${faNumber(item.direct)} مستقیم</small></div>`;
  }).join("");

  const distribution = structure?.distribution || [];
  const maximum = Math.max(1, ...distribution.map((item) => item.total));
  $("#distribution-list").innerHTML = distribution.length
    ? distribution.map((item) => `<div class="distribution-row">
        <span title="${escapeHTML(item.name)}">${escapeHTML(item.name)}</span>
        <span class="distribution-bar"><i style="width:${Math.max(6, (item.total / maximum) * 100)}%"></i></span>
        <b>${faNumber(item.total)}</b>
      </div>`).join("")
    : '<p class="cluster-empty">داده‌ای برای نمایش نیست.</p>';

  const clusters = structure?.clusters || [];
  $("#cluster-list").innerHTML = clusters.length
    ? clusters.map((cluster) => `<div class="cluster-item"><span>${escapeHTML(cluster.reference)}</span><b>${faNumber(cluster.count)} شاهد در ${faNumber(cluster.span)} آیه</b></div>`).join("")
    : '<p class="cluster-empty">خوشهٔ خطیِ چندآیه‌ای در این بازیابی دیده نشد.</p>';
  $("#structure-note").textContent = structure?.note || "";
}

function renderFramework(data) {
  $("#framework-notice").textContent = data.notice || "";
  $("#framework-grid").innerHTML = (data.categories || []).map((category, index) => `<article class="framework-card">
    <span class="framework-index">${faNumber(index + 1)}</span>
    <h3>${escapeHTML(category.title)}</h3>
    <p>${escapeHTML(category.description)}</p>
    <div class="framework-topics">${(category.topics || []).map((topic) => `<button type="button" class="framework-topic" data-framework-query="${escapeHTML(topic)}">${escapeHTML(topic)}</button>`).join("")}</div>
  </article>`).join("");
  $("#protocol-list").innerHTML = (data.protocol || []).map((item) => `<article class="protocol-item">
    <b>${escapeHTML(item.title)}</b>
    <p>${escapeHTML(item.description)}</p>
    <span>${escapeHTML(item.availability)}</span>
  </article>`).join("");
}

async function loadFramework() {
  try {
    const response = await fetch(apiUrl("/api/framework"));
    if (!response.ok) throw new Error("framework unavailable");
    renderFramework(await response.json());
  } catch {
    try {
      const response = await fetch(OFFLINE_FRAMEWORK_URL);
      if (!response.ok) throw new Error("offline framework unavailable");
      renderFramework(await response.json());
    } catch {
      $("#framework-notice").textContent = "چارچوب پژوهش در دسترس نیست؛ جست‌وجوی متنی همچنان فعال است.";
      $("#framework-grid").innerHTML = '<p class="cluster-empty">لطفاً اتصال را دوباره بررسی کنید.</p>';
    }
  }
}

function addSvgElement(parent, name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  parent.appendChild(element);
  return element;
}

function ringCoordinates(ids, radius, startAngle, centerX = 310, centerY = 215) {
  const count = Math.max(ids.length, 1);
  return Object.fromEntries(ids.map((id, index) => {
    const angle = startAngle + (Math.PI * 2 * index) / count;
    return [id, [centerX + radius * Math.cos(angle), centerY + radius * Math.sin(angle)]];
  }));
}

function nodePositions(nodes) {
  const positions = { topic: [310, 215] };
  const groups = {
    verse: nodes.filter((node) => node.kind === "verse").map((node) => node.id),
    term: nodes.filter((node) => node.kind === "term").map((node) => node.id),
    story: nodes.filter((node) => node.kind === "story").map((node) => node.id),
    surah: nodes.filter((node) => node.kind === "surah").map((node) => node.id),
  };
  Object.assign(positions, ringCoordinates(groups.verse, 65, -Math.PI / 2));
  Object.assign(positions, ringCoordinates(groups.term, 112, -Math.PI / 2 + 0.35));
  Object.assign(positions, ringCoordinates(groups.story, 146, Math.PI / 4));
  Object.assign(positions, ringCoordinates(groups.surah, 184, -Math.PI / 2));
  return positions;
}

function graphLabel(node) {
  if (node.kind === "verse") {
    const chunks = node.label.split(" ");
    return chunks.length > 1 ? [chunks.slice(0, -1).join(" "), chunks.at(-1)] : [node.label];
  }
  return [node.label];
}

function renderArc(graph) {
  const arc = $("#arc-view");
  arc.innerHTML = (graph.reading_arc || []).map((step, index) => `<article class="arc-step" data-stage="${faNumber(index + 1)}">
    <b>${escapeHTML(step.title)}</b>
    <p>${escapeHTML(step.body)}</p>
  </article>`).join("");
}

function renderGraphMetrics(graph) {
  const metrics = graph.metrics || {};
  const items = [
    [metrics.lexical_terms, "واژهٔ پل"],
    [metrics.surah_connections, "سورهٔ پیوندی"],
    [metrics.narrative_paths, "مسیر روایی"],
    [metrics.story_lexical_hits, "شاهد در داستان"],
  ];
  $("#graph-metrics").innerHTML = items.map(([value, label]) => `<div class="graph-metric"><b>${faNumber(value)}</b><span>${escapeHTML(label)}</span></div>`).join("");
  $("#graph-note").textContent = graph.notice || "";
}

function renderGraph(graph) {
  const svg = $("#graph");
  svg.replaceChildren();
  if (!graph || !graph.nodes.length) return;
  const positions = nodePositions(graph.nodes);

  graph.edges.forEach((edge) => {
    const [x1, y1] = positions[edge.source] || [0, 0];
    const [x2, y2] = positions[edge.target] || [0, 0];
    const line = addSvgElement(svg, "line", { x1, y1, x2, y2, class: "graph-line" });
    const title = addSvgElement(line, "title");
    title.textContent = edge.label;
  });

  graph.nodes.forEach((node) => {
    const [x, y] = positions[node.id] || [310, 215];
    const radii = { topic: 37, term: 29, story: 29, surah: 26, verse: 20 };
    const radius = radii[node.kind] || 24;
    const group = addSvgElement(svg, "g", { class: `graph-node node-${node.kind}`, transform: `translate(${x} ${y})`, tabindex: "0" });
    const title = addSvgElement(group, "title");
    title.textContent = `${node.label} — ${node.meta}`;
    addSvgElement(group, "circle", { r: radius });
    const labels = graphLabel(node);
    const startingY = labels.length === 1 ? -2 : -6;
    labels.forEach((label, index) => {
      const text = addSvgElement(group, "text", { y: startingY + index * 11, class: "node-title" });
      text.textContent = label.length > 13 ? `${label.slice(0, 12)}…` : label;
    });
    const meta = addSvgElement(group, "text", { y: labels.length === 1 ? 13 : 16, class: "node-meta" });
    meta.textContent = node.meta.length > 17 ? `${node.meta.slice(0, 16)}…` : node.meta;
  });
  renderArc(graph);
  renderGraphMetrics(graph);
}

function setGraphView(view) {
  const network = $("#network-view");
  const arc = $("#arc-view");
  network.hidden = view !== "network";
  arc.hidden = view !== "arc";
  document.querySelectorAll("[data-graph-view]").forEach((button) => {
    const active = button.dataset.graphView === view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
}

function renderReflection(reflection) {
  if (!reflection) return;
  $("#reflection-title").textContent = reflection.title || "تأمل کاربردی";
  $("#reflection-focus").textContent = reflection.focus || "";
  $("#reflection-list").innerHTML = (reflection.prompts || []).map((prompt) => `<li>${escapeHTML(prompt)}</li>`).join("");
  $("#reflection-notice").textContent = reflection.notice || "";
}

function render(data) {
  state.data = data;
  state.filter = "all";
  $("#topic-label").textContent = data.canonical_topic || data.query;
  $("#summary-text").textContent = data.summary;
  $("#topic-description").textContent = data.topic_description || "";
  $("#corpus-note").textContent = `${faNumber(data.corpus.total_verses)} آیه · عربی و ترجمهٔ فارسی`;
  $("#result-quality").textContent = data.mode?.label || "مسیر قابل ممیزی";
  modeSelect.value = data.mode?.id || modeSelect.value;

  const expansion = $("#expansion-row");
  expansion.innerHTML = (data.expansion || [])
    .map((label) => `<span>${escapeHTML(label)}</span>`)
    .join("");
  renderStats(data.stats);
  renderVerses();
  const available = data.stats.direct + data.stats.thematic;
  const loadMore = $("#load-more");
  loadMore.hidden = !available || data.stats.shown >= available || state.limit >= 24;
  if (!loadMore.hidden) {
    const remaining = Math.min(12, 24 - state.limit, available - data.stats.shown);
    loadMore.innerHTML = `نمایش ${faNumber(remaining)} آیهٔ بیشتر <span>↓</span>`;
  }
  renderContext(data.context);
  renderNarrative(data.narrative);
  renderStructure(data.structure);
  renderGraph(data.graph);
  renderReflection(data.reflection);
  $("#questions-list").innerHTML = data.questions.map((question) => `<li>${escapeHTML(question)}</li>`).join("");
  $("#method-list").innerHTML = data.method.steps.map((step) => `<li>${escapeHTML(step)}</li>`).join("");

  document.querySelectorAll(".filter-tabs button").forEach((button) => {
    const active = button.dataset.filter === "all";
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
}

async function research(query, scroll = false, limit = 12) {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    showError("لطفاً یک واژه یا موضوع بنویسید.");
    input.focus();
    return;
  }
  input.value = cleanQuery;
  state.limit = limit;
  loading();
  try {
    const response = await fetch(apiUrl("/api/analyze"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: cleanQuery, limit, include_context: true, mode: modeSelect.value }),
    });
    const payload = await response.json();
    if (!response.ok) {
      const apiError = new Error(payload.detail || "دریافت نتیجه ناموفق بود.");
      apiError.validation = response.status === 422;
      throw apiError;
    }
    render(payload);
    if (scroll) $("#research").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    if (!error.validation) {
      try {
        const fallback = await offlineAnalyze(cleanQuery, limit);
        render(fallback);
        showOfflineNotice();
        if (scroll) $("#research").scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      } catch {
        // Use the regular error state below if neither online nor offline research is available.
      }
    }
    resultsList.innerHTML = `<div class="empty-results"><b>اتصال به موتور پژوهش برقرار نشد.</b>لطفاً دوباره تلاش کنید.</div>`;
    showError(error.message || "خطای پیش‌بینی‌نشده رخ داد.");
  } finally {
    submit.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  research(input.value, true);
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => research(button.dataset.query, true));
});

$("#framework-grid").addEventListener("click", (event) => {
  const button = event.target.closest("[data-framework-query]");
  if (!button) return;
  input.value = button.dataset.frameworkQuery;
  modeSelect.value = "topic";
  research(button.dataset.frameworkQuery, true);
});

$("#load-more").addEventListener("click", () => {
  if (!state.data) return;
  research(state.data.query, false, Math.min(24, state.limit + 12));
});

$("#export-research").addEventListener("click", () => {
  if (!state.data) return;
  if (state.data.offline) {
    showError("گزارش Markdownِ قابل ممیزی به سرور پژوهش نیاز دارد. برای گزارش کامل، اتصال HTTPS را از نشان بالای صفحه تنظیم کنید.");
    return;
  }
  const params = new URLSearchParams({ q: state.data.query, mode: modeSelect.value });
  window.location.assign(`${apiUrl("/api/export/markdown")}?${params.toString()}`);
});

document.querySelectorAll(".filter-tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter-tabs button").forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    renderVerses();
  });
});

resultsList.addEventListener("click", async (event) => {
  const saveButton = event.target.closest("[data-save]");
  if (saveButton && state.data) {
    const verse = state.data.verses.find((item) => item.id === saveButton.dataset.save);
    if (verse && saveVerse(verse)) {
      saveButton.textContent = "در دفتر ✓";
      saveButton.classList.add("saved");
      saveButton.disabled = true;
    }
    return;
  }

  const button = event.target.closest("[data-copy]");
  if (!button || !state.data) return;
  const verse = state.data.verses.find((item) => item.id === button.dataset.copy);
  if (!verse) return;
  const citation = `${verse.reference}\n${verse.arabic}\n${verse.persian}`;
  try {
    await navigator.clipboard.writeText(citation);
    button.textContent = "کپی شد ✓";
  } catch {
    button.textContent = "متن را انتخاب کنید";
  }
  window.setTimeout(() => { button.textContent = "کپی شاهد ↗"; }, 1600);
});

$("#narrative-list").addEventListener("click", (event) => {
  const button = event.target.closest("[data-save-narrative]");
  if (!button || !state.data) return;
  const path = state.data.narrative?.paths?.find((item) => item.id === button.dataset.saveNarrative);
  if (path && saveVerse(path)) {
    button.textContent = "در دفتر ✓";
    button.classList.add("saved");
    button.disabled = true;
  }
});

$("#notebook-list").addEventListener("click", (event) => {
  const editButton = event.target.closest("[data-edit-note]");
  if (editButton) {
    const item = notebook.find((entry) => entry.id === editButton.dataset.editNote);
    if (!item) return;
    const note = window.prompt("یادداشت پژوهشی یا منبع تفسیر را با نام اثر، جلد و صفحه ثبت کنید:", item.note || "");
    if (note === null) return;
    item.note = note.trim().slice(0, 1000);
    persistNotebook();
    renderNotebook();
    return;
  }
  const button = event.target.closest("[data-remove-note]");
  if (!button) return;
  notebook = notebook.filter((item) => item.id !== button.dataset.removeNote);
  persistNotebook();
  renderNotebook();
  renderVerses();
});

$("#export-notebook").addEventListener("click", () => {
  if (!notebook.length) return;
  const today = new Intl.DateTimeFormat("fa-IR", { dateStyle: "long" }).format(new Date());
  const body = [
    "# دفتر شواهد ذهن‌یار",
    "",
    `تاریخ خروجی: ${today}`,
    "",
    ...notebook.flatMap((item) => [
      `## ${item.reference}`,
      "",
      item.arabic,
      "",
      item.persian,
      "",
      `پرسش هنگام ذخیره: ${item.query || "—"}`,
      `یادداشت / منبع: ${item.note || "—"}`,
      "",
    ]),
  ].join("\n");
  const blob = new Blob([body], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "zehnyar-evidence-notebook.md";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
});

$("#clear-notebook").addEventListener("click", () => {
  if (!notebook.length || !window.confirm("همهٔ شواهد ذخیره‌شده از همین مرورگر پاک شوند؟")) return;
  notebook = [];
  persistNotebook();
  renderNotebook();
  renderVerses();
});

document.querySelectorAll("[data-graph-view]").forEach((button) => {
  button.addEventListener("click", () => setGraphView(button.dataset.graphView));
});

$("#connection-settings").addEventListener("click", () => {
  const current = localStorage.getItem(API_BASE_KEY) || "";
  const value = window.prompt("آدرس HTTPS سرور ذهن‌یار را وارد کنید. برای بازگشت به حالت آفلاین، مقدار را خالی بگذارید:", current);
  if (value === null) return;
  const normalized = value.trim().replace(/\/$/, "");
  if (!normalized) {
    localStorage.removeItem(API_BASE_KEY);
    updateConnectionLabel();
    research(input.value);
    return;
  }
  if (!/^https:\/\/[^\s/]+/i.test(normalized)) {
    showError("برای اتصال امن، آدرس HTTPS کامل سرور را وارد کنید.");
    return;
  }
  localStorage.setItem(API_BASE_KEY, normalized);
  updateConnectionLabel();
  loadFramework();
  research(input.value);
});

$("#graph-info").addEventListener("click", () => {
  const help = $("#graph-help");
  help.hidden = !help.hidden;
  $("#graph-info").setAttribute("aria-expanded", String(!help.hidden));
});

$("#method-toggle").addEventListener("click", () => {
  const content = $("#method-content");
  const button = $("#method-toggle");
  content.hidden = !content.hidden;
  button.setAttribute("aria-expanded", String(!content.hidden));
});

if ("serviceWorker" in navigator && /^(https?:)$/.test(window.location.protocol)) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}

renderNotebook();
updateConnectionLabel();
setGraphView("network");
loadFramework();
research(input.value);
