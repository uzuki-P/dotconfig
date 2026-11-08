"""Render a publish-html Markdown document into the shared HTML shell.

The Markdown dialect is CommonMark plus tables, strikethrough, task lists, autolinks,
`{key="value"}` block attributes, and `:::` containers that map onto the shared
document components. Raw HTML passes through, so a document can drop to custom
markup (inline SVG, a <style> block, a small script) wherever Markdown runs out.
See references/markdown.md for the authoring guide.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))

from markdown_it import MarkdownIt  # noqa: E402
from markdown_it.token import Token  # noqa: E402
from mdit_py_plugins.attrs import attrs_block_plugin  # noqa: E402
from mdit_py_plugins.container import container_plugin  # noqa: E402
from mdit_py_plugins.deflist import deflist_plugin  # noqa: E402
from mdit_py_plugins.gfm_autolink import gfm_autolink_plugin  # noqa: E402
from mdit_py_plugins.tasklists import tasklists_plugin  # noqa: E402


CONTAINERS = (
    "callout", "note", "verdict", "panel", "metrics", "timeline",
    "grid", "columns", "prose", "details", "sources",
)
DIAGRAM_HINT = "Pan, zoom, or open fullscreen"
FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
INFO_ATTR = re.compile(r'(\w[\w-]*)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))')


@dataclass
class MarkdownDocument:
    title: str
    kicker: str
    summary: str
    body: str
    warnings: list[str] = field(default_factory=list)


def _parser() -> MarkdownIt:
    md = (
        MarkdownIt("commonmark", {"html": True, "typographer": False})
        .enable(["table", "strikethrough"])
        .use(attrs_block_plugin)
        .use(tasklists_plugin)
        .use(deflist_plugin)
        .use(gfm_autolink_plugin)
    )
    for name in CONTAINERS:
        md.use(container_plugin, name)
    return md


def parse_front_matter(source: str) -> tuple[dict[str, str], str]:
    match = FRONT_MATTER.match(source)
    if not match:
        return {}, source
    meta: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        pair = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*)$", line)
        if pair:
            key, value = pair.group(1).lower(), pair.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            meta[key] = "" if value in ("|", ">", ">-", "|-") else value
        elif key:
            # A folded or indented continuation line joins the previous value.
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    return meta, source[match.end():]


def parse_info(info: str) -> tuple[str, dict[str, str]]:
    """Split a fence or container info string into its leading words and key="value" attributes."""
    attrs = {m.group(1).lower(): next(g for g in m.groups()[1:] if g is not None) for m in INFO_ATTR.finditer(info)}
    words = INFO_ATTR.sub("", info).strip()
    return words, attrs


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


class Renderer:
    def __init__(self) -> None:
        self.md = _parser()
        self.warnings: list[str] = []
        rules = self.md.renderer.rules
        rules["fence"] = self._fence
        rules["table_open"] = lambda *a: '<div class="table-wrap">\n<table>\n'
        rules["table_close"] = lambda *a: "</table>\n</div>\n"
        rules["th_open"] = self._cell
        rules["td_open"] = self._cell
        rules["link_open"] = self._link_open

    # ----- inline and leaf rules -----

    def _cell(self, tokens, idx, options, env) -> str:
        token = tokens[idx]
        style = token.attrs.pop("style", "") if token.attrs else ""
        if "right" in str(style):
            token.attrSet("class", "numeric")
        elif "center" in str(style):
            token.attrSet("style", "text-align:center")
        return self.md.renderer.renderToken(tokens, idx, options, env)

    def _link_open(self, tokens, idx, options, env) -> str:
        token = tokens[idx]
        href = str(token.attrGet("href") or "")
        if href.startswith(("http://", "https://")):
            token.attrSet("target", "_blank")
            token.attrSet("rel", "noreferrer")
        return self.md.renderer.renderToken(tokens, idx, options, env)

    def _fence(self, tokens, idx, options, env) -> str:
        token = tokens[idx]
        words, attrs = parse_info(token.info or "")
        language = (words.split() or [""])[0].lower()
        code = token.content
        title = attrs.get("title", "")
        if language == "mermaid":
            caption = attrs.get("caption", DIAGRAM_HINT)
            if not title:
                self.warnings.append("a mermaid block has no title=\"...\"; the caption names the JPG download")
            return (
                '<figure class="diagram">\n'
                f"<figcaption><strong>{html.escape(title or 'Diagram')}</strong>"
                f"<span>{html.escape(caption)}</span></figcaption>\n"
                f'<pre class="mermaid">{html.escape(code.rstrip())}</pre>\n'
                "</figure>\n"
            )
        language_class = f' class="language-{_attr(language)}"' if language else ""
        block = f"<pre><code{language_class}>{html.escape(code)}</code></pre>\n"
        if not title:
            return block
        label = attrs.get("label", language)
        return (
            '<div>\n<div class="code-caption">'
            f"<h3>{html.escape(title)}</h3>"
            + (f"<p>{html.escape(label)}</p>" if label else "")
            + f"</div>\n{block}</div>\n"
        )

    # ----- containers -----

    def _render(self, tokens: list[Token], env: dict) -> str:
        return self.md.renderer.render(tokens, self.md.options, env)

    def _inline(self, text: str, env: dict) -> str:
        return self.md.renderInline(text, env).strip()

    def collapse_containers(self, tokens: list[Token], env: dict) -> list[Token]:
        """Replace every ::: container (innermost first) with one html_block token."""
        output: list[Token] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token.type.startswith("container_") and token.type.endswith("_open"):
                name = token.type[len("container_"):-len("_open")]
                depth, end = 1, index + 1
                while end < len(tokens) and depth:
                    if tokens[end].type == token.type:
                        depth += 1
                    elif tokens[end].type == f"container_{name}_close":
                        depth -= 1
                    end += 1
                inner = self.collapse_containers(tokens[index + 1:end - 1], env)
                words, attrs = parse_info(token.info or "")
                words = words.split(None, 1)
                argument = words[1] if len(words) > 1 else ""
                block = Token("html_block", "", 0)
                block.content = self.container_html(name, argument, attrs, inner, env)
                block.map = token.map
                output.append(block)
                index = end
                continue
            output.append(token)
            index += 1
        return output

    def container_html(self, name: str, argument: str, attrs: dict[str, str], inner: list[Token], env: dict) -> str:
        body = self._render(inner, env)
        title = attrs.get("title") or argument
        if name == "callout":
            return f'<div class="callout">\n{body}</div>\n'
        if name == "note":
            return f'<div class="note">\n{body}</div>\n'
        if name == "verdict":
            heading = f"<h3>{self._inline(title or 'Recommendation', env)}</h3>\n"
            return f'<div class="verdict">\n{heading}{body}</div>\n'
        if name == "panel":
            heading = f"<h3>{self._inline(title, env)}</h3>\n" if title else ""
            return f'<div class="panel">\n{heading}{body}</div>\n'
        if name == "details":
            # "::: details Summary text open" starts expanded.
            opened = argument.split()[-1:] == ["open"]
            if opened:
                argument = argument[: -len("open")].strip()
            summary = self._inline(attrs.get("title") or argument or "Details", env)
            opened = " open" if opened else ""
            return f"<details{opened}>\n<summary>{summary}</summary>\n<div class=\"details-body\">\n{body}</div>\n</details>\n"
        if name == "grid":
            kind = argument.split()[0] if argument else "two"
            if kind not in ("two", "three", "sidebar"):
                self.warnings.append(f"::: grid {kind} is not a known grid; use two, three, or sidebar")
                kind = "two"
            return f'<div class="grid {kind}">\n{body}</div>\n'
        if name in ("columns", "prose"):
            return f'<div class="{name}">\n{body}</div>\n'
        if name == "sources":
            listing = body.replace("<ul>", '<ul class="sources">', 1)
            if listing == body:
                self.warnings.append("::: sources should contain a bulleted list of links")
            return listing
        if name == "metrics":
            return self._metrics(inner, env)
        if name == "timeline":
            return self._timeline(inner, env)
        return body

    def _list_items(self, inner: list[Token]) -> list[list[Token]]:
        items: list[list[Token]] = []
        depth = 0
        current: list[Token] | None = None
        for token in inner:
            if token.type == "list_item_open":
                depth += 1
                if depth == 1:
                    current = []
                    continue
            elif token.type == "list_item_close":
                depth -= 1
                if depth == 0 and current is not None:
                    items.append(current)
                    current = None
                    continue
            if current is not None:
                current.append(token)
        return items

    def _metrics(self, inner: list[Token], env: dict) -> str:
        cells = []
        for item in self._list_items(inner):
            text = " ".join(t.content for t in item if t.type == "inline").strip()
            label, separator, value = text.partition(":")
            if not separator:
                self.warnings.append(f"metric item has no 'Label: value' form: {text[:40]!r}")
                continue
            value = value.strip()
            accent = value.startswith("**") and value.endswith("**") and len(value) > 4
            figure = self._inline(value[2:-2] if accent else value, env)
            cells.append(
                f'<div class="metric"><span>{self._inline(label.strip(), env)}</span>'
                f'<strong{" class=\"accent\"" if accent else ""}>{figure}</strong></div>'
            )
        if not cells:
            self.warnings.append("::: metrics should contain a list of 'Label: value' items")
        return '<div class="metrics">\n' + "\n".join(cells) + "\n</div>\n"

    def _timeline(self, inner: list[Token], env: dict) -> str:
        steps = []
        for number, item in enumerate(self._list_items(inner), start=1):
            first_inline = next((t for t in item if t.type == "inline"), None)
            heading = ""
            if first_inline is not None:
                match = re.match(r"^\*\*(.+?)\*\*\s*(?:[—–:-]\s*)?(.*)$", first_inline.content, re.DOTALL)
                if match:
                    heading = f"<h3>{self._inline(match.group(1), env)}</h3>"
                    first_inline.content = match.group(2)
                    children: list[Token] = []
                    self.md.inline.parse(first_inline.content, self.md, env, children)
                    first_inline.children = children
            # Tight list paragraphs are hidden; render them as paragraphs inside the step.
            for token in item:
                if token.type in ("paragraph_open", "paragraph_close"):
                    token.hidden = False
            content = self._render(item, env).replace("<p></p>\n", "")
            steps.append(
                f'<div class="timeline-item"><span class="timeline-index">{number}</span>'
                f"<div>{heading}{content}</div></div>"
            )
        if not steps:
            self.warnings.append("::: timeline should contain a numbered list of steps")
        return '<div class="timeline">\n' + "\n".join(steps) + "\n</div>\n"

    # ----- document -----

    def section_head(self, heading: Token, inline: Token, env: dict) -> str:
        attrs = dict(heading.attrs or {})
        eyebrow = str(attrs.pop("eyebrow", ""))
        meta = str(attrs.pop("meta", ""))
        identifier = attrs.pop("id", "")
        id_attr = f' id="{_attr(str(identifier))}"' if identifier else ""
        title = self._render([inline], env).strip()
        title_html = f"<h2{id_attr}>{title}</h2>"
        if eyebrow:
            title_html = f'<div><p class="eyebrow">{self._inline(eyebrow, env)}</p>{title_html}</div>'
        meta_html = f'<p class="section-meta">{self._inline(meta, env)}</p>' if meta else ""
        return f'<div class="section-head">{title_html}{meta_html}</div>\n'

    def render_body(self, source: str) -> tuple[str, str]:
        """Return (title from a leading # heading or "", body HTML)."""
        env: dict = {}
        tokens = self.collapse_containers(self.md.parse(source, env), env)
        title = ""
        # A leading top-level "# Title" becomes the document title.
        start = next((i for i, t in enumerate(tokens) if t.type != "html_block" or t.content.strip()), 0)
        if len(tokens) > start + 2 and tokens[start].type == "heading_open" and tokens[start].tag == "h1":
            title = tokens[start + 1].content.strip()
            tokens = tokens[:start] + tokens[start + 3:]
        if any(t.type == "heading_open" and t.tag == "h1" for t in tokens):
            self.warnings.append("only the first line may be a # heading; use ## for sections")

        chunks: list[tuple[tuple[Token, Token] | None, list[Token]]] = [(None, [])]
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token.type == "heading_open" and token.tag == "h2" and token.level == 0:
                chunks.append(((token, tokens[index + 1]), []))
                index += 3
                continue
            chunks[-1][1].append(token)
            index += 1

        parts = []
        intro_head, intro = chunks[0]
        if intro:
            # The opening paragraph is the lede.
            for token in intro:
                if token.type == "paragraph_open" and token.level == 0:
                    token.attrSet("class", "lede")
                    break
                if token.type != "html_block" or token.content.strip():
                    break
            parts.append(self._render(intro, env))
        for head, chunk in chunks[1:]:
            heading, inline = head  # type: ignore[misc]
            parts.append(
                '<section class="section">\n'
                + self.section_head(heading, inline, env)
                + self._render(chunk, env)
                + "</section>\n"
            )
        if len(chunks) == 1:
            self.warnings.append("no ## sections; the outline rail and section numbers need at least one")
        return title, "".join(parts)


def render_markdown(source: str) -> MarkdownDocument:
    meta, body = parse_front_matter(source)
    renderer = Renderer()
    heading_title, body_html = renderer.render_body(body)
    title = meta.get("title") or heading_title
    if not title:
        raise ValueError("a Markdown document needs a title: front matter `title:` or a first-line `# Title`")
    summary = " ".join(meta.get("summary", "").split())
    if not summary:
        renderer.warnings.append("front matter has no summary:; the catalog and meta description use it")
    if meta.get("lede"):
        body_html = f'<p class="lede">{renderer._inline(meta["lede"], {})}</p>\n' + body_html
    return MarkdownDocument(
        title=title,
        kicker=meta.get("kicker", ""),
        summary=summary,
        body=body_html,
        warnings=list(dict.fromkeys(renderer.warnings)),
    )


def fill_shell(shell: str, document: MarkdownDocument) -> str:
    rendered = shell.replace("{{DOCUMENT_TITLE}}", html.escape(document.title))
    rendered = rendered.replace("{{DOCUMENT_KICKER}}", html.escape(document.kicker or "Notes"))
    rendered = rendered.replace("{{DOCUMENT_SUMMARY}}", html.escape(document.summary, quote=True))
    return rendered.replace("<!-- DOCUMENT_CONTENT -->", document.body.rstrip())
