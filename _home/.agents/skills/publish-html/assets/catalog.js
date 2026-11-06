// publish-html catalog runtime, v2. The page embeds every record as JSON; the
// API (html_preview.py serve, behind Caddy at /api/*) only performs changes.
import { mountThemeMenu } from "./theme-menu.js";

const data = JSON.parse(document.getElementById("catalog-data").textContent || '{"documents":[]}');
const docs = data.documents;
const results = document.getElementById("results");
const statusLine = document.getElementById("results-status");
const search = document.getElementById("search");
const sort = document.getElementById("sort");
const layoutKey = "html-preview-layout";
const themeKey = "html-response-theme";
const media = matchMedia("(prefers-color-scheme: dark)");

const state = {
  view: "library",
  layout: readLayout(),
  query: "",
  sort: "created-desc",
  live: false,
};

const icon = (paths) => `<svg viewBox="0 0 24 24" aria-hidden="true">${paths}</svg>`;
const icons = {
  open: icon('<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
  download: icon('<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>'),
  archive: icon('<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v10h14V9M10 13h4"/>'),
  restore: icon('<path d="M4 12a8 8 0 1 0 2.4-5.7L4 8.6"/><path d="M4 4v4.6h4.6"/>'),
  refresh: icon('<path d="M20 12a8 8 0 1 1-2.4-5.7L20 8.6"/><path d="M20 4v4.6h-4.6"/>'),
  remove: icon('<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>'),
};

function readLayout() {
  try { return localStorage.getItem(layoutKey) === "tiles" ? "tiles" : "rows"; } catch { return "rows"; }
}

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function highlight(text) {
  const safe = escapeHtml(text);
  const terms = state.query.trim().split(/\s+/).filter((t) => t.length > 1);
  if (!terms.length) return safe;
  const pattern = new RegExp(`(${terms.map((t) => escapeHtml(t).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  return safe.replace(pattern, "<mark>$1</mark>");
}

const dateFormat = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" });
const monthFormat = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });

function relativeDay(date) {
  const today = new Date();
  const start = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).valueOf();
  const days = Math.round((start(today) - start(date)) / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return dateFormat.format(date);
}

const assetVersion = data.assetVersion ? `?v=${encodeURIComponent(data.assetVersion)}` : "";
function docUrl(doc) { return `d/${encodeURIComponent(doc.id)}/`; }
function docHref(doc) { return `${docUrl(doc)}${assetVersion}`; }

/* ---------- Filtering ---------- */

function visibleDocs() {
  const terms = state.query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const list = docs.filter((doc) => doc.archived === (state.view === "archive")).filter((doc) => {
    if (!terms.length) return true;
    const haystack = `${doc.title} ${doc.summary} ${doc.kicker} ${doc.id}`.toLowerCase();
    return terms.every((term) => haystack.includes(term));
  });
  const [field, direction] = state.sort.split("-");
  const factor = direction === "asc" ? 1 : -1;
  list.sort((a, b) => field === "title"
    ? a.title.localeCompare(b.title) * factor
    : (new Date(a[field]) - new Date(b[field])) * factor);
  return list;
}

function groups(list) {
  if (state.sort.startsWith("title")) return [{ label: null, items: list }];
  const field = state.sort.split("-")[0];
  const map = new Map();
  for (const doc of list) {
    const label = monthFormat.format(new Date(doc[field]));
    if (!map.has(label)) map.set(label, []);
    map.get(label).push(doc);
  }
  return [...map].map(([label, items]) => ({ label, items }));
}

/* ---------- Rendering ---------- */

function actionsMarkup(doc) {
  const label = escapeHtml(doc.title);
  if (doc.archived) {
    return `
      <button class="action" type="button" data-action="unarchive" data-id="${escapeHtml(doc.id)}" aria-label="Restore ${label}">${icons.restore}<span class="action-label">Restore</span></button>
      <button class="action danger" type="button" data-action="remove" data-id="${escapeHtml(doc.id)}" aria-label="Delete ${label} permanently">${icons.remove}<span class="action-label">Delete</span></button>`;
  }
  return `
    <button class="action" type="button" data-action="thumbnail" data-id="${escapeHtml(doc.id)}" title="Refresh thumbnail" aria-label="Refresh thumbnail for ${label}">${icons.refresh}</button>
    <a class="action" href="${docUrl(doc)}download.html" download title="Download HTML" aria-label="Download ${label}">${icons.download}</a>
    <button class="action" type="button" data-action="archive" data-id="${escapeHtml(doc.id)}" title="Archive" aria-label="Archive ${label}">${icons.archive}</button>
    <button class="action danger" type="button" data-action="remove" data-id="${escapeHtml(doc.id)}" title="Delete" aria-label="Delete ${label} permanently">${icons.remove}</button>`;
}

function thumbSrc(doc) {
  const thumbs = doc.thumbs || {};
  const dark = document.documentElement.dataset.resolvedTheme === "dark" && thumbs.dark;
  const version = dark ? thumbs.dark : thumbs.light;
  if (!version) return null;
  return `${docUrl(doc)}${dark ? "thumb-dark.png" : "thumb.png"}?t=${version}`;
}

function thumbMarkup(doc) {
  const busy = refreshing.has(doc.id) ? " is-refreshing" : "";
  const src = thumbSrc(doc);
  if (src) return `<div class="thumb${busy}"><img src="${src}" alt="" loading="lazy" decoding="async"></div>`;
  return `<div class="thumb${busy}"><iframe src="${docHref(doc)}" title="" loading="lazy" scrolling="no" sandbox="allow-same-origin" tabindex="-1" aria-hidden="true"></iframe></div>`;
}

function metaMarkup(doc) {
  const created = new Date(doc.created);
  const updated = new Date(doc.updated);
  const edited = updated - created > 3600_000 ? `<span>Edited ${relativeDay(updated).replace(/^(Today|Yesterday)$/, (w) => w.toLowerCase())}</span>` : "";
  // The ID is noise while scanning; show it only when the search matched it.
  const terms = state.query.trim().toLowerCase().split(/\s+/).filter((t) => t.length > 1);
  const idMatch = terms.some((t) => doc.id.toLowerCase().includes(t));
  return `<div class="row-meta"><time datetime="${doc.created}">${relativeDay(created)}</time>${edited}${idMatch ? `<code>${highlight(doc.id)}</code>` : ""}</div>`;
}

function rowMarkup(doc) {
  const title = doc.archived
    ? `<h3>${highlight(doc.title)}</h3>`
    : `<h3><a href="${docHref(doc)}">${highlight(doc.title)}</a></h3>`;
  return `<article class="row" data-id="${escapeHtml(doc.id)}">
    ${doc.archived ? "" : thumbMarkup(doc)}
    <div>
      ${doc.kicker ? `<p class="kicker">${highlight(doc.kicker)}</p>` : ""}
      ${title}
      ${doc.summary ? `<p class="summary">${highlight(doc.summary)}</p>` : ""}
      ${metaMarkup(doc)}
    </div>
    <div class="row-actions">${actionsMarkup(doc)}</div>
  </article>`;
}

function tileMarkup(doc) {
  return `<article class="tile" data-id="${escapeHtml(doc.id)}">
    ${thumbMarkup(doc)}
    <div class="tile-actions">${actionsMarkup(doc)}</div>
    <div class="tile-info">
      ${doc.kicker ? `<p class="kicker">${highlight(doc.kicker)}</p>` : ""}
      <h3><a href="${docHref(doc)}">${highlight(doc.title)}</a></h3>
      ${metaMarkup(doc)}
    </div>
  </article>`;
}

function render() {
  const list = visibleDocs();
  const libraryCount = docs.filter((d) => !d.archived).length;
  const archiveCount = docs.length - libraryCount;
  document.getElementById("count-library").textContent = libraryCount;
  document.getElementById("count-archive").textContent = archiveCount;

  const newest = docs.filter((d) => !d.archived).map((d) => new Date(d.created)).sort((a, b) => b - a)[0];
  const when = newest ? relativeDay(newest) : "";
  const phrase = /^(Today|Yesterday|\d+ days ago)$/.test(when) ? when.toLowerCase() : `on ${when}`;
  document.getElementById("catalog-summary").textContent = libraryCount
    ? `${libraryCount} documents in the library. The latest was published ${phrase}.`
    : "No documents yet.";

  statusLine.textContent = state.query
    ? `${list.length} of ${state.view === "archive" ? archiveCount : libraryCount} match “${state.query.trim()}”`
    : "";

  if (!list.length) {
    results.innerHTML = state.query
      ? `<div class="empty"><h2>Nothing matches “${escapeHtml(state.query.trim())}”</h2><p>Search covers titles, summaries, kickers, and document IDs.</p><button class="action" type="button" data-clear>Clear search</button></div>`
      : state.view === "archive"
        ? `<div class="empty"><h2>The archive is empty</h2><p>Archived documents leave the library but keep their files, so you can restore them here.</p></div>`
        : `<div class="empty"><h2>Nothing published yet</h2><p>Ask an agent to run <code>/publish-html</code> and the document appears here.</p></div>`;
    return;
  }

  const useTiles = state.layout === "tiles" && state.view === "library";
  results.innerHTML = groups(list).map(({ label, items }) => `
    <section class="group">
      ${label ? `<h2 class="group-head">${escapeHtml(label)} <span>${items.length}</span></h2>` : ""}
      <div class="${useTiles ? `tiles${state.query.trim() ? " searching" : ""}` : `rows${state.view === "archive" ? " archived" : ""}`}">
        ${items.map(useTiles ? tileMarkup : rowMarkup).join("")}
      </div>
    </section>`).join("");
  scaleThumbs();
}

/* Thumbnails render the page at 1280px and scale to the frame width. */
const thumbObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    entry.target.style.setProperty("--thumb-scale", (entry.contentRect.width / 1280).toFixed(4));
  }
});
function scaleThumbs() {
  thumbObserver.disconnect();
  results.querySelectorAll(".thumb").forEach((thumb) => thumbObserver.observe(thumb));
}

/* ---------- Actions ---------- */

async function api(path, id) {
  await apiReady;
  if (!state.live) throw new Error("the catalog API isn’t reachable. Start html-preview-api.service");
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Requested-With": "html-preview-catalog" },
    body: JSON.stringify(id === undefined ? {} : { id }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `${response.status} ${response.statusText}`);
  return body;
}

function toast(message, undo) {
  const region = document.querySelector(".toast-region");
  region.innerHTML = "";
  const element = document.createElement("div");
  element.className = "catalog-toast";
  element.innerHTML = `<span>${escapeHtml(message)}</span>`;
  if (undo) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Undo";
    button.addEventListener("click", () => { element.remove(); undo(); });
    element.append(button);
  }
  region.append(element);
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.remove(), undo ? 6000 : 3000);
}

async function setArchived(doc, archived, { quiet = false } = {}) {
  try {
    await api(archived ? "/api/archive" : "/api/unarchive", doc.id);
    doc.archived = archived;
    render();
    if (quiet) return;
    toast(
      archived ? `Archived “${doc.title}”` : `Restored “${doc.title}” to the library`,
      () => setArchived(doc, !archived, { quiet: true }),
    );
  } catch (error) {
    toast(`Could not ${archived ? "archive" : "restore"}: ${error.message}`);
  }
}

async function removeDoc(doc, button) {
  if (button.dataset.confirm !== "true") {
    button.dataset.confirm = "true";
    button.innerHTML = `${icons.remove}<span>Delete forever?</span>`;
    clearTimeout(button.timer);
    button.timer = setTimeout(() => render(), 4000);
    return;
  }
  try {
    await api("/api/remove", doc.id);
    docs.splice(docs.indexOf(doc), 1);
    render();
    toast(`Deleted “${doc.title}”`);
  } catch (error) {
    toast(`Could not delete: ${error.message}`);
  }
}

/* ---------- Thumbnails ---------- */

const refreshing = new Set();
const refreshAllButton = document.getElementById("refresh-thumbs");

async function refreshThumbnails(doc) {
  const targets = doc ? [doc] : docs.filter((d) => !d.archived);
  if (!targets.length || targets.some((d) => refreshing.has(d.id))) return;
  targets.forEach((d) => refreshing.add(d.id));
  if (!doc) { refreshAllButton.disabled = true; refreshAllButton.classList.add("is-busy"); }
  render();
  if (!doc) toast(`Refreshing ${targets.length} thumbnails…`);
  try {
    const body = await api("/api/thumbnails", doc ? doc.id : undefined);
    for (const [id, thumbs] of Object.entries(body.thumbs || {})) {
      const match = docs.find((d) => d.id === id);
      if (match) match.thumbs = thumbs;
    }
    const failed = Object.keys(body.errors || {}).length;
    toast(failed
      ? `${failed} thumbnail${failed === 1 ? "" : "s"} failed: ${Object.values(body.errors)[0]}`
      : doc ? `Refreshed the thumbnail for “${doc.title}”` : `Refreshed ${targets.length} thumbnails`);
  } catch (error) {
    toast(`Could not refresh thumbnails: ${error.message}`);
  } finally {
    targets.forEach((d) => refreshing.delete(d.id));
    if (!doc) { refreshAllButton.disabled = false; refreshAllButton.classList.remove("is-busy"); }
    render();
  }
}

refreshAllButton.addEventListener("click", () => refreshThumbnails());

results.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (event.target.closest("[data-clear]")) { search.value = ""; state.query = ""; render(); search.focus(); return; }
  if (!button) return;
  const doc = docs.find((d) => d.id === button.dataset.id);
  if (!doc) return;
  event.preventDefault();
  if (button.dataset.action === "archive") setArchived(doc, true);
  if (button.dataset.action === "unarchive") setArchived(doc, false);
  if (button.dataset.action === "remove") removeDoc(doc, button);
  if (button.dataset.action === "thumbnail") refreshThumbnails(doc);
});

/* ---------- Controls ---------- */

document.querySelectorAll("[role=tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    state.view = tab.dataset.view;
    document.querySelectorAll("[role=tab]").forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
    results.setAttribute("aria-labelledby", tab.id);
    document.querySelector(".segmented").hidden = state.view === "archive";
    refreshAllButton.hidden = state.view === "archive";
    render();
  });
});

document.querySelectorAll("[data-layout]").forEach((button) => {
  button.setAttribute("aria-pressed", String(button.dataset.layout === state.layout));
  button.addEventListener("click", () => {
    state.layout = button.dataset.layout;
    try { localStorage.setItem(layoutKey, state.layout); } catch {}
    document.querySelectorAll("[data-layout]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
    render();
  });
});

search.addEventListener("input", () => { state.query = search.value; render(); });
sort.addEventListener("change", () => { state.sort = sort.value; render(); });

document.addEventListener("keydown", (event) => {
  const typing = event.target.closest("input, select, textarea");
  if (event.key === "/" && !typing) { event.preventDefault(); search.focus(); search.select(); }
  if (event.key === "Escape" && event.target === search) { search.value = ""; state.query = ""; render(); search.blur(); }
});

/* ---------- Theme ---------- */

function applyTheme(theme, persist = true) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.dataset.resolvedTheme = theme === "system" ? (media.matches ? "dark" : "light") : theme;
  if (persist) { try { localStorage.setItem(themeKey, theme); } catch {} }
  render();
}
mountThemeMenu(document.getElementById("theme-menu"), {
  current: document.documentElement.dataset.theme || "system",
  placement: "down",
  align: "end",
  buttonClass: "icon-button",
  onSelect: (theme) => applyTheme(theme),
});
media.addEventListener("change", () => { if (document.documentElement.dataset.theme === "system") applyTheme("system", false); });
applyTheme(document.documentElement.dataset.theme || "system", false);

/* ---------- Boot ---------- */

const apiReady = fetch("/api/health", { cache: "no-store" })
  .then((response) => { state.live = response.ok && response.headers.get("content-type")?.includes("json"); })
  .catch(() => { state.live = false; });

render();
