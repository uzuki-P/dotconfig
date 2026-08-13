#!/usr/bin/env python3
"""Create, validate, publish, list, and remove private HTML documents."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from dataclasses import dataclass
import html
from html.parser import HTMLParser
import io
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote


DEFAULT_ROOT = Path.home() / "docker" / "html-preview" / "public"
DEFAULT_BASE_URL = "https://html-preview.ts.uzuki-p.my.id"
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ASSET_NAMES = ("document.css", "document.js", "favicon.svg")
ASSET_VERSION = "11"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
DOCUMENT_TIMESTAMP = re.compile(r"^(\d{8}-\d{6})(?:-|$)")


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class DocumentInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.add(tag)
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


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
            atomic_write_text(index, refreshed)


def write_standalone_document(directory: Path) -> None:
    source = (directory / "index.html").read_text(encoding="utf-8")
    output = directory / "download.html"
    rendered = render_standalone_document(source)
    atomic_write_text(output, rendered)


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


def read_html(path: Path) -> tuple[str, DocumentInspector]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds the 10 MiB publication limit")
    source = path.read_text(encoding="utf-8")
    return source, validate_source(source)


def command_new(args: argparse.Namespace) -> int:
    template = (skill_root() / "assets" / "document-shell.html").read_text(encoding="utf-8")
    rendered = template.replace("{{DOCUMENT_TITLE}}", html.escape(args.title))
    rendered = rendered.replace("{{DOCUMENT_KICKER}}", html.escape(args.kicker or "HTML response"))
    output = Path(args.output).expanduser()
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


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser()
    _, inspector = read_html(path)
    print(f"valid\t{inspector.title}")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    sync_assets(root)
    refresh_document_assets(root)
    write_index(root)
    print(root / "assets")
    return 0


def command_publish(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    source_path = Path(args.file).expanduser()
    source, inspector = read_html(source_path)
    source = version_document_assets(source)
    sync_assets(root)

    label = slugify(args.slug or inspector.title)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    document_id = f"{stamp}-{label}-{secrets.token_hex(2)}"
    documents = root / "d"
    documents.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".publishing-", dir=documents))
    destination = documents / document_id
    try:
        output = temporary / "index.html"
        output.write_text(source, encoding="utf-8")
        output.chmod(0o644)
        download = temporary / "download.html"
        download.write_text(render_standalone_document(source), encoding="utf-8")
        download.chmod(0o644)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    write_index(root)
    base_url = args.base_url.rstrip("/")
    print(f"{base_url}/d/{document_id}/")
    return 0


def document_record(directory: Path) -> DocumentRecord:
    index = directory / "index.html"
    try:
        title = inspect_document(index.read_text(encoding="utf-8")).title
    except (OSError, UnicodeError):
        title = "unreadable document"
    try:
        updated_at = datetime.fromtimestamp(index.stat().st_mtime, timezone.utc)
    except OSError:
        updated_at = datetime.now(timezone.utc)
    return DocumentRecord(
        document_id=directory.name,
        title=title or "untitled",
        created_at=created_at_from_id(directory.name) or updated_at,
        updated_at=updated_at,
    )


def iter_document_records(root: Path):
    documents = root / "d"
    if not documents.is_dir():
        return
    for directory in sorted(documents.iterdir(), key=lambda item: item.name, reverse=True):
        index = directory / "index.html"
        if not directory.is_dir() or directory.name.startswith(".") or not index.is_file():
            continue
        yield document_record(directory)


def iter_documents(root: Path):
    for record in iter_document_records(root):
        yield record.document_id, record.title


def format_date(value: datetime) -> str:
    return value.strftime("%b %d, %Y").replace(" 0", " ")


def document_url(document_id: str) -> str:
    return f"d/{quote(document_id, safe='')}/"


def render_document_card(record: DocumentRecord) -> str:
    document_path = document_url(record.document_id)
    href = html.escape(f"{document_path}?v={ASSET_VERSION}", quote=True)
    download_href = html.escape(f"{document_path}download.html", quote=True)
    title = html.escape(record.title, quote=True)
    document_id = html.escape(record.document_id)
    document_id_attribute = html.escape(record.document_id, quote=True)
    search_text = html.escape(
        f"{record.title} {record.document_id}".casefold(), quote=True
    )
    sort_title = html.escape(record.title.casefold(), quote=True)
    created_timestamp = int(record.created_at.timestamp())
    updated_timestamp = int(record.updated_at.timestamp())
    created_iso = html.escape(record.created_at.isoformat(timespec="seconds"), quote=True)
    updated_iso = html.escape(record.updated_at.isoformat(timespec="seconds"), quote=True)
    created_label = html.escape(format_date(record.created_at))
    updated_label = html.escape(format_date(record.updated_at))
    return f"""<article class="document-card" data-search="{search_text}" data-title="{sort_title}" data-created="{created_timestamp}" data-updated="{updated_timestamp}" data-document-id="{document_id_attribute}">
  <div class="document-thumbnail">
    <iframe src="{href}" title="Thumbnail preview of {title}" loading="lazy" scrolling="no" sandbox="allow-same-origin" tabindex="-1"></iframe>
    <a class="thumbnail-link" href="{href}" aria-label="Open {title}"></a>
    <div class="thumbnail-actions" aria-label="Document actions">
      <a class="thumbnail-action thumbnail-preview" href="{href}" aria-label="Open {title}">Open preview ↗</a>
      <a class="thumbnail-action thumbnail-download" href="{download_href}" download title="Download HTML" aria-label="Download HTML: {title}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 3a1 1 0 0 1 2 0v10.59l3.3-3.3a1 1 0 1 1 1.4 1.42l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 1 1 1.4-1.42l3.3 3.3V3Z"></path><path d="M5 19a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H6a1 1 0 0 1-1-1Z"></path></svg></a>
    </div>
  </div>
  <div class="document-card__body">
    <h3><a href="{href}">{title}</a></h3>
    <p class="document-id">{document_id}</p>
    <dl class="document-dates">
      <div><dt>Created</dt><dd><time datetime="{created_iso}">{created_label}</time></dd></div>
      <div><dt>Updated</dt><dd><time datetime="{updated_iso}">{updated_label}</time></dd></div>
    </dl>
  </div>
</article>"""


def render_index(records: list[DocumentRecord]) -> str:
    cards = "\n".join(render_document_card(record) for record in records)
    if not cards:
        cards = """<div class="empty-state">
  <h3>No published HTML yet</h3>
  <p>Publish a document to see its thumbnail and metadata here.</p>
</div>"""
    template = (skill_root() / "assets" / "index-shell.html").read_text(encoding="utf-8")
    return template.replace("{{DOCUMENT_COUNT}}", str(len(records))).replace(
        "{{DOCUMENT_CARDS}}", cards
    )


def write_index(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    output = root / "index.html"
    records = list(iter_document_records(root))
    for record in records:
        write_standalone_document(root / "d" / record.document_id)
    source = render_index(records)
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
    for document_id, title in iter_documents(root) or ():
        print(f"{document_id}\t{title}\t{base_url}/d/{document_id}/")
    return 0


def command_remove(args: argparse.Namespace) -> int:
    if not SAFE_ID.fullmatch(args.document_id):
        raise ValueError("invalid document id")
    root = Path(args.root).expanduser().resolve()
    destination = (root / "d" / args.document_id).resolve()
    expected_parent = (root / "d").resolve()
    if destination.parent != expected_parent or not destination.is_dir():
        raise FileNotFoundError(args.document_id)
    shutil.rmtree(destination)
    write_index(root)
    print(args.document_id)
    return 0


def command_self_test(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="html-preview-test-") as temporary_name:
        test_root = Path(temporary_name) / "public"
        draft = Path(temporary_name) / "draft.html"
        new_args = argparse.Namespace(
            title="Self-test document", kicker="Validation", output=str(draft)
        )
        with redirect_stdout(io.StringIO()):
            command_new(new_args)
        source = draft.read_text(encoding="utf-8").replace(
            "<!-- DOCUMENT_CONTENT -->",
            '<section class="section"><h2>Ready</h2><p>The publishing path works.</p></section>',
        )
        draft.write_text(source, encoding="utf-8")
        validate_source(source)
        sync_assets(test_root)
        for name in ASSET_NAMES:
            if not (test_root / "assets" / name).is_file():
                raise AssertionError(f"asset did not synchronize: {name}")
        document_js = (test_root / "assets" / "document.js").read_text(encoding="utf-8")
        for marker in (
            "download-document",
            "buildStandaloneDocument",
            "new Blob",
            "event.ctrlKey",
            "diagram-note",
            "home-button",
            "theme-menu",
        ):
            if marker not in document_js:
                raise AssertionError(f"document asset is missing: {marker}")
        publish_args = argparse.Namespace(
            root=str(test_root),
            base_url="https://example.invalid",
            file=str(draft),
            slug="self-test",
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
            "document-thumbnail",
            "document-search",
            "document-sort",
            "theme-picker",
            "data-theme-choice",
            "html-response-theme",
            'scrolling="no"',
            "data-search=",
            "data-created=",
            "data-updated=",
            "Created",
            "Updated",
            "Download HTML",
            "thumbnail-actions",
            "thumbnail-download",
            f"d/{published[0][0]}/",
        ):
            if marker not in index_source:
                raise AssertionError(f"index is missing: {marker}")
        remove_args = argparse.Namespace(root=str(test_root), document_id=published[0][0])
        with redirect_stdout(io.StringIO()):
            command_remove(remove_args)
        if list(iter_documents(test_root) or ()):
            raise AssertionError("removed document is still listed")
        if "Self-test document" in (test_root / "index.html").read_text(encoding="utf-8"):
            raise AssertionError("removed document is still present in the index")
    print("self-test passed")
    return 0


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

    new_parser = subparsers.add_parser("new", help="create a document from the shared shell")
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--kicker")
    new_parser.add_argument("--output", required=True)
    new_parser.set_defaults(handler=command_new)

    validate_parser = subparsers.add_parser("validate", help="validate a completed HTML document")
    validate_parser.add_argument("file")
    validate_parser.set_defaults(handler=command_validate)

    sync_parser = subparsers.add_parser(
        "sync", help="synchronize shared browser assets and the document index"
    )
    sync_parser.set_defaults(handler=command_sync)

    publish_parser = subparsers.add_parser("publish", help="publish a validated HTML document")
    publish_parser.add_argument("file")
    publish_parser.add_argument("--slug")
    publish_parser.set_defaults(handler=command_publish)

    list_parser = subparsers.add_parser("list", help="list published documents")
    list_parser.set_defaults(handler=command_list)

    remove_parser = subparsers.add_parser("remove", help="remove one published document")
    remove_parser.add_argument("document_id")
    remove_parser.set_defaults(handler=command_remove)

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
