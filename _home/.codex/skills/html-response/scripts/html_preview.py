#!/usr/bin/env python3
"""Create, validate, publish, list, and remove private HTML documents."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
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


DEFAULT_ROOT = Path.home() / "docker" / "html-preview" / "public"
DEFAULT_BASE_URL = "https://html-preview.ts.uzuki-p.my.id"
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ASSET_NAMES = ("document.css", "document.js", "favicon.svg")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")


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


def sync_assets(root: Path) -> None:
    source_dir = skill_root() / "assets"
    target_dir = root / "assets"
    for name in ASSET_NAMES:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"missing skill asset: {source}")
        atomic_copy(source, target_dir / name)


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
    print(root / "assets")
    return 0


def command_publish(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    source_path = Path(args.file).expanduser()
    source, inspector = read_html(source_path)
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
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    base_url = args.base_url.rstrip("/")
    print(f"{base_url}/d/{document_id}/")
    return 0


def iter_documents(root: Path):
    documents = root / "d"
    if not documents.is_dir():
        return
    for directory in sorted(documents.iterdir(), key=lambda item: item.name, reverse=True):
        index = directory / "index.html"
        if not directory.is_dir() or directory.name.startswith(".") or not index.is_file():
            continue
        try:
            title = inspect_document(index.read_text(encoding="utf-8")).title
        except (OSError, UnicodeError):
            title = "unreadable document"
        yield directory.name, title or "untitled"


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
        remove_args = argparse.Namespace(root=str(test_root), document_id=published[0][0])
        with redirect_stdout(io.StringIO()):
            command_remove(remove_args)
        if list(iter_documents(test_root) or ()):
            raise AssertionError("removed document is still listed")
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

    sync_parser = subparsers.add_parser("sync", help="synchronize shared browser assets")
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
