const api = "/api/analyze";
const state = { data: null, filter: "all" };

const $ = (selector) => document.querySelector(selector);
const form = $("#search-form");
const input = $("#query");
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

function loading() {
  const template = $("#loading-template");
  resultsList.replaceChildren(template.content.cloneNode(true));
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
    .map(([value, label]) => `<div class="stat"><strong>${escapeHTML(value)}</strong><span>${escapeHTML(label)}</span></div>`)
    .join("");
}

function verseCard(verse, index, context = false) {
  if (context) {
    return `<article class="context-item">
      <div class="context-ref">${escapeHTML(verse.reference)} · ${escapeHTML(verse.revelation)}</div>
      <p>${escapeHTML(verse.persian)}</p>
    </article>`;
  }
  const matchMarkup = verse.matches
    .map((match) => `<span>${escapeHTML(match)}</span>`)
    .join("");
  return `<article class="verse-card" data-verse-id="${escapeHTML(verse.id)}" style="animation-delay:${Math.min(index, 9) * 35}ms">
    <div class="verse-head">
      <span class="reference">${escapeHTML(verse.reference)} <small>· ${escapeHTML(verse.revelation)}</small></span>
      <span class="relation ${relationClass(verse)}">${escapeHTML(verse.relation)}</span>
    </div>
    <p class="verse-arabic" lang="ar" dir="rtl">${escapeHTML(verse.arabic)}</p>
    <p class="verse-persian">${escapeHTML(verse.persian)}</p>
    <div class="verse-foot">
      <div class="match-list">${matchMarkup}</div>
      <button class="copy-verse" type="button" data-copy="${escapeHTML(verse.id)}" aria-label="کپی ارجاع ${escapeHTML(verse.reference)}">کپی شاهد ↗</button>
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
  $("#corpus-note").textContent = `${data.corpus.total_verses.toLocaleString("fa-IR")} آیه · عربی و ترجمهٔ فارسی`;
  $("#result-quality").textContent = data.canonical_topic ? "گسترش واژگانیِ آشکار" : "بازیابی واژگانیِ آزاد";

  const expansion = $("#expansion-row");
  expansion.innerHTML = (data.expansion || [])
    .map((label) => `<span>${escapeHTML(label)}</span>`)
    .join("");
  renderStats(data.stats);
  renderVerses();
  renderContext(data.context);
  renderGraph(data.graph);
  $("#questions-list").innerHTML = data.questions.map((question) => `<li>${escapeHTML(question)}</li>`).join("");
  $("#method-list").innerHTML = data.method.steps.map((step) => `<li>${escapeHTML(step)}</li>`).join("");

  document.querySelectorAll(".filter-tabs button").forEach((button) => {
    const active = button.dataset.filter === "all";
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
}

async function research(query, scroll = false) {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    showError("لطفاً یک واژه یا موضوع بنویسید.");
    input.focus();
    return;
  }
  input.value = cleanQuery;
  loading();
  try {
    const response = await fetch(api, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: cleanQuery, limit: 12, include_context: true }),
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

research(input.value);
