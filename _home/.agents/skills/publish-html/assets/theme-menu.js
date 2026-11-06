// publish-html theme dropdown, shared by the catalog and every document.
// An icon button opens a menu of System, Light, and Dark with the current
// choice checked. Styles live in document.css (.theme-menu).

const svg = (paths) => `<svg viewBox="0 0 24 24" aria-hidden="true">${paths}</svg>`;

export const themeIcons = {
  system: svg('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'),
  light: svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  dark: svg('<path d="M20.4 15.5A9 9 0 0 1 8.5 3.6a9 9 0 1 0 11.9 11.9Z"/>'),
};
const check = svg('<path d="m5 12.5 4.5 4.5L19 7.5"/>');

export const themeOptions = [
  ["system", "System"],
  ["light", "Light"],
  ["dark", "Dark"],
];

let serial = 0;

/**
 * Turn `container` into a theme dropdown.
 * placement: "up" opens above the button, "down" below it.
 * align: "start" or "end" edge of the button the menu lines up with.
 */
export function mountThemeMenu(container, { current = "system", onSelect, placement = "down", align = "end", buttonClass = "" }) {
  const id = `theme-menu-${++serial}`;
  container.classList.add("theme-menu");
  container.dataset.placement = placement;
  container.dataset.align = align;
  container.innerHTML = `
    <button type="button" class="${buttonClass}" aria-haspopup="menu" aria-expanded="false" aria-controls="${id}"></button>
    <div class="theme-menu-list" id="${id}" role="menu" aria-label="Theme" hidden>
      ${themeOptions.map(([value, label]) => `
        <button type="button" role="menuitemradio" aria-checked="false" data-theme-option="${value}" tabindex="-1">
          ${themeIcons[value]}<span>${label}</span><span class="theme-menu-check">${check}</span>
        </button>`).join("")}
    </div>`;
  const trigger = container.querySelector("[aria-haspopup]");
  const list = container.querySelector("[role=menu]");
  const items = [...list.querySelectorAll("[role=menuitemradio]")];
  let theme = current;

  function update(next) {
    theme = next;
    const label = themeOptions.find(([value]) => value === next)?.[1] || "System";
    trigger.innerHTML = themeIcons[next] || themeIcons.system;
    trigger.title = `Theme: ${label}`;
    trigger.setAttribute("aria-label", `Theme: ${label}`);
    items.forEach((item) => item.setAttribute("aria-checked", String(item.dataset.themeOption === next)));
  }

  const isOpen = () => !list.hidden;
  function open(focusItem = true) {
    list.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    if (focusItem) (items.find((item) => item.dataset.themeOption === theme) || items[0]).focus();
  }
  function close(refocus = false) {
    if (!isOpen()) return;
    list.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    if (refocus) trigger.focus();
  }
  function choose(value) {
    close(true);
    if (value !== theme) {
      update(value);
      onSelect?.(value);
    }
  }

  trigger.addEventListener("click", (event) => {
    // A pointer click opens without moving focus into the menu.
    isOpen() ? close() : open(event.detail === 0);
  });
  trigger.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); open(); }
  });
  list.addEventListener("click", (event) => {
    const item = event.target.closest("[role=menuitemradio]");
    if (item) choose(item.dataset.themeOption);
  });
  list.addEventListener("keydown", (event) => {
    const index = items.indexOf(document.activeElement);
    const move = { ArrowDown: 1, ArrowUp: -1 }[event.key];
    if (move) { event.preventDefault(); items[(index + move + items.length) % items.length].focus(); }
    else if (event.key === "Home") { event.preventDefault(); items[0].focus(); }
    else if (event.key === "End") { event.preventDefault(); items.at(-1).focus(); }
    else if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(true); }
    else if (event.key === "Tab") close();
  });
  document.addEventListener("pointerdown", (event) => { if (!container.contains(event.target)) close(); });
  container.addEventListener("focusout", (event) => { if (!container.contains(event.relatedTarget)) close(); });

  update(current);
  return { update, close };
}
