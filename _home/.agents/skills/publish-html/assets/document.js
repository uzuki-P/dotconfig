// publish-html document runtime, v2.
// Adds the reading chrome (outline rail, progress, meta line), code
// highlighting and copy, Mermaid rendering, and pan/zoom for every diagram.

const media = window.matchMedia("(prefers-color-scheme: dark)");
const themeKey = "html-response-theme";
const themeOrder = ["system", "light", "dark"];
let mermaidApi = null;
let diagramSerial = 0;

const icon = (paths) => `<svg viewBox="0 0 24 24" aria-hidden="true">${paths}</svg>`;
const icons = {
  home: icon('<path d="M4 11 12 4l8 7"/><path d="M6 9.5V20h12V9.5"/>'),
  contents: icon('<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>'),
  download: icon('<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>'),
  system: icon('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'),
  light: icon('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  dark: icon('<path d="M20.4 15.5A9 9 0 0 1 8.5 3.6a9 9 0 1 0 11.9 11.9Z"/>'),
  minus: icon('<path d="M6 12h12"/>'),
  plus: icon('<path d="M6 12h12M12 6v12"/>'),
  image: icon('<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="m21 16-5-5-9 9"/>'),
  expand: icon('<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>'),
};

/* ---------- Theme ---------- */

function storedTheme() {
  try {
    const value = localStorage.getItem(themeKey);
    return themeOrder.includes(value) ? value : "system";
  } catch {
    return "system";
  }
}

function resolvedTheme(theme) {
  return theme === "system" ? (media.matches ? "dark" : "light") : theme;
}

function applyTheme(theme, persist = true) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.dataset.resolvedTheme = resolvedTheme(theme);
  const button = document.querySelector("[data-tool='theme']");
  if (button) {
    const next = themeOrder[(themeOrder.indexOf(theme) + 1) % themeOrder.length];
    button.innerHTML = icons[theme];
    button.title = `Theme: ${theme}. Switch to ${next}`;
    button.setAttribute("aria-label", `Theme: ${theme}. Switch to ${next}`);
  }
  if (persist) {
    try { localStorage.setItem(themeKey, theme); } catch { /* storage may be blocked */ }
  }
}

/* ---------- Headings, meta line, contents ---------- */

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "section";
}

function topSections() {
  return [...document.querySelectorAll(".document > .section")]
    .map((section, index) => ({ section, heading: section.querySelector("h2"), number: index + 1 }))
    .filter((entry) => entry.heading);
}

function setupAnchors(entries) {
  const used = new Set();
  for (const { heading } of entries) {
    let id = heading.id || slugify(heading.textContent || "");
    while (used.has(id) || (document.getElementById(id) && document.getElementById(id) !== heading)) id += "-x";
    used.add(id);
    heading.id = id;
    const anchor = document.createElement("a");
    anchor.className = "heading-anchor";
    anchor.href = `#${id}`;
    anchor.textContent = "#";
    anchor.setAttribute("aria-label", `Link to ${heading.textContent?.trim()}`);
    heading.append(anchor);
  }
}

function publishedDate() {
  const match = location.pathname.match(/\/d\/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})-/);
  if (match) {
    const [, y, mo, d, h, mi, s] = match;
    return new Date(Date.UTC(+y, +mo - 1, +d, +h, +mi, +s));
  }
  const meta = document.querySelector('meta[name="published"]')?.getAttribute("content");
  return meta ? new Date(meta) : null;
}

function setupMetaLine(entries) {
  const hero = document.querySelector(".document > .hero");
  if (!hero || hero.querySelector(".doc-meta")) return;
  const words = (document.querySelector(".document")?.innerText || "").split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.round(words / 230));
  const items = [];
  const date = publishedDate();
  if (date && !Number.isNaN(date.valueOf())) {
    const label = date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
    items.push(`Published <time datetime="${date.toISOString()}"><strong>${label}</strong></time>`);
  }
  items.push(`<strong>${minutes} min</strong> read`);
  if (entries.length > 1) items.push(`<strong>${entries.length}</strong> sections`);
  const list = document.createElement("ul");
  list.className = "doc-meta";
  list.setAttribute("aria-label", "Document details");
  list.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
  hero.append(list);
}


/* ---------- Reading chrome: outline rail ---------- */
// Wide screens: a sticky left rail with the outline, per-section progress, and tools.
// Narrow screens: a bottom bar whose contents button opens the outline as a sheet.

function headingText(heading) {
  return [...heading.childNodes]
    .filter((n) => !(n.nodeType === 1 && n.classList.contains("heading-anchor")))
    .map((n) => n.textContent).join("").trim();
}

const escapeText = (value) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;");

function setupToolbar(entries) {
  const root = document.documentElement;
  root.classList.add("has-rail");
  const progress = document.createElement("div");
  progress.className = "read-progress";
  progress.setAttribute("aria-hidden", "true");

  const title = document.querySelector(".document h1")?.textContent?.trim() || document.title;
  const rail = document.createElement("aside");
  rail.className = "doc-rail";
  rail.setAttribute("aria-label", "Document outline and tools");
  rail.innerHTML = `
    <a class="tool rail-home" href="/" title="All documents" aria-label="All documents">${icons.home}<span class="tool-label">All documents</span></a>
    <p class="rail-title">${escapeText(title)}</p>
    ${entries.length ? `
      <button type="button" class="tool rail-toggle" aria-expanded="false" aria-controls="rail-outline" aria-label="Contents" title="Contents">${icons.contents}<span class="rail-position">1 of ${entries.length}</span></button>
      <nav class="rail-outline" id="rail-outline" aria-label="Sections">${entries.map(({ heading, number }) =>
        `<a href="#${heading.id}" data-section="${number}"><span>${number}</span><span>${escapeText(headingText(heading))}</span></a>`).join("")}</nav>`
      : "<span></span>"}
    <div class="rail-tools">
      <button type="button" class="tool" data-tool="download" title="Download HTML" aria-label="Download HTML">${icons.download}</button>
      <button type="button" class="tool" data-tool="theme" title="Theme" aria-label="Theme">${icons.system}</button>
    </div>`;
  document.body.prepend(rail);
  document.body.append(progress);

  rail.querySelector("[data-tool='download']").addEventListener("click", (event) => downloadDocument(event.currentTarget));
  rail.querySelector("[data-tool='theme']").addEventListener("click", async () => {
    const current = root.dataset.theme || "system";
    applyTheme(themeOrder[(themeOrder.indexOf(current) + 1) % themeOrder.length]);
    if (mermaidApi) await renderDiagrams();
  });

  const toggle = rail.querySelector(".rail-toggle");
  const outline = rail.querySelector(".rail-outline");
  const setOpen = (open) => {
    root.classList.toggle("rail-open", open);
    toggle?.setAttribute("aria-expanded", String(open));
    if (open) (outline.querySelector('[aria-current="true"]') || outline.querySelector("a"))?.focus();
  };
  toggle?.addEventListener("click", () => setOpen(!root.classList.contains("rail-open")));
  outline?.addEventListener("click", (event) => { if (event.target.closest("a")) setOpen(false); });
  document.addEventListener("click", (event) => {
    if (root.classList.contains("rail-open") && !rail.contains(event.target)) setOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.classList.contains("rail-open")) { setOpen(false); toggle?.focus(); }
  });

  const links = outline ? [...outline.querySelectorAll("a")] : [];
  const position = rail.querySelector(".rail-position");
  let ticking = false;
  let lastActive = null;
  const update = () => {
    ticking = false;
    const max = root.scrollHeight - innerHeight;
    progress.style.setProperty("--progress", max > 0 ? Math.min(1, scrollY / max).toFixed(4) : "0");
    if (!entries.length) return;
    const line = innerHeight * 0.3;
    let active = entries[0];
    entries.forEach((entry, index) => {
      const box = entry.section.getBoundingClientRect();
      if (box.top <= line) active = entry;
      const read = Math.min(1, Math.max(0, (line - box.top) / Math.max(1, box.height)));
      links[index]?.style.setProperty("--section-progress", read.toFixed(3));
    });
    links.forEach((link) => link.setAttribute("aria-current", String(link.dataset.section === String(active.number))));
    // Keep the active entry visible in a long outline without moving the page.
    const current = links.find((link) => link.dataset.section === String(active.number));
    if (current && outline && current !== lastActive) {
      lastActive = current;
      const top = current.offsetTop; // the outline is positioned, so this is relative to it
      if (top < outline.scrollTop || top + current.offsetHeight > outline.scrollTop + outline.clientHeight) {
        outline.scrollTop = top - outline.clientHeight / 3;
      }
    }
    if (position) position.textContent = `${active.number} of ${entries.length}`;
  };
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener("resize", update);
  update();
}

/* ---------- Code ---------- */

function setupCodeBlocks(highlighter) {
  document.querySelectorAll("pre code").forEach((code) => {
    const pre = code.closest("pre");
    if (!pre || pre.classList.contains("mermaid")) return;
    if (highlighter) {
      try { highlighter.highlightElement(code); } catch { /* unknown language stays plain */ }
    }
    let block = pre.closest(".code-block");
    if (!block) {
      block = document.createElement("div");
      block.className = "code-block";
      pre.before(block);
      block.append(pre);
    }
    if (block.querySelector(":scope > .copy-code")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = "Copy";
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent || "");
        button.textContent = "Copied";
        button.dataset.state = "done";
      } catch {
        button.textContent = "Copy blocked";
        button.dataset.state = "error";
      }
      setTimeout(() => { button.textContent = "Copy"; delete button.dataset.state; }, 1400);
    });
    block.append(button);
  });
}

/* ---------- Download ---------- */

function stylesheetSource(link) {
  if (!link.sheet) throw new Error(`Could not read ${link.href}`);
  return [...link.sheet.cssRules].map((rule) => rule.cssText).join("\n\n")
    .replace(/@font-face\s*\{[^{}]*\}\s*/g, "");
}

function buildStandaloneDocument() {
  const stylesheets = [...document.querySelectorAll('link[rel~="stylesheet"]')].map(stylesheetSource);
  const copy = document.documentElement.cloneNode(true);
  copy.querySelectorAll(
    'script, link[rel~="stylesheet"], link[rel~="icon"], .doc-rail, .read-progress, .copy-code, .diagram-tools, .diagram-note, .heading-anchor, .toast, dialog',
  ).forEach((element) => element.remove());
  copy.querySelectorAll("pre.mermaid[hidden]").forEach((source) => {
    if (source.parentElement?.querySelector(":scope > .diagram-shell")) source.remove();
    else source.removeAttribute("hidden");
  });
  copy.querySelectorAll(".diagram-canvas svg").forEach((svg) => { svg.style.transform = ""; });
  copy.classList.remove("has-rail", "rail-open");
  const head = copy.querySelector("head");
  if (head && stylesheets.length) {
    const style = document.createElement("style");
    style.textContent = stylesheets.join("\n\n");
    head.append(style);
  }
  return `<!doctype html>\n${copy.outerHTML}\n`;
}

function downloadFilename() {
  const title = document.title.trim() || document.querySelector("h1")?.textContent?.trim() || "document";
  return `${slugify(title)}.html`;
}

function downloadDocument(button) {
  button.disabled = true;
  try {
    const blob = new Blob([buildStandaloneDocument()], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = downloadFilename();
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Downloaded ${link.download}`);
  } catch (error) {
    console.error("Could not build the standalone HTML", error);
    toast("Download failed: the stylesheet could not be read.");
  }
  setTimeout(() => { button.disabled = false; }, 800);
}

function toast(message) {
  document.querySelector(".toast")?.remove();
  const element = document.createElement("div");
  element.className = "toast";
  element.setAttribute("role", "status");
  element.textContent = message;
  document.body.append(element);
  setTimeout(() => element.remove(), 2400);
}

/* ---------- Diagrams ---------- */

/* ---------- Diagram export ---------- */

// Page-level CSS variables don't exist inside a standalone SVG image, so resolve every
// var(--x) against the live element before rasterizing. Variables the SVG defines in its
// own <style> still resolve inside the image.
function resolveCssVariables(markup, element) {
  const styles = getComputedStyle(element);
  const pattern = /var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*?))?\)/g;
  for (let pass = 0; pass < 4; pass += 1) {
    const next = markup.replace(pattern, (match, name, fallback) =>
      styles.getPropertyValue(name).trim() || (fallback ?? match));
    if (next === markup) break;
    markup = next;
  }
  return markup;
}

// An SVG drawn as an image can't fetch webfonts, and a fallback font is wider than the
// one Mermaid measured with, which clips labels. Inline the fonts the SVG uses.
const exportFonts = [
  ["Atkinson Hyperlegible Next", "normal", "200 800", "https://cdn.jsdelivr.net/npm/@fontsource-variable/atkinson-hyperlegible-next@5.2.6/files/atkinson-hyperlegible-next-latin-wght-normal.woff2"],
  ["Bricolage Grotesque", "normal", "200 800", "https://cdn.jsdelivr.net/npm/@fontsource-variable/bricolage-grotesque@5.2.10/files/bricolage-grotesque-latin-wght-normal.woff2"],
  ["Maple Mono", "normal", "400", "https://cdn.jsdelivr.net/fontsource/fonts/maple-mono@5.3.0/latin-400-normal.woff2"],
];
const fontDataCache = new Map();

async function fontDataUrl(url) {
  if (!fontDataCache.has(url)) {
    fontDataCache.set(url, fetch(url).then((response) => {
      if (!response.ok) throw new Error(`font ${response.status}`);
      return response.blob();
    }).then((blob) => new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    })));
  }
  return fontDataCache.get(url);
}

async function embedFonts(markup) {
  const rules = await Promise.all(exportFonts
    .filter(([family]) => markup.includes(family))
    .map(async ([family, style, weight, url]) => {
      try {
        return `@font-face{font-family:"${family}";font-style:${style};font-weight:${weight};src:url(${await fontDataUrl(url)}) format("woff2");}`;
      } catch {
        return "";
      }
    }));
  const css = rules.join("");
  return css ? markup.replace(/<svg\b[^>]*>/, (open) => `${open}<style>${css}</style>`) : markup;
}

function diagramFilename(canvas) {
  const caption = canvas.closest("figure")?.querySelector("figcaption strong")?.textContent?.trim();
  const page = document.querySelector("h1")?.textContent?.trim() || document.title;
  const all = [...document.querySelectorAll(".document .diagram-canvas")];
  const index = all.indexOf(canvas);
  return `${slugify(caption ? `${page} ${caption}` : `${page} diagram ${index >= 0 ? index + 1 : ""}`)}.jpg`;
}

async function downloadDiagramJpg(svg, canvas, button) {
  button.disabled = true;
  try {
    const box = svg.viewBox?.baseVal;
    const rect = svg.getBBox();
    const width = box?.width || rect.width || svg.clientWidth;
    const height = box?.height || rect.height || svg.clientHeight;
    const scale = Math.min(3, 8000 / Math.max(width, height));
    const clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", String(width));
    clone.setAttribute("height", String(height));
    clone.style.transform = "";
    clone.style.maxWidth = "";
    const background = getComputedStyle(document.documentElement).getPropertyValue("--raised").trim() || "#ffffff";
    // Page fonts reach the SVG by inheritance, which a standalone image doesn't have.
    clone.style.fontFamily = getComputedStyle(svg).fontFamily;
    const markup = await embedFonts(resolveCssVariables(new XMLSerializer().serializeToString(clone), svg));
    const image = new Image();
    image.decoding = "async";
    image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;
    await image.decode();
    const output = document.createElement("canvas");
    output.width = Math.round(width * scale);
    output.height = Math.round(height * scale);
    const context = output.getContext("2d");
    context.fillStyle = background;
    context.fillRect(0, 0, output.width, output.height);
    context.drawImage(image, 0, 0, output.width, output.height);
    const blob = await new Promise((resolve, reject) =>
      output.toBlob((value) => (value ? resolve(value) : reject(new Error("canvas export failed"))), "image/jpeg", 0.92));
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = diagramFilename(canvas);
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Downloaded ${link.download}`);
  } catch (error) {
    console.error("Could not export the diagram", error);
    toast("JPG export failed. The diagram source is still in the page.");
  }
  button.disabled = false;
}

function diagramButton(html, title, action) {
  const button = document.createElement("button");
  button.type = "button";
  button.innerHTML = html;
  button.title = title;
  button.setAttribute("aria-label", title);
  button.addEventListener("click", action);
  return button;
}

// mode "inline": the page keeps normal scrolling; Ctrl/Cmd + wheel zooms.
// mode "canvas" (fullscreen): Figma-style. Wheel pans vertically, Shift + wheel pans
// horizontally, trackpad two-finger swipes pan both ways, Ctrl/Cmd + wheel (and
// trackpad pinch, which browsers report as Ctrl + wheel) zooms at the pointer.
function setupViewport(canvas, openFullscreen, mode = "inline") {
  const svg = canvas.querySelector("svg");
  if (!svg || canvas.dataset.viewport) return;
  canvas.dataset.viewport = "ready";
  const state = { x: 0, y: 0, scale: 1, dragging: false, px: 0, py: 0 };
  const apply = () => {
    svg.style.transformOrigin = "0 0";
    svg.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
  };
  const zoom = (factor, clientX, clientY) => {
    const previous = state.scale;
    const next = Math.min(5, Math.max(0.3, previous * factor));
    const bounds = canvas.getBoundingClientRect();
    const ax = clientX === undefined ? bounds.width / 2 : clientX - bounds.left;
    const ay = clientY === undefined ? bounds.height / 2 : clientY - bounds.top;
    state.x = ax - ((ax - state.x) * next) / previous;
    state.y = ay - ((ay - state.y) * next) / previous;
    state.scale = next;
    apply();
  };
  const reset = () => { Object.assign(state, { x: 0, y: 0, scale: 1 }); apply(); };

  canvas.addEventListener("wheel", (event) => {
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? canvas.clientHeight : 1;
    const dx = event.deltaX * unit;
    const dy = event.deltaY * unit;
    if (event.ctrlKey || event.metaKey) {
      event.preventDefault();
      zoom(Math.exp(-Math.max(-60, Math.min(60, dy)) * 0.01), event.clientX, event.clientY);
      return;
    }
    if (mode !== "canvas") return;
    event.preventDefault();
    if (event.shiftKey && !dx) {
      state.x -= dy;
    } else {
      state.x -= dx;
      state.y -= dy;
    }
    apply();
  }, { passive: false });

  if (mode === "canvas") {
    canvas.tabIndex = 0;
    canvas.addEventListener("keydown", (event) => {
      const step = event.shiftKey ? 160 : 48;
      const moves = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
      if (moves[event.key]) { state.x += moves[event.key][0]; state.y += moves[event.key][1]; apply(); event.preventDefault(); }
      if ((event.ctrlKey || event.metaKey) && (event.key === "=" || event.key === "+")) { zoom(1.2); event.preventDefault(); }
      if ((event.ctrlKey || event.metaKey) && event.key === "-") { zoom(1 / 1.2); event.preventDefault(); }
      if ((event.ctrlKey || event.metaKey) && event.key === "0") { reset(); event.preventDefault(); }
    });
  }
  canvas.addEventListener("pointerdown", (event) => {
    state.dragging = true;
    state.px = event.clientX;
    state.py = event.clientY;
    canvas.classList.add("dragging");
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!state.dragging) return;
    state.x += event.clientX - state.px;
    state.y += event.clientY - state.py;
    state.px = event.clientX;
    state.py = event.clientY;
    apply();
  });
  const stop = (event) => {
    state.dragging = false;
    canvas.classList.remove("dragging");
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  };
  canvas.addEventListener("pointerup", stop);
  canvas.addEventListener("pointercancel", stop);
  canvas.addEventListener("dblclick", reset);

  const shell = canvas.closest(".diagram-shell");
  const tools = document.createElement("div");
  tools.className = "diagram-tools";
  tools.setAttribute("role", "toolbar");
  tools.setAttribute("aria-label", "Diagram controls");
  tools.append(
    diagramButton(icons.minus, "Zoom out", () => zoom(0.82)),
    diagramButton(icons.plus, "Zoom in", () => zoom(1.22)),
    diagramButton("1:1", "Reset view", reset),
  );
  if (openFullscreen) tools.append(diagramButton(icons.expand, "Open fullscreen", openFullscreen));
  const jpg = diagramButton(`${icons.image}<span>JPG</span>`, "Download diagram as JPG", () => downloadDiagramJpg(svg, canvas, jpg));
  jpg.classList.add("with-label");
  tools.append(jpg);
  const note = document.createElement("p");
  note.className = "diagram-note";
  note.textContent = mode === "canvas"
    ? "Scroll to pan. Shift + scroll pans sideways. Ctrl + scroll or pinch to zoom. Ctrl + 0 resets."
    : "Drag to pan. Ctrl + scroll to zoom. Double-click resets.";
  shell?.append(tools, note);
  reset();
}

function openDiagramFullscreen(svgMarkup) {
  let dialog = document.querySelector("dialog.diagram-dialog");
  if (!dialog) {
    dialog = document.createElement("dialog");
    dialog.className = "diagram-dialog";
    dialog.setAttribute("aria-label", "Fullscreen diagram");
    const close = document.createElement("button");
    close.type = "button";
    close.className = "dialog-close";
    close.textContent = "Close";
    close.addEventListener("click", () => dialog.close());
    const stage = document.createElement("div");
    stage.className = "dialog-stage";
    dialog.append(close, stage);
    document.body.append(dialog);
  }
  const stage = dialog.querySelector(".dialog-stage");
  stage.innerHTML = `<div class="diagram-shell"><div class="diagram-canvas">${svgMarkup}</div></div>`;
  dialog.showModal();
  setupViewport(stage.querySelector(".diagram-canvas"), null, "canvas");
  stage.querySelector(".diagram-canvas")?.focus({ preventScroll: true });
  }

function setupStaticDiagrams() {
  document.querySelectorAll(".diagram-shell > .diagram-canvas").forEach((canvas) => {
    const svg = canvas.querySelector(":scope > svg");
    if (!svg) return;
    // Some documents ship their own pan/zoom script. Keep it and only add export.
    const ownTools = canvas.closest(".diagram-shell")?.querySelector(":scope > .diagram-tools");
    if (ownTools) {
      if (!ownTools.querySelector(".with-label")) {
        const jpg = diagramButton(`${icons.image}<span>JPG</span>`, "Download diagram as JPG", () => downloadDiagramJpg(svg, canvas, jpg));
        jpg.classList.add("with-label");
        ownTools.append(jpg);
      }
      return;
    }
    setupViewport(canvas, () => openDiagramFullscreen(svg.outerHTML));
  });
}

function diagramThemeVariables() {
  const styles = getComputedStyle(document.documentElement);
  const v = (name) => styles.getPropertyValue(name).trim();
  return {
    primaryColor: v("--pink-soft"),
    primaryTextColor: v("--ink"),
    primaryBorderColor: v("--pink"),
    lineColor: v("--muted"),
    secondaryColor: v("--surface"),
    tertiaryColor: v("--raised"),
    background: v("--raised"),
    fontFamily: v("--font-body") || "ui-sans-serif, system-ui, sans-serif",
  };
}

async function renderDiagrams() {
  const sources = [...document.querySelectorAll("pre.mermaid")];
  if (!sources.length) return;
  if (!mermaidApi) {
    sources.forEach((source) => {
      if (source.parentElement?.querySelector(":scope > .diagram-error")) return;
      const error = document.createElement("div");
      error.className = "diagram-error";
      error.textContent = "Mermaid did not load, so the diagram source is shown instead.";
      source.before(error);
    });
    return;
  }
  mermaidApi.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "base",
    themeVariables: diagramThemeVariables(),
    flowchart: { htmlLabels: false, curve: "basis" },
  });
  for (const source of sources) {
    source.dataset.diagramSource ||= source.textContent || "";
    source.parentElement?.querySelector(":scope > .diagram-shell")?.remove();
    source.parentElement?.querySelector(":scope > .diagram-error")?.remove();
    source.hidden = true;
    try {
      diagramSerial += 1;
      const result = await mermaidApi.render(`doc-diagram-${diagramSerial}`, source.dataset.diagramSource);
      const shell = document.createElement("div");
      shell.className = "diagram-shell";
      const canvas = document.createElement("div");
      canvas.className = "diagram-canvas";
      canvas.innerHTML = result.svg;
      shell.append(canvas);
      source.after(shell);
      setupViewport(canvas, () => openDiagramFullscreen(result.svg));
    } catch (error) {
      source.hidden = false;
      const message = document.createElement("div");
      message.className = "diagram-error";
      message.textContent = `Diagram error: ${error instanceof Error ? error.message : "invalid Mermaid source"}`;
      source.before(message);
    }
  }
}

/* ---------- Boot ---------- */

async function boot() {
  const entries = topSections();
  setupAnchors(entries);
  setupMetaLine(entries);
  setupToolbar(entries);
  applyTheme(storedTheme(), false);
  media.addEventListener("change", async () => {
    if (document.documentElement.dataset.theme !== "system") return;
    applyTheme("system", false);
    if (mermaidApi) await renderDiagrams();
  });
  setupStaticDiagrams();

  const needsHighlight = document.querySelector("pre code:not(.mermaid code)");
  const needsMermaid = document.querySelector("pre.mermaid");
  const [highlightResult, mermaidResult] = await Promise.allSettled([
    needsHighlight ? import("https://cdn.jsdelivr.net/npm/highlight.js@11.12.0/+esm") : Promise.resolve(null),
    needsMermaid ? import("https://cdn.jsdelivr.net/npm/mermaid@11.16.1/dist/mermaid.esm.min.mjs") : Promise.resolve(null),
  ]);
  const highlighter = highlightResult.status === "fulfilled" ? highlightResult.value?.default : null;
  mermaidApi = mermaidResult.status === "fulfilled" ? mermaidResult.value?.default : null;
  setupCodeBlocks(highlighter);
  await renderDiagrams();
}

boot();
