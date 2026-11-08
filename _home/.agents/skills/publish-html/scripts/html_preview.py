#!/usr/bin/env python3
"""Create, validate, publish, list, archive, remove, and serve private HTML documents.

Documents are written either as Markdown (preferred; rendered by markdown_doc.py into the
shared shell) or as a full HTML file made from the shell with `new --output doc.html`.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
import functools
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import urllib.error
import urllib.request

from markdown_doc import fill_shell, render_markdown


DEFAULT_ROOT = Path.home() / "docker" / "html-preview" / "public"
DEFAULT_BASE_URL = "https://html-preview.ts.uzuki-p.my.id"
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ASSET_NAMES = ("document.css", "document.js", "theme-menu.js", "catalog.css", "catalog.js", "favicon.svg")
ASSET_VERSION = "23"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
DOCUMENT_TIMESTAMP = re.compile(r"^(\d{8}-\d{6})(?:-|$)")
ARCHIVE_SUBDIR = ".archive"
API_REQUIRED_HEADER = ("x-requested-with", "html-preview-catalog")
MAX_API_BODY_BYTES = 4096
SUMMARY_LIMIT = 240
# Thumbnails are screenshots of the first 1280x800 of a page, saved at half size.
MARKDOWN_SUFFIXES = {".md", ".markdown"}
MARKDOWN_SOURCE_NAME = "source.md"
MARKDOWN_TEMPLATE = """---
title: {title}
kicker: {kicker}
summary: {summary}
---

Open with one or two sentences that state the answer. This paragraph becomes the lede.

## First section

Write the section here. See references/markdown.md for tables, Mermaid, callouts,
metrics, timelines, grids, and raw HTML.
"""
THUMB_FILES = {"light": "thumb.png", "dark": "thumb-dark.png"}
THUMB_VIEWPORT = (1280, 800)
THUMB_SCALE = 0.5
THUMB_TIMEOUT_SECONDS = 60
THUMB_WORKERS = 3
BROWSER_CANDIDATES = ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    kicker: str = ""
    summary: str = ""
    thumbs: tuple[tuple[str, int], ...] = ()


VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class DocumentInspector(HTMLParser):
    """Collect what validation, linting, and the catalog need in one pass."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.in_title = False
        self.title_parts: list[str] = []
        self.description: str | None = None
        self.kicker = ""
        self.lede = ""
        self.first_paragraph = ""
        self.h1_count = 0
        self.warnings: list[str] = []
        self._stack: list[tuple[str, set[str]]] = []
        self._capture: str | None = None
        self._capture_depth = 0
        self._buffer: list[str] = []

    def _inside(self, tag: str | None = None, class_name: str | None = None) -> bool:
        return any(
            (tag is None or name == tag) and (class_name is None or class_name in classes)
            for name, classes in self._stack
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.add(tag)
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "title":
            self.in_title = True
        elif tag == "meta" and attributes.get("name") == "description":
            self.description = " ".join((attributes.get("content") or "").split())
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "table" and not self._inside(class_name="table-wrap"):
            self.warnings.append("a <table> is not wrapped in .table-wrap, so it can overflow on phones")
        elif tag == "svg" and not self._inside("svg"):
            labelled = attributes.get("aria-label") or attributes.get("aria-labelledby")
            if not labelled and attributes.get("aria-hidden") != "true":
                self.warnings.append("an <svg> has no aria-label or aria-labelledby")
        elif tag == "img" and attributes.get("alt") is None:
            self.warnings.append(f"an <img> has no alt text: {attributes.get('src') or '(no src)'}")
        if self._capture:
            if tag not in VOID_TAGS:
                self._capture_depth += 1
        elif tag == "p":
            if "kicker" in classes and not self.kicker:
                self._start_capture("kicker")
            elif "lede" in classes and not self.lede:
                self._start_capture("lede")
            elif not self.first_paragraph and not classes & {"kicker", "eyebrow", "section-meta", "note"}:
                self._start_capture("first_paragraph")
        if tag not in VOID_TAGS:
            self._stack.append((tag, classes))

    def _start_capture(self, name: str) -> None:
        self._capture = name
        self._capture_depth = 0
        self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break
        if not self._capture or tag in VOID_TAGS:
            return
        if self._capture_depth:
            self._capture_depth -= 1
            return
        setattr(self, self._capture, " ".join("".join(self._buffer).split()))
        self._capture = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self._capture:
            self._buffer.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())

    @property
    def summary(self) -> str:
        text = self.description or self.lede or self.first_paragraph
        if len(text) <= SUMMARY_LIMIT:
            return text
        return text[:SUMMARY_LIMIT].rsplit(" ", 1)[0].rstrip(",;:") + "…"

    def lint(self) -> list[str]:
        warnings = list(dict.fromkeys(self.warnings))
        if not self.description:
            warnings.insert(0, "no <meta name=\"description\">; pass --summary to `new` so the catalog can describe it")
        if self.h1_count != 1:
            warnings.insert(0, f"expected one <h1>, found {self.h1_count}")
        return warnings


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48].rstrip("-") or "document"


def inspect_document(source: str) -> DocumentInspector:
    parser = DocumentInspector()
    parser.feed(source)
    parser.close()
    return parser


def validate_source(source: str) -> DocumentInspector:
    errors: list[str] = []
    lowered = source.lower()
    if "<!doctype html>" not in lowered:
        errors.append("missing <!doctype html>")
    inspector = inspect_document(source)
    for tag in ("html", "head", "title", "body"):
        if tag not in inspector.tags:
            errors.append(f"missing <{tag}>")
    if not inspector.title:
        errors.append("empty <title>")
    if "<!-- DOCUMENT_CONTENT -->" in source:
        errors.append("unreplaced document-content marker")
    leftover = sorted(set(re.findall(r"\{\{DOCUMENT_[A-Z_]+\}\}", source)))
    if leftover:
        errors.append(f"unreplaced shell placeholder: {', '.join(leftover)}")
    if errors:
        raise ValueError("; ".join(errors))
    return inspector


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(destination: Path, source: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(source)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def sync_assets(root: Path) -> None:
    source_dir = skill_root() / "assets"
    target_dir = root / "assets"
    for name in ASSET_NAMES:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"missing skill asset: {source}")
        atomic_copy(source, target_dir / name)


def render_standalone_document(source: str) -> str:
    stylesheet = (skill_root() / "assets" / "document.css").read_text(encoding="utf-8")
    stylesheet = re.sub(r"@font-face\s*\{[^{}]*\}\s*", "", stylesheet)
    rendered = re.sub(
        r'<link\b[^>]*\brel=["\']stylesheet["\'][^>]*>\s*',
        f"<style>\n{stylesheet}\n</style>\n",
        source,
        count=1,
        flags=re.IGNORECASE,
    )
    rendered = re.sub(
        r'<link\b[^>]*\brel=["\']icon["\'][^>]*>\s*',
        "",
        rendered,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"<script\b[^>]*>.*?</script>\s*",
        "",
        rendered,
        flags=re.IGNORECASE | re.DOTALL,
    )


def version_document_assets(source: str) -> str:
    version = f"?v={ASSET_VERSION}"
    source = re.sub(
        r"/assets/document\.css(?:\?[^\"']*)?",
        f"/assets/document.css{version}",
        source,
    )
    return re.sub(
        r"/assets/document\.js(?:\?[^\"']*)?",
        f"/assets/document.js{version}",
        source,
    )


def refresh_document_assets(root: Path) -> None:
    documents = root / "d"
    if not documents.is_dir():
        return
    for directory in documents.iterdir():
        index = directory / "index.html"
        if not directory.is_dir() or directory.name.startswith(".") or not index.is_file():
            continue
        source = index.read_text(encoding="utf-8")
        refreshed = version_document_assets(source)
        if refreshed != source:
            # An asset bump is not an edit: keep the catalog's "Edited" date.
            stat = index.stat()
            atomic_write_text(index, refreshed)
            os.utime(index, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def write_standalone_document(directory: Path) -> None:
    source = (directory / "index.html").read_text(encoding="utf-8")
    output = directory / "download.html"
    rendered = render_standalone_document(source)
    atomic_write_text(output, rendered)


def find_browser() -> str | None:
    configured = os.environ.get("HTML_PREVIEW_BROWSER")
    if configured:
        return configured
    for name in BROWSER_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    shells = sorted(
        (Path.home() / ".cache" / "ms-playwright").glob(
            "chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell"
        )
    )
    return str(shells[-1]) if shells else None


class QuietFileHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


@contextmanager
def serve_static(root: Path):
    """Serve the document root on an ephemeral loopback port for screenshots."""
    handler = functools.partial(QuietFileHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def capture_thumbnail(browser: str, url: str, output: Path, scheme: str) -> None:
    width, height = THUMB_VIEWPORT
    # Chrome helpers can still be writing the profile as it exits; leftovers are harmless.
    with tempfile.TemporaryDirectory(prefix="html-preview-browser-", ignore_cleanup_errors=True) as profile:
        shot = Path(profile) / "shot.png"
        command = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--hide-scrollbars",
            "--mute-audio",
            f"--user-data-dir={profile}/profile",
            f"--window-size={width},{height}",
            f"--force-device-scale-factor={THUMB_SCALE}",
            "--virtual-time-budget=4000",
            f"--blink-settings=preferredColorScheme={0 if scheme == 'dark' else 1}",
            f"--screenshot={shot}",
            url,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=THUMB_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise OSError(f"browser timed out after {THUMB_TIMEOUT_SECONDS}s") from error
        if not shot.is_file() or shot.stat().st_size == 0:
            detail = (completed.stderr or completed.stdout).strip().splitlines()[-1:] or ["no output"]
            raise OSError(f"browser did not write a screenshot: {detail[0]}")
        shot.chmod(0o644)
        temporary = output.with_name(f".{output.name}.{secrets.token_hex(3)}")
        shutil.copyfile(shot, temporary)
        temporary.chmod(0o644)
        os.replace(temporary, output)


def render_thumbnails(
    root: Path, document_ids: list[str] | None = None, missing_only: bool = False
) -> dict[str, str]:
    """Screenshot documents and return {id: error} for the ones that failed."""
    root = root.expanduser().resolve()
    if document_ids is None:
        document_ids = [record.document_id for record in iter_document_records(root)]
    directories = [document_dir(root, "d", document_id) for document_id in document_ids]
    jobs = [
        (directory, scheme, directory / name)
        for directory in directories
        for scheme, name in THUMB_FILES.items()
        if not (missing_only and (directory / name).is_file())
    ]
    if not jobs:
        return {}
    browser = find_browser()
    if browser is None:
        raise FileNotFoundError(
            "no Chrome or Chromium found for thumbnails; set HTML_PREVIEW_BROWSER"
        )
    errors: dict[str, str] = {}
    with serve_static(root) as base:
        def run(job: tuple[Path, str, Path]) -> None:
            directory, scheme, output = job
            try:
                capture_thumbnail(browser, f"{base}/d/{directory.name}/?thumbnail", output, scheme)
            except OSError as error:
                errors[directory.name] = str(error)

        with ThreadPoolExecutor(max_workers=THUMB_WORKERS) as pool:
            list(pool.map(run, jobs))
    return errors


def report_thumbnail_errors(errors: dict[str, str]) -> None:
    for document_id, error in errors.items():
        print(f"warning: thumbnail failed for {document_id}: {error}", file=sys.stderr)


def created_at_from_id(document_id: str) -> datetime | None:
    match = DOCUMENT_TIMESTAMP.match(document_id)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


@dataclass
class LoadedDocument:
    html: str
    inspector: DocumentInspector
    markdown: str | None = None
    warnings: tuple[str, ...] = ()


def is_markdown(path: Path) -> bool:
    return path.suffix.lower() in MARKDOWN_SUFFIXES


def render_markdown_source(markdown: str) -> tuple[str, list[str]]:
    document = render_markdown(markdown)
    shell = (skill_root() / "assets" / "document-shell.html").read_text(encoding="utf-8")
    return fill_shell(shell, document), document.warnings


def load_document(path: Path) -> LoadedDocument:
    """Read an HTML or Markdown draft and return validated HTML plus every lint warning."""
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds the 10 MiB publication limit")
    source = path.read_text(encoding="utf-8")
    markdown = None
    extra: list[str] = []
    if is_markdown(path):
        markdown = source
        source, extra = render_markdown_source(markdown)
    inspector = validate_source(source)
    warnings = [*inspector.lint(), *extra]
    if markdown is not None:
        # The front matter summary check replaces the HTML meta-description hint.
        warnings = [w for w in warnings if "meta name=" not in w]
    return LoadedDocument(source, inspector, markdown, tuple(dict.fromkeys(warnings)))


def front_matter_value(value: str) -> str:
    value = " ".join(value.split())
    return json.dumps(value, ensure_ascii=False) if re.search(r"[:#\"']|^[-?!&*|>%@`]", value) else value


def command_new(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser()
    if is_markdown(output):
        rendered = MARKDOWN_TEMPLATE.format(
            title=front_matter_value(args.title),
            kicker=front_matter_value(args.kicker or "Notes"),
            summary=front_matter_value(args.summary),
        )
    else:
        template = (skill_root() / "assets" / "document-shell.html").read_text(encoding="utf-8")
        rendered = template.replace("{{DOCUMENT_TITLE}}", html.escape(args.title))
        rendered = rendered.replace("{{DOCUMENT_KICKER}}", html.escape(args.kicker or "HTML response"))
        rendered = rendered.replace("{{DOCUMENT_SUMMARY}}", html.escape(" ".join(args.summary.split()), quote=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output_file:
            output_file.write(rendered)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    print(output)
    return 0


def report_warnings(document: LoadedDocument) -> None:
    for warning in document.warnings:
        print(f"warning: {warning}", file=sys.stderr)


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser()
    document = load_document(path)
    report_warnings(document)
    print(f"valid\t{document.inspector.title}")
    return 0


def command_render(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser()
    if not is_markdown(path):
        raise ValueError("render takes a Markdown file (.md)")
    document = load_document(path)
    report_warnings(document)
    output = Path(args.output).expanduser()
    atomic_write_text(output, document.html)
    print(output)
    return 0


def command_sync(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    sync_assets(root)
    refresh_document_assets(root)
    try:
        report_thumbnail_errors(render_thumbnails(root, missing_only=True))
    except FileNotFoundError as error:
        print(f"warning: {error}", file=sys.stderr)
    write_index(root)
    print(root / "assets")
    return 0


def command_thumbnails(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    errors = render_thumbnails(root, args.document_ids or None, missing_only=args.missing)
    report_thumbnail_errors(errors)
    write_index(root)
    return 1 if errors else 0


def command_publish(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    source_path = Path(args.file).expanduser()
    document = load_document(source_path)
    report_warnings(document)
    inspector = document.inspector
    source = version_document_assets(document.html)
    sync_assets(root)

    documents = root / "d"
    documents.mkdir(parents=True, exist_ok=True)
    if args.update:
        # Keep the URL: the id must already be published (not archived).
        document_id = document_dir(root, "d", args.update).name
    else:
        label = slugify(args.slug or inspector.title)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        document_id = f"{stamp}-{label}-{secrets.token_hex(2)}"
    temporary = Path(tempfile.mkdtemp(prefix=".publishing-", dir=documents))
    destination = documents / document_id
    retired: Path | None = None
    try:
        output = temporary / "index.html"
        output.write_text(source, encoding="utf-8")
        output.chmod(0o644)
        download = temporary / "download.html"
        download.write_text(render_standalone_document(source), encoding="utf-8")
        download.chmod(0o644)
        if document.markdown is not None:
            markdown = temporary / MARKDOWN_SOURCE_NAME
            markdown.write_text(document.markdown, encoding="utf-8")
            markdown.chmod(0o644)
        temporary.chmod(0o755)
        if destination.exists():
            retired = documents / f".retired-{document_id}-{secrets.token_hex(2)}"
            os.replace(destination, retired)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if retired is not None and retired.exists():
            shutil.rmtree(retired)

    if not getattr(args, "skip_thumbnail", False):
        try:
            report_thumbnail_errors(render_thumbnails(root, [document_id]))
        except FileNotFoundError as error:
            print(f"warning: {error}", file=sys.stderr)
    write_index(root)
    base_url = args.base_url.rstrip("/")
    print(f"{base_url}/d/{document_id}/")
    return 0


def document_record(directory: Path) -> DocumentRecord:
    index = directory / "index.html"
    kicker = summary = ""
    try:
        inspector = inspect_document(index.read_text(encoding="utf-8"))
        title, kicker, summary = inspector.title, inspector.kicker, inspector.summary
    except (OSError, UnicodeError):
        title = "unreadable document"
    try:
        updated_at = datetime.fromtimestamp(index.stat().st_mtime, timezone.utc)
    except OSError:
        updated_at = datetime.now(timezone.utc)
    thumbs = []
    for scheme, name in THUMB_FILES.items():
        try:
            thumbs.append((scheme, int((directory / name).stat().st_mtime)))
        except OSError:
            continue
    return DocumentRecord(
        document_id=directory.name,
        title=title or "untitled",
        created_at=created_at_from_id(directory.name) or updated_at,
        updated_at=updated_at,
        kicker=kicker,
        summary=summary,
        thumbs=tuple(thumbs),
    )


def iter_records(root: Path, subdir: str):
    documents = root / subdir
    if not documents.is_dir():
        return
    for directory in sorted(documents.iterdir(), key=lambda item: item.name, reverse=True):
        index = directory / "index.html"
        if not directory.is_dir() or directory.name.startswith(".") or not index.is_file():
            continue
        yield document_record(directory)


def iter_document_records(root: Path):
    yield from iter_records(root, "d")


def iter_documents(root: Path):
    for record in iter_document_records(root):
        yield record.document_id, record.title


def render_index(records: list[DocumentRecord], archived: list[DocumentRecord]) -> str:
    payload = {
        "assetVersion": ASSET_VERSION,
        "documents": [record_payload(record) | {"archived": False} for record in records]
        + [record_payload(record) | {"archived": True} for record in archived],
    }
    # "</" would end the inline <script>; JSON allows the escaped form.
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    template = (skill_root() / "assets" / "index-shell.html").read_text(encoding="utf-8")
    return (
        template.replace("{{CATALOG_DATA}}", data)
        .replace("{{DOCUMENT_COUNT}}", str(len(records)))
        .replace("{{ASSET_VERSION}}", ASSET_VERSION)
    )


def write_index(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    output = root / "index.html"
    records = list(iter_document_records(root))
    archived = list(iter_records(root, ARCHIVE_SUBDIR))
    for record in records:
        write_standalone_document(root / "d" / record.document_id)
    source = render_index(records, archived)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".index.", dir=root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as index_file:
            index_file.write(source)
            index_file.flush()
            os.fsync(index_file.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def command_list(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    base_url = args.base_url.rstrip("/")
    if getattr(args, "archived", False):
        for record in iter_records(root, ARCHIVE_SUBDIR):
            print(f"{record.document_id}\t{record.title}\tarchived")
        return 0
    for document_id, title in iter_documents(root) or ():
        print(f"{document_id}\t{title}\t{base_url}/d/{document_id}/")
    return 0


def document_dir(root: Path, subdir: str, document_id: str) -> Path:
    if not SAFE_ID.fullmatch(document_id):
        raise ValueError("invalid document id")
    base = (root / subdir).resolve()
    destination = (base / document_id).resolve()
    if destination.parent != base or not destination.is_dir():
        raise FileNotFoundError(f"{document_id} is not published")
    return destination


def archive_document(root: Path, document_id: str) -> None:
    root = root.resolve()
    source = document_dir(root, "d", document_id)
    archive = root / ARCHIVE_SUBDIR
    archive.mkdir(parents=True, exist_ok=True)
    os.replace(source, archive / document_id)
    write_index(root)


def unarchive_document(root: Path, document_id: str) -> None:
    root = root.resolve()
    source = document_dir(root, ARCHIVE_SUBDIR, document_id)
    documents = root / "d"
    documents.mkdir(parents=True, exist_ok=True)
    os.replace(source, documents / document_id)
    write_index(root)


def remove_document(root: Path, document_id: str) -> None:
    root = root.resolve()
    for subdir in ("d", ARCHIVE_SUBDIR):
        try:
            destination = document_dir(root, subdir, document_id)
        except FileNotFoundError:
            continue
        shutil.rmtree(destination)
        write_index(root)
        return
    raise FileNotFoundError(f"{document_id} is not published")


def command_archive(args: argparse.Namespace) -> int:
    archive_document(Path(args.root).expanduser(), args.document_id)
    print(args.document_id)
    return 0


def command_unarchive(args: argparse.Namespace) -> int:
    unarchive_document(Path(args.root).expanduser(), args.document_id)
    print(args.document_id)
    return 0


def command_remove(args: argparse.Namespace) -> int:
    remove_document(Path(args.root).expanduser(), args.document_id)
    print(args.document_id)
    return 0


def record_payload(record: DocumentRecord) -> dict:
    return {
        "id": record.document_id,
        "title": record.title,
        "kicker": record.kicker,
        "summary": record.summary,
        "created": record.created_at.isoformat(timespec="seconds"),
        "updated": record.updated_at.isoformat(timespec="seconds"),
        "thumbs": dict(record.thumbs),
    }


def build_api_server(root: Path, host: str, port: int) -> ThreadingHTTPServer:
    root = root.expanduser().resolve()
    guard = threading.Lock()
    thumb_guard = threading.Lock()

    class ApiHandler(BaseHTTPRequestHandler):
        server_version = "html-preview-api/1"

        def log_message(self, format: str, *args) -> None:
            print(f"api\t{self.address_string()}\t{format % args}", file=sys.stderr)

        def send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def read_json_object(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_API_BODY_BYTES:
                raise ValueError("request body is too large")
            body = self.rfile.read(length) if length else b""
            data = json.loads(body.decode("utf-8")) if body else {}
            if not isinstance(data, dict):
                raise ValueError("request body must be a JSON object")
            return data

        def forbidden(self) -> bool:
            header, expected = API_REQUIRED_HEADER
            if self.headers.get(header) != expected:
                self.send_json(403, {"error": "forbidden"})
                return True
            origin = self.headers.get("Origin")
            if origin:
                host_header = self.headers.get("Host") or ""
                if urlsplit(origin).netloc != host_header:
                    self.send_json(403, {"error": "cross-origin requests are blocked"})
                    return True
            return False

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/health":
                self.send_json(200, {"ok": True})
                return
            if path == "/api/documents":
                with guard:
                    self.send_json(
                        200,
                        {
                            "active": [
                                record_payload(record)
                                for record in iter_records(root, "d")
                            ],
                            "archived": [
                                record_payload(record)
                                for record in iter_records(root, ARCHIVE_SUBDIR)
                            ],
                        },
                    )
                return
            self.send_json(404, {"error": "not found"})

        def refresh_thumbnails(self) -> None:
            try:
                body = self.read_json_object()
                document_id = body.get("id")
                if document_id is not None:
                    document_ids = [str(document_id)]
                    document_dir(root, "d", document_ids[0])
                else:
                    document_ids = None
                if not thumb_guard.acquire(blocking=False):
                    self.send_json(409, {"error": "a thumbnail refresh is already running"})
                    return
                try:
                    errors = render_thumbnails(root, document_ids)
                finally:
                    thumb_guard.release()
                with guard:
                    write_index(root)
                    records = {
                        record.document_id: dict(record.thumbs)
                        for record in iter_records(root, "d")
                    }
            except FileNotFoundError as error:
                self.send_json(404, {"error": str(error)})
                return
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except (OSError, UnicodeError) as error:
                self.send_json(500, {"error": str(error)})
                return
            if document_ids is not None:
                records = {key: value for key, value in records.items() if key in document_ids}
            self.send_json(200, {"ok": not errors, "thumbs": records, "errors": errors})

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/thumbnails":
                if not self.forbidden():
                    self.refresh_thumbnails()
                return
            actions = {
                "/api/archive": archive_document,
                "/api/unarchive": unarchive_document,
                "/api/remove": remove_document,
            }
            action = actions.get(path)
            if action is None:
                self.send_json(404, {"error": "not found"})
                return
            if self.forbidden():
                return
            try:
                body = self.read_json_object()
                document_id = str(body.get("id") or "")
                with guard:
                    action(root, document_id)
            except FileNotFoundError as error:
                self.send_json(404, {"error": str(error)})
                return
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except (OSError, UnicodeError) as error:
                self.send_json(500, {"error": str(error)})
                return
            self.send_json(200, {"ok": True, "id": document_id, "action": path.rsplit("/", 1)[-1]})

    return ThreadingHTTPServer((host, port), ApiHandler)


def command_serve(args: argparse.Namespace) -> int:
    server = build_api_server(Path(args.root).expanduser(), args.bind, args.port)
    bound_host, bound_port = server.server_address[:2]
    print(f"{bound_host}:{bound_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def command_self_test(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="html-preview-test-") as temporary_name:
        test_root = Path(temporary_name) / "public"
        draft = Path(temporary_name) / "draft.html"
        new_args = argparse.Namespace(
            title="Self-test document",
            kicker="Validation",
            summary="Checks that publishing works end to end.",
            output=str(draft),
        )
        with redirect_stdout(io.StringIO()):
            command_new(new_args)
        source = draft.read_text(encoding="utf-8").replace(
            "<!-- DOCUMENT_CONTENT -->",
            '<section class="section"><h2>Ready</h2><p>The publishing path works.</p></section>',
        )
        draft.write_text(source, encoding="utf-8")
        inspector = validate_source(source)
        if inspector.summary != "Checks that publishing works end to end.":
            raise AssertionError(f"summary was not read from the meta description: {inspector.summary!r}")
        if inspector.lint():
            raise AssertionError(f"clean draft produced lint warnings: {inspector.lint()}")
        noisy = validate_source(source.replace("<p>The publishing", "<table><tr><td>x</td></tr></table><p>The publishing"))
        if not any("table-wrap" in warning for warning in noisy.lint()):
            raise AssertionError("lint missed an unwrapped table")
        try:
            validate_source(source.replace("Checks that publishing works end to end.", "{{DOCUMENT_SUMMARY}}"))
        except ValueError:
            pass
        else:
            raise AssertionError("validation accepted an unreplaced shell placeholder")
        sync_assets(test_root)
        for name in ASSET_NAMES:
            if not (test_root / "assets" / name).is_file():
                raise AssertionError(f"asset did not synchronize: {name}")
        document_js = (test_root / "assets" / "document.js").read_text(encoding="utf-8")
        for marker in (
            "buildStandaloneDocument",
            "new Blob",
            "event.ctrlKey",
            "event.shiftKey",
            "diagram-note",
            "doc-rail",
            "rail-outline",
            "downloadDiagramJpg",
            "embedFonts",
        ):
            if marker not in document_js:
                raise AssertionError(f"document asset is missing: {marker}")
        publish_args = argparse.Namespace(
            root=str(test_root),
            base_url="https://example.invalid",
            file=str(draft),
            slug="self-test",
            update=None,
            skip_thumbnail=True,
        )
        with redirect_stdout(io.StringIO()):
            command_publish(publish_args)
        published = list(iter_documents(test_root) or ())
        if len(published) != 1 or published[0][1] != "Self-test document":
            raise AssertionError("published document was not listed correctly")
        published_source = (test_root / "d" / published[0][0] / "index.html").read_text(
            encoding="utf-8"
        )
        for marker in (
            f"/assets/document.css?v={ASSET_VERSION}",
            f"/assets/document.js?v={ASSET_VERSION}",
        ):
            if marker not in published_source:
                raise AssertionError(f"published document is missing: {marker}")
        download_source = (test_root / "d" / published[0][0] / "download.html").read_text(
            encoding="utf-8"
        )
        for marker in ("<style>", "<main"):
            if marker not in download_source:
                raise AssertionError(f"standalone document is missing: {marker}")
        if "/assets/document.css" in download_source or "<script" in download_source:
            raise AssertionError("standalone document still references preview assets")
        index_source = (test_root / "index.html").read_text(encoding="utf-8")
        for marker in (
            "Self-test document",
            "Checks that publishing works end to end.",
            'id="catalog-data"',
            f"catalog.js?v={ASSET_VERSION}",
            f'"assetVersion": "{ASSET_VERSION}"',
            'id="search"',
            'id="sort"',
            'data-layout="rows"',
            'data-view="archive"',
            published[0][0],
        ):
            if marker not in index_source:
                raise AssertionError(f"index is missing: {marker}")
        catalog_js = (test_root / "assets" / "catalog.js").read_text(encoding="utf-8")
        for marker in ("/api/archive", "/api/unarchive", "/api/remove", "/api/thumbnails", "html-preview-catalog", "Undo"):
            if marker not in catalog_js:
                raise AssertionError(f"catalog asset is missing: {marker}")

        # --update replaces the document in place and keeps its id.
        updated_draft = Path(temporary_name) / "updated.html"
        updated_draft.write_text(source.replace("The publishing path works.", "Updated in place."), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            command_publish(argparse.Namespace(
                root=str(test_root), base_url="https://example.invalid",
                file=str(updated_draft), slug=None, update=published[0][0],
                skip_thumbnail=True,
            ))
        after_update = list(iter_documents(test_root) or ())
        if [item[0] for item in after_update] != [published[0][0]]:
            raise AssertionError("--update created a new document instead of replacing it")
        if "Updated in place." not in (test_root / "d" / published[0][0] / "index.html").read_text(encoding="utf-8"):
            raise AssertionError("--update did not replace the document")
        if any(path.name.startswith(".") for path in (test_root / "d").iterdir()):
            raise AssertionError("--update left a temporary directory behind")
        if "{{" in index_source or f'"{ARCHIVE_SUBDIR}/' in index_source:
            raise AssertionError("index contains an unreplaced marker")
        archive_args = argparse.Namespace(root=str(test_root), document_id=published[0][0])
        with redirect_stdout(io.StringIO()):
            command_archive(archive_args)
        if list(iter_documents(test_root) or ()):
            raise AssertionError("archived document is still listed")
        index_data = json.loads(
            (test_root / "index.html").read_text(encoding="utf-8")
            .split('id="catalog-data">', 1)[1].split("</script>", 1)[0]
        )
        if [item["archived"] for item in index_data["documents"]] != [True]:
            raise AssertionError("archived document is not marked archived in the index")
        if not (test_root / ARCHIVE_SUBDIR / published[0][0] / "index.html").is_file():
            raise AssertionError("archived document files are missing")
        archived = list(iter_records(test_root, ARCHIVE_SUBDIR))
        if len(archived) != 1:
            raise AssertionError("archived document was not listed with --archived")
        with redirect_stdout(io.StringIO()):
            command_unarchive(
                argparse.Namespace(root=str(test_root), document_id=published[0][0])
            )
        if len(list(iter_documents(test_root) or ())) != 1:
            raise AssertionError("unarchived document is not listed again")
        with redirect_stdout(io.StringIO()):
            command_archive(archive_args)
        with redirect_stdout(io.StringIO()):
            command_remove(argparse.Namespace(root=str(test_root), document_id=published[0][0]))
        if list(iter_documents(test_root) or ()) or list(iter_records(test_root, ARCHIVE_SUBDIR)):
            raise AssertionError("removed archived document is still present")
        if published[0][0] in (test_root / "index.html").read_text(encoding="utf-8"):
            raise AssertionError("removed document is still present in the index")

        with redirect_stdout(io.StringIO()):
            command_publish(publish_args)
        republished = list(iter_documents(test_root) or ())
        if len(republished) != 1:
            raise AssertionError("republished document is missing")
        server = build_api_server(test_root, "127.0.0.1", 0)
        api_thread = threading.Thread(target=server.serve_forever, daemon=True)
        api_thread.start()
        try:
            port = server.server_address[1]
            base = f"http://127.0.0.1:{port}"

            def api_request(path: str, payload: dict | None = None, header: bool = True):
                request = urllib.request.Request(base + path, method="POST" if payload is not None else "GET")
                if payload is not None:
                    request.add_header("Content-Type", "application/json")
                    if header:
                        request.add_header(API_REQUIRED_HEADER[0], API_REQUIRED_HEADER[1])
                    request.data = json.dumps(payload).encode("utf-8")
                try:
                    with urllib.request.urlopen(request) as response:
                        return response.status, json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as error:
                    return error.code, json.loads(error.read().decode("utf-8"))

            status, payload = api_request("/api/documents")
            if status != 200 or len(payload["active"]) != 1 or payload["archived"]:
                raise AssertionError("api document listing is wrong")
            document_id = payload["active"][0]["id"]
            status, _ = api_request("/api/archive", {"id": document_id}, header=False)
            if status != 403:
                raise AssertionError("api accepted a request without the guard header")
            status, _ = api_request("/api/archive", {"id": document_id})
            if status != 200:
                raise AssertionError("api archive failed")
            status, payload = api_request("/api/documents")
            if status != 200 or payload["active"] or len(payload["archived"]) != 1:
                raise AssertionError("api archive did not update the listing")
            status, _ = api_request("/api/unarchive", {"id": document_id})
            if status != 200:
                raise AssertionError("api unarchive failed")
            status, _ = api_request("/api/remove", {"id": document_id})
            if status != 200:
                raise AssertionError("api remove failed")
            status, payload = api_request("/api/documents")
            if status != 200 or payload["active"] or payload["archived"]:
                raise AssertionError("api remove did not update the listing")
            status, _ = api_request("/api/thumbnails", {"id": "../escape"})
            if status != 400:
                raise AssertionError("api thumbnails accepted an unsafe id")
            status, _ = api_request("/api/thumbnails", {"id": "missing-document"}, header=False)
            if status != 403:
                raise AssertionError("api thumbnails accepted a request without the guard header")
            status, _ = api_request("/api/health")
            if status != 200:
                raise AssertionError("api health check failed")
        finally:
            server.shutdown()
            server.server_close()
            api_thread.join(timeout=5)
        markdown_self_test(Path(temporary_name), test_root)
    print("self-test passed")
    return 0


MARKDOWN_SAMPLE = """---
title: Markdown self-test
kicker: Validation
summary: "Checks the Markdown path: sections, tables, Mermaid, and containers."
---

The opening paragraph is the lede.

{eyebrow="Decision" meta="Scope"}
## Gate first

::: verdict Ship the gate
Reverse this if **billing** slips.
:::

::: metrics
- Monthly cost: **$247**
- Agents: 100
:::

| Option | Cost |
|---|---:|
| Cloud | $247 |

## Flow

```mermaid title="Request path"
flowchart TD
  A --> B
```

```ts title="Cost model"
const total = a < b && c;
```

::: timeline
1. **Align** - confirm the boundary.
2. **Ship** - watch it.
:::

:::: grid two
::: panel Left
One.
:::
::: panel Right
Two.
:::
::::

::: details Raw payload
Hidden by default.
:::

<x-custom data-ok="1">raw HTML passes through</x-custom>
"""


def markdown_self_test(workspace: Path, test_root: Path) -> None:
    draft = workspace / "draft.md"
    draft.write_text(MARKDOWN_SAMPLE, encoding="utf-8")
    document = load_document(draft)
    if document.warnings:
        raise AssertionError(f"clean Markdown produced warnings: {list(document.warnings)}")
    rendered = document.html
    for marker in (
        "<title>Markdown self-test</title>",
        'content="Checks the Markdown path: sections, tables, Mermaid, and containers."',
        '<p class="lede">The opening paragraph is the lede.</p>',
        '<p class="eyebrow">Decision</p><h2>Gate first</h2></div><p class="section-meta">Scope</p>',
        '<div class="verdict">\n<h3>Ship the gate</h3>',
        '<strong class="accent">$247</strong>',
        '<div class="table-wrap">',
        '<th class="numeric">Cost</th>',
        '<figcaption><strong>Request path</strong>',
        '<pre class="mermaid">flowchart TD\n  A --&gt; B</pre>',
        '<div class="code-caption"><h3>Cost model</h3>',
        'const total = a &lt; b &amp;&amp; c;',
        '<span class="timeline-index">2</span><div><h3>Ship</h3>',
        '<div class="grid two">',
        "<summary>Raw payload</summary>",
        '<x-custom data-ok="1">raw HTML passes through</x-custom>',
    ):
        if marker not in rendered:
            raise AssertionError(f"rendered Markdown is missing: {marker}")
    if rendered.count('<section class="section">') != 2:
        raise AssertionError("Markdown did not split into two sections")
    if document.inspector.summary != "Checks the Markdown path: sections, tables, Mermaid, and containers.":
        raise AssertionError("Markdown summary did not reach the meta description")
    noisy = workspace / "noisy.md"
    noisy.write_text("# Only a title\n\n```mermaid\nflowchart TD\n```\n", encoding="utf-8")
    warnings = " ".join(load_document(noisy).warnings)
    for expected in ("no ## sections", "no summary", "title="):
        if expected not in warnings:
            raise AssertionError(f"Markdown lint missed: {expected}")
    with redirect_stdout(io.StringIO()):
        command_publish(argparse.Namespace(
            root=str(test_root), base_url="https://example.invalid", file=str(draft),
            slug="markdown", update=None, skip_thumbnail=True,
        ))
    published = [item for item in iter_documents(test_root) if item[1] == "Markdown self-test"]
    if len(published) != 1:
        raise AssertionError("Markdown document was not published")
    directory = test_root / "d" / published[0][0]
    if (directory / MARKDOWN_SOURCE_NAME).read_text(encoding="utf-8") != MARKDOWN_SAMPLE:
        raise AssertionError("Markdown source was not kept next to the page")
    skeleton = workspace / "skeleton.md"
    with redirect_stdout(io.StringIO()):
        command_new(argparse.Namespace(
            title="Skeleton: test", kicker=None, summary="A summary with: colon.", output=str(skeleton),
        ))
    if load_document(skeleton).inspector.title != "Skeleton: test":
        raise AssertionError("new --output .md produced an unreadable skeleton")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=os.environ.get("HTML_PREVIEW_ROOT", str(DEFAULT_ROOT)),
        help="service document root",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("HTML_PREVIEW_BASE_URL", DEFAULT_BASE_URL),
        help="public URL used in command output",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser(
        "new", help="start a Markdown (.md output) or HTML (.html output) draft"
    )
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--kicker")
    new_parser.add_argument(
        "--summary",
        required=True,
        help="one or two sentences for the meta description and the catalog",
    )
    new_parser.add_argument("--output", required=True)
    new_parser.set_defaults(handler=command_new)

    validate_parser = subparsers.add_parser("validate", help="validate a completed HTML or Markdown document")
    validate_parser.add_argument("file")
    validate_parser.set_defaults(handler=command_validate)

    render_parser = subparsers.add_parser("render", help="render a Markdown document to HTML without publishing")
    render_parser.add_argument("file")
    render_parser.add_argument("--output", required=True)
    render_parser.set_defaults(handler=command_render)

    sync_parser = subparsers.add_parser(
        "sync", help="synchronize shared browser assets and the document index"
    )
    sync_parser.set_defaults(handler=command_sync)

    publish_parser = subparsers.add_parser("publish", help="publish a validated HTML or Markdown document")
    publish_parser.add_argument("file")
    publish_parser.add_argument("--slug")
    publish_parser.add_argument(
        "--update",
        metavar="DOCUMENT_ID",
        help="replace an already published document and keep its URL",
    )
    publish_parser.add_argument(
        "--skip-thumbnail", action="store_true", help="do not screenshot the catalog thumbnail"
    )
    publish_parser.set_defaults(handler=command_publish)

    thumbs_parser = subparsers.add_parser(
        "thumbnails", help="screenshot catalog thumbnails for published documents"
    )
    thumbs_parser.add_argument("document_ids", nargs="*", help="documents to refresh (default: all)")
    thumbs_parser.add_argument(
        "--missing", action="store_true", help="only documents without thumbnails"
    )
    thumbs_parser.set_defaults(handler=command_thumbnails)

    list_parser = subparsers.add_parser("list", help="list published documents")
    list_parser.add_argument(
        "--archived", action="store_true", help="list archived documents instead"
    )
    list_parser.set_defaults(handler=command_list)

    archive_parser = subparsers.add_parser(
        "archive", help="hide a published document without deleting it"
    )
    archive_parser.add_argument("document_id")
    archive_parser.set_defaults(handler=command_archive)

    unarchive_parser = subparsers.add_parser(
        "unarchive", help="restore an archived document"
    )
    unarchive_parser.add_argument("document_id")
    unarchive_parser.set_defaults(handler=command_unarchive)

    remove_parser = subparsers.add_parser(
        "remove", help="remove one published or archived document"
    )
    remove_parser.add_argument("document_id")
    remove_parser.set_defaults(handler=command_remove)

    serve_parser = subparsers.add_parser(
        "serve", help="serve the local JSON API used by the catalog page"
    )
    serve_parser.add_argument("--bind", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=4179)
    serve_parser.set_defaults(handler=command_serve)

    test_parser = subparsers.add_parser("self-test", help="exercise the local publishing primitives")
    test_parser.set_defaults(handler=command_self_test)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (FileNotFoundError, OSError, UnicodeError, ValueError) as error:
        print(f"html-preview: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
