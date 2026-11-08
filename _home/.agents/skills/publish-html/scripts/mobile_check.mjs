#!/usr/bin/env node
// Load pages in headless Chrome at phone size and fail when the page scrolls sideways.
// Usage: node mobile_check.mjs [--shots DIR] [--shot-height 1600] [--scroll-to SELECTOR] [--width 390] URL...
// Needs Chrome or Chromium (HTML_PREVIEW_BROWSER overrides the search). No npm packages.

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const option = (name, fallback) => {
  const index = args.indexOf(name);
  if (index < 0) return fallback;
  const [, value] = args.splice(index, 2);
  return value;
};
const shots = option("--shots", null);
const width = Number(option("--width", "390"));
const shotHeight = Number(option("--shot-height", "1600"));
const scrollTo = option("--scroll-to", null);
const height = 844;
const urls = args;
if (!urls.length) {
  console.error("usage: mobile_check.mjs [--shots DIR] [--width 390] URL...");
  process.exit(2);
}

function findBrowser() {
  if (process.env.HTML_PREVIEW_BROWSER) return process.env.HTML_PREVIEW_BROWSER;
  for (const dir of (process.env.PATH || "").split(":")) {
    for (const name of ["google-chrome-stable", "google-chrome", "chromium", "chromium-browser"]) {
      if (existsSync(join(dir, name))) return join(dir, name);
    }
  }
  const cache = join(homedir(), ".cache", "ms-playwright");
  if (existsSync(cache)) {
    for (const entry of readdirSync(cache).filter((name) => name.startsWith("chromium-")).sort().reverse()) {
      const candidate = join(cache, entry, "chrome-linux64", "chrome");
      if (existsSync(candidate)) return candidate;
    }
  }
  return null;
}

const browser = findBrowser();
if (!browser) {
  console.error("mobile-check: no Chrome or Chromium found; set HTML_PREVIEW_BROWSER");
  process.exit(2);
}

const profile = mkdtempSync(join(tmpdir(), "html-preview-mobile-"));
const chrome = spawn(browser, [
  "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  "--hide-scrollbars", "--mute-audio", `--user-data-dir=${profile}`,
  "--remote-debugging-port=0", "about:blank",
], { stdio: ["ignore", "ignore", "pipe"] });

const endpoint = await new Promise((resolve, reject) => {
  let buffer = "";
  const timer = setTimeout(() => reject(new Error("Chrome did not start")), 20000);
  chrome.stderr.on("data", (chunk) => {
    buffer += chunk;
    const match = buffer.match(/DevTools listening on (ws:\/\/\S+)/);
    if (match) { clearTimeout(timer); resolve(match[1]); }
  });
  chrome.on("exit", () => reject(new Error("Chrome exited before it was ready")));
});

const socket = new WebSocket(endpoint);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let serial = 0;
const pending = new Map();
const listeners = new Set();
socket.onmessage = (message) => {
  const data = JSON.parse(message.data);
  if (data.id && pending.has(data.id)) {
    const { resolve, reject } = pending.get(data.id);
    pending.delete(data.id);
    if (data.error) reject(new Error(data.error.message)); else resolve(data.result);
  } else if (data.method) {
    for (const listener of listeners) listener(data);
  }
};
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  serial += 1;
  pending.set(serial, { resolve, reject });
  socket.send(JSON.stringify({ id: serial, method, params, ...(sessionId ? { sessionId } : {}) }));
});
const waitFor = (method, sessionId, timeout = 30000) => new Promise((resolve) => {
  const timer = setTimeout(() => { listeners.delete(listener); resolve(null); }, timeout);
  const listener = (data) => {
    if (data.method === method && data.sessionId === sessionId) {
      clearTimeout(timer);
      listeners.delete(listener);
      resolve(data);
    }
  };
  listeners.add(listener);
});

// Runs in the page: list visible elements that stick out past the viewport, outside the
// scrollers that are allowed to scroll sideways (tables, code, diagrams).
const audit = `(() => {
  const root = document.documentElement;
  const limit = root.clientWidth;
  const scrollers = ".table-wrap, .code-block, pre, .diagram-shell, .diagram-canvas, dialog, .doc-rail, .rail-outline, .theme-menu-list";
  const offenders = [];
  // An ancestor that clips its overflow keeps a wide child from scrolling the page.
  const clipped = (element) => {
    for (let node = element.parentElement; node && node !== document.body; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.overflowX !== "visible") return true;
    }
    return false;
  };
  for (const element of document.body.querySelectorAll("*")) {
    if (element.closest(scrollers) || clipped(element)) continue;
    const box = element.getBoundingClientRect();
    if (!box.width || !box.height) continue;
    if (box.right > limit + 1 || box.left < -1) {
      const name = element.tagName.toLowerCase() + (element.className && typeof element.className === "string" ? "." + element.className.trim().split(/\\s+/).join(".") : "");
      offenders.push(name + " [" + Math.round(box.left) + "→" + Math.round(box.right) + "]");
    }
  }
  return { scrollWidth: root.scrollWidth, clientWidth: limit, offenders: offenders.slice(0, 12) };
})()`;

let failed = 0;
try {
  for (const [index, url] of urls.entries()) {
    const { targetId } = await send("Target.createTarget", { url: "about:blank" });
    const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
    await send("Page.enable", {}, sessionId);
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 2, mobile: true }, sessionId);
    await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 }, sessionId);
    const loaded = waitFor("Page.loadEventFired", sessionId);
    await send("Page.navigate", { url }, sessionId);
    await loaded;
    // Let Mermaid, Pele, and fonts finish.
    await new Promise((resolve) => setTimeout(resolve, 2500));
    const { result } = await send("Runtime.evaluate", { expression: audit, returnByValue: true }, sessionId);
    const report = result.value;
    const ok = report.scrollWidth <= report.clientWidth + 1;
    if (!ok) failed += 1;
    console.log(`${ok ? "ok" : "FAIL"}\t${width}px\tscrollWidth=${report.scrollWidth}\t${url}`);
    if (!ok) for (const offender of report.offenders) console.log(`\toverflows: ${offender}`);
    if (shots) {
      const metrics = await send("Page.getLayoutMetrics", {}, sessionId);
      let top = 0;
      if (scrollTo) {
        const found = await send("Runtime.evaluate", { expression: `(() => { const e = document.querySelector(${JSON.stringify(scrollTo)}); return e ? e.getBoundingClientRect().top + scrollY - 80 : 0; })()`, returnByValue: true }, sessionId);
        top = Math.max(0, Math.round(found.result.value || 0));
      }
      const fullHeight = Math.min(shotHeight, Math.ceil(metrics.cssContentSize.height) - top);
      const shot = await send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: true,
        clip: { x: 0, y: top, width, height: fullHeight, scale: 1 },
      }, sessionId);
      const file = join(shots, `mobile-${index + 1}.png`);
      writeFileSync(file, Buffer.from(shot.data, "base64"));
      console.log(`\tscreenshot: ${file}`);
    }
    await send("Target.closeTarget", { targetId });
  }
} finally {
  socket.close();
  const exited = new Promise((resolve) => chrome.once("exit", resolve));
  chrome.kill();
  await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 3000))]);
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch { /* Chrome helpers may linger */ }
}
process.exit(failed ? 1 : 0);
