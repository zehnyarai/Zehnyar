const api = "/api/analyze";
const NOTEBOOK_KEY = "zehnyar-evidence-notebook-v1";
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
  submit.disabled = true;
  statusMessage.classList.remove("show");
}

function showError(message) {
  statusMessage.textContent = message;
  statusMessage.classList.add("show");
}

function relationClass(verse) {
  return verse.relation.includes("مستقیم") ? "direct" : "thematic";
}

function renderStats(stats) {
  const items = [
    [stats.direct, "شاهد مستقیم"],
    [stats.thematic, "پیوند موضوعی"],
    [stats.surahs, "سورهٔ درگیر"],
    [stats.shown, "آیهٔ نمایش‌داده‌شده"],
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
  return `<article class="verse-card" data-verse-id="${escapeHTML(verse.id)}" style="animation-delay:${Math.min(index, 9) * 35}ms">
    <div class="verse-head">
      <span class="reference">${escapeHTML(verse.reference)} <small>· ${escapeHTML(verse.revelation)}</small></span>
      <span class="relation ${relationClass(verse)}">${escapeHTML(verse.relation)}</span>
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
    const response = await fetch("/api/framework");
    if (!response.ok) throw new Error("framework unavailable");
    renderFramework(await response.json());
  } catch {
    $("#framework-notice").textContent = "چارچوب پژوهش در دسترس نیست؛ جست‌وجوی متنی همچنان فعال است.";
    $("#framework-grid").innerHTML = '<p class="cluster-empty">لطفاً اتصال را دوباره بررسی کنید.</p>';
  }
}

function addSvgElement(parent, name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  parent.appendChild(element);
  return element;
}

function nodePositions(nodes) {
  const positions = { topic: [310, 195] };
  const term = [[158, 92], [462, 92], [158, 302], [462, 302]];
  const verse = [[72, 198], [548, 198], [310, 43], [310, 347], [73, 56], [547, 335]];
  let termIndex = 0;
  let verseIndex = 0;
  nodes.forEach((node) => {
    if (node.kind === "term") positions[node.id] = term[termIndex++ % term.length];
    if (node.kind === "verse") positions[node.id] = verse[verseIndex++ % verse.length];
  });
  return positions;
}

function graphLabel(node) {
  if (node.kind !== "verse") return [node.label];
  const chunks = node.label.split(" ");
  return chunks.length > 1 ? [chunks.slice(0, -1).join(" "), chunks.at(-1)] : [node.label];
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
    const [x, y] = positions[node.id] || [310, 195];
    const radius = node.kind === "topic" ? 37 : node.kind === "term" ? 30 : 25;
    const group = addSvgElement(svg, "g", { class: `graph-node node-${node.kind}`, transform: `translate(${x} ${y})`, tabindex: "0" });
    const title = addSvgElement(group, "title");
    title.textContent = `${node.label} — ${node.meta}`;
    addSvgElement(group, "circle", { r: radius });
    const labels = graphLabel(node);
    const startingY = labels.length === 1 ? -2 : -6;
    labels.forEach((label, index) => {
      const text = addSvgElement(group, "text", { y: startingY + index * 11, class: "node-title" });
      text.textContent = label.length > 14 ? `${label.slice(0, 13)}…` : label;
    });
    if (node.kind !== "verse") {
      const meta = addSvgElement(group, "text", { y: labels.length === 1 ? 13 : 16, class: "node-meta" });
      meta.textContent = node.meta.length > 18 ? `${node.meta.slice(0, 17)}…` : node.meta;
    }
  });
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
  renderStructure(data.structure);
  renderGraph(data.graph);
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
    const response = await fetch(api, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: cleanQuery, limit, include_context: true, mode: modeSelect.value }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "دریافت نتیجه ناموفق بود.");
    render(payload);
    if (scroll) $("#research").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
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

renderNotebook();
loadFramework();
research(input.value);
