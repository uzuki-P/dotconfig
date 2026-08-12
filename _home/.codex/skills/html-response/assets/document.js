const media = window.matchMedia("(prefers-color-scheme: dark)");
const themeKey = "html-response-theme";
let mermaidApi = null;
let diagramSerial = 0;

const themeIcons = {
  system: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"></rect><path d="M8 21h8M12 17v4"></path></svg>',
  light: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"></path></svg>',
  dark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.4 15.5A9 9 0 0 1 8.5 3.6 9 9 0 1 0 20.4 15.5Z"></path></svg>',
};

function storedTheme() {
  try {
    const value = localStorage.getItem(themeKey);
    return ["system", "light", "dark"].includes(value) ? value : "system";
  } catch {
    return "system";
  }
}

function resolvedTheme(theme) {
  return theme === "system" ? (media.matches ? "dark" : "light") : theme;
}

function applyTheme(theme, persist = true) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.resolvedTheme = resolvedTheme(theme);
  document.querySelectorAll("[data-theme-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme));
  });
  if (persist) {
    try {
      localStorage.setItem(themeKey, theme);
    } catch {
      // The visual state still works when storage is unavailable.
    }
  }
}

function setupThemePicker() {
  const picker = document.createElement("div");
  picker.className = "theme-picker";
  picker.setAttribute("aria-label", "Color theme");
  for (const theme of ["system", "light", "dark"]) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.themeChoice = theme;
    button.title = `${theme[0].toUpperCase()}${theme.slice(1)} theme`;
    button.setAttribute("aria-label", `Use ${theme} theme`);
    button.innerHTML = themeIcons[theme];
    button.addEventListener("click", async () => {
      applyTheme(theme);
      if (mermaidApi) await renderDiagrams();
    });
    picker.append(button);
  }
  document.body.append(picker);
  applyTheme(storedTheme(), false);
  media.addEventListener("change", async () => {
    if (document.documentElement.dataset.theme !== "system") return;
    applyTheme("system", false);
    if (mermaidApi) await renderDiagrams();
  });
}

function setupCodeBlocks(highlighter) {
  document.querySelectorAll("pre code").forEach((code) => {
    if (code.closest("pre")?.classList.contains("mermaid")) return;
    if (highlighter) {
      try {
        highlighter.highlightElement(code);
      } catch {
        // Preserve readable, unhighlighted code for unknown languages.
      }
    }
    const pre = code.closest("pre");
    if (!pre) return;
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
      } catch {
        button.textContent = "Unavailable";
      }
      window.setTimeout(() => { button.textContent = "Copy"; }, 1400);
    });
    block.append(button);
  });
}

function diagramButton(label, title, action) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.title = title;
  button.setAttribute("aria-label", title);
  button.addEventListener("click", action);
  return button;
}

function setupViewport(canvas, openFullscreen) {
  const svg = canvas.querySelector("svg");
  if (!svg) return;
  const state = { x: 0, y: 0, scale: 1, dragging: false, pointerX: 0, pointerY: 0 };

  const apply = () => {
    svg.style.transformOrigin = "0 0";
    svg.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
  };

  const zoom = (factor, clientX, clientY) => {
    const previous = state.scale;
    const next = Math.min(4, Math.max(0.35, previous * factor));
    const bounds = canvas.getBoundingClientRect();
    const anchorX = clientX === undefined ? bounds.width / 2 : clientX - bounds.left;
    const anchorY = clientY === undefined ? bounds.height / 2 : clientY - bounds.top;
    state.x = anchorX - ((anchorX - state.x) * next) / previous;
    state.y = anchorY - ((anchorY - state.y) * next) / previous;
    state.scale = next;
    apply();
  };

  const reset = () => {
    state.x = 0;
    state.y = 0;
    state.scale = 1;
    apply();
  };

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoom(event.deltaY < 0 ? 1.12 : 0.89, event.clientX, event.clientY);
  }, { passive: false });

  canvas.addEventListener("pointerdown", (event) => {
    state.dragging = true;
    state.pointerX = event.clientX;
    state.pointerY = event.clientY;
    canvas.classList.add("dragging");
    canvas.setPointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (!state.dragging) return;
    state.x += event.clientX - state.pointerX;
    state.y += event.clientY - state.pointerY;
    state.pointerX = event.clientX;
    state.pointerY = event.clientY;
    apply();
  });

  const stopDragging = (event) => {
    state.dragging = false;
    canvas.classList.remove("dragging");
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  };
  canvas.addEventListener("pointerup", stopDragging);
  canvas.addEventListener("pointercancel", stopDragging);

  const shell = canvas.closest(".diagram-shell");
  const tools = document.createElement("div");
  tools.className = "diagram-tools";
  tools.setAttribute("aria-label", "Diagram controls");
  tools.append(
    diagramButton("−", "Zoom out", () => zoom(0.82)),
    diagramButton("+", "Zoom in", () => zoom(1.22)),
    diagramButton("1:1", "Reset to 1:1 zoom", reset),
  );
  if (openFullscreen) {
    tools.append(diagramButton("⛶", "Open fullscreen diagram", openFullscreen));
  }
  shell?.append(tools);
  reset();
}

function fullscreenDialog() {
  let dialog = document.querySelector("#html-response-diagram-dialog");
  if (dialog) return dialog;
  dialog = document.createElement("dialog");
  dialog.id = "html-response-diagram-dialog";
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
  return dialog;
}

function openDiagramFullscreen(svgMarkup) {
  const dialog = fullscreenDialog();
  const stage = dialog.querySelector(".dialog-stage");
  stage.replaceChildren();
  const shell = document.createElement("div");
  shell.className = "diagram-shell";
  const canvas = document.createElement("div");
  canvas.className = "diagram-canvas";
  canvas.innerHTML = svgMarkup;
  shell.append(canvas);
  stage.append(shell);
  dialog.showModal();
  setupViewport(canvas, null);
}

function diagramThemeVariables() {
  const styles = getComputedStyle(document.documentElement);
  return {
    primaryColor: styles.getPropertyValue("--pink-soft").trim(),
    primaryTextColor: styles.getPropertyValue("--ink").trim(),
    primaryBorderColor: styles.getPropertyValue("--pink").trim(),
    lineColor: styles.getPropertyValue("--muted").trim(),
    secondaryColor: styles.getPropertyValue("--surface").trim(),
    tertiaryColor: styles.getPropertyValue("--raised").trim(),
    background: styles.getPropertyValue("--raised").trim(),
    fontFamily: "ui-sans-serif, system-ui, sans-serif",
  };
}

async function renderDiagrams() {
  const sources = [...document.querySelectorAll("pre.mermaid")];
  if (!sources.length) return;
  if (!mermaidApi) {
    sources.forEach((source) => {
      source.hidden = true;
      const error = document.createElement("div");
      error.className = "diagram-error";
      error.textContent = "Mermaid could not be loaded. The diagram source remains in the document.";
      source.after(error);
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
      const result = await mermaidApi.render(`html-response-diagram-${diagramSerial}`, source.dataset.diagramSource);
      const shell = document.createElement("div");
      shell.className = "diagram-shell";
      const canvas = document.createElement("div");
      canvas.className = "diagram-canvas";
      canvas.innerHTML = result.svg;
      shell.append(canvas);
      source.after(shell);
      setupViewport(canvas, () => openDiagramFullscreen(result.svg));
    } catch (error) {
      const message = document.createElement("div");
      message.className = "diagram-error";
      message.textContent = `Diagram error: ${error instanceof Error ? error.message : "invalid Mermaid source"}`;
      source.after(message);
    }
  }
}

async function boot() {
  setupThemePicker();
  const [highlightResult, mermaidResult] = await Promise.allSettled([
    import("https://cdn.jsdelivr.net/npm/highlight.js@11.12.0/+esm"),
    import("https://cdn.jsdelivr.net/npm/mermaid@11.16.1/dist/mermaid.esm.min.mjs"),
  ]);
  const highlighter = highlightResult.status === "fulfilled" ? highlightResult.value.default : null;
  mermaidApi = mermaidResult.status === "fulfilled" ? mermaidResult.value.default : null;
  setupCodeBlocks(highlighter);
  await renderDiagrams();
}

boot();
