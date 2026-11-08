"""gokapi-thumbs: previews of Gokapi files for the gokapi-android and desktop apps.

GET /api/thumbnail/{id}?size=s|l with the caller's Gokapi `apikey` header. The caller's
key is checked by asking Gokapi for the file's metadata; file contents are read with the
service's own VIEW+DOWNLOAD key. See ../docs/thumbnails.md.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageOps

# Bump when the output of any generator changes; old cache entries and client ETags expire.
GENERATOR_VERSION = 1

SIZES = {"s": 160, "l": 960}
FILE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ROUTE = re.compile(r"^/api/thumbnail/([^/]+)$")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".log"}
MAX_IMAGE_BYTES = 40 * 1024 * 1024
TEXT_BYTES = 8192
TEXT_LINES = 3
TEXT_CHARS = 240
AUTH_TTL = 60.0
FAILED_RETRY = 3600.0
Image.MAX_IMAGE_PIXELS = 80_000_000


@dataclass(frozen=True)
class Config:
    gokapi_url: str
    service_key: str
    cache_dir: Path
    workers: int = 2
    queue_wait: float = 20.0
    prewarm_every: float = 300.0
    cors_origins: frozenset[str] = frozenset()

    @staticmethod
    def from_env() -> "Config":
        key_file = os.environ.get("THUMBS_KEY_FILE", "/run/secrets/thumbs-api-key")
        return Config(
            gokapi_url=os.environ.get("THUMBS_GOKAPI_URL", "http://127.0.0.1:53842").rstrip("/"),
            service_key=Path(key_file).read_text().strip(),
            cache_dir=Path(os.environ.get("THUMBS_CACHE_DIR", "/cache")),
            workers=int(os.environ.get("THUMBS_WORKERS", "2")),
            prewarm_every=float(os.environ.get("THUMBS_PREWARM_SECONDS", "300")),
            cors_origins=frozenset(o for o in os.environ.get("THUMBS_CORS_ORIGINS", "").split() if o),
        )


class GokapiError(Exception):
    def __init__(self, status: int, body: bytes):
        super().__init__(f"Gokapi answered {status}")
        self.status = status
        self.body = body


# Kinds -------------------------------------------------------------------------------------


def kind_of(meta: dict) -> str | None:
    """The generator for a file, or None when it has no preview."""
    if meta.get("IsEncrypted") or meta.get("RequiresClientSideDecryption") or meta.get("IsPendingDeletion"):
        return None
    if meta.get("IsSavedOnLocalStorage") is False:
        return None
    name = str(meta.get("Name", "")).lower()
    ext = os.path.splitext(name)[1]
    content_type = str(meta.get("ContentType", "")).lower()
    if ext in TEXT_EXTENSIONS or content_type.startswith("text/"):
        return "text"
    if ext in IMAGE_EXTENSIONS or (content_type.startswith("image/") and content_type != "image/svg+xml"):
        return "image"
    return None


# Text --------------------------------------------------------------------------------------

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_QUOTE = re.compile(r"^\s*(>\s?)+")
_LIST = re.compile(r"^\s*([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?")
_RULE = re.compile(r"^\s*([-*_]\s*){3,}$")
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_REF_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
_AUTOLINK = re.compile(r"<(https?://[^>]+)>")
_HTML = re.compile(r"</?[A-Za-z][^>]*>")
_EMPHASIS = re.compile(r"(\*\*|__|\*|_|~~)(?=\S)(.+?)(?<=\S)\1")
_CODE = re.compile(r"`+([^`]*)`+")
_REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s+\S+")
# Underlines and separators such as ==== or ----, in Markdown and plain text alike.
_SEPARATOR = re.compile(r"^[=\-_*#~+.]{3,}$")


def decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        # A multi-byte character cut at the end of the partial read.
        if e.start >= len(data) - 3:
            return data[: e.start].decode("utf-8", errors="replace")
        return data.decode("latin-1")


def text_preview(data: bytes, markdown: bool) -> str:
    """Up to TEXT_LINES non-blank lines and TEXT_CHARS characters, Markdown syntax removed."""
    text = decode_text(data).lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if len(data) >= TEXT_BYTES and len(lines) > 1:
        lines = lines[:-1]  # the last line may be cut off by the partial read
    if markdown and lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), None)
        if end is not None:
            lines = lines[end + 1 :]
    out: list[str] = []
    used = 0
    for raw in lines:
        line = raw.strip()
        if _SEPARATOR.match(line):
            continue
        if markdown:
            if _FENCE.match(line) or _RULE.match(line) or _TABLE_RULE.match(line) or _REF_DEF.match(line):
                continue
            line = _HEADING.sub("", line)
            line = _QUOTE.sub("", line)
            line = _LIST.sub("", line)
            line = _IMAGE.sub(r"\1", line)
            line = _LINK.sub(r"\1", line)
            line = _REF_LINK.sub(r"\1", line)
            line = _AUTOLINK.sub(r"\1", line)
            line = _HTML.sub("", line)
            line = _CODE.sub(r"\1", line)
            for _ in range(2):
                line = _EMPHASIS.sub(r"\2", line)
            if line.startswith("|") or line.endswith("|"):
                line = " · ".join(cell.strip() for cell in line.strip("|").split("|") if cell.strip())
            line = line.strip()
        line = re.sub(r"\s+", " ", line)
        if not line:
            continue
        if used + len(line) > TEXT_CHARS:
            line = line[: max(0, TEXT_CHARS - used)].rstrip() + "…"
        out.append(line)
        used += len(line)
        if len(out) >= TEXT_LINES or used >= TEXT_CHARS:
            break
    return "\n".join(out)


# Images ------------------------------------------------------------------------------------


def image_thumbnail(data: bytes, size: str) -> bytes:
    side = SIZES[size]
    with Image.open(io.BytesIO(data)) as img:
        if img.format == "JPEG":
            img.draft("RGB", (side * 2, side * 2))
        img.seek(0)
        frame = ImageOps.exif_transpose(img)
        has_alpha = frame.mode in ("RGBA", "LA", "PA") or (frame.mode == "P" and "transparency" in frame.info)
        frame = frame.convert("RGBA" if has_alpha else "RGB")
        if size == "s":
            frame = ImageOps.fit(frame, (side, side), Image.Resampling.LANCZOS)
        else:
            frame.thumbnail((side, side), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        frame.save(out, "WEBP", quality=80, method=4)
        return out.getvalue()


# Service -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Result:
    kind: str  # "image", "text", "none", "busy"
    body: bytes = b""


class Thumbnailer:
    def __init__(self, config: Config):
        self.config = config
        self.slots = threading.BoundedSemaphore(config.workers)
        self._auth: dict[tuple[str, str], tuple[float, dict]] = {}
        self._auth_lock = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

    # Gokapi calls

    def _request(self, path: str, key: str, headers: dict | None = None, limit: int | None = None) -> bytes:
        request = urllib.request.Request(
            f"{self.config.gokapi_url}/api/{path}",
            headers={"apikey": key, "accept": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(limit) if limit is not None else response.read()
        except urllib.error.HTTPError as e:
            raise GokapiError(e.code, e.read(4096)) from None

    def metadata(self, file_id: str, caller_key: str) -> dict:
        """The file's metadata as the caller sees it; raises GokapiError when Gokapi refuses."""
        cache_key = (hashlib.sha256(caller_key.encode()).hexdigest(), file_id)
        now = time.monotonic()
        with self._auth_lock:
            hit = self._auth.get(cache_key)
            if hit and hit[0] > now:
                return hit[1]
        meta = json.loads(self._request(f"files/list/{urllib.parse.quote(file_id)}", caller_key))
        with self._auth_lock:
            if len(self._auth) > 2000:
                self._auth = {k: v for k, v in self._auth.items() if v[0] > now}
            self._auth[cache_key] = (now + AUTH_TTL, meta)
        return meta

    def list_files(self) -> list[dict]:
        return json.loads(self._request("files/list", self.config.service_key))

    def read_file(self, file_id: str, limit: int | None = None) -> bytes:
        headers = {"Range": f"bytes=0-{limit - 1}"} if limit else None
        return self._request(f"files/download/{urllib.parse.quote(file_id)}", self.config.service_key, headers, limit)

    # Cache

    def _paths(self, file_id: str, size: str) -> dict[str, Path]:
        base = self.config.cache_dir / file_id / f"v{GENERATOR_VERSION}-{size}"
        return {k: base.with_suffix(f".{k}") for k in ("webp", "txt", "none", "failed")}

    def _cached(self, file_id: str, size: str) -> Result | None:
        paths = self._paths(file_id, size)
        if paths["webp"].exists():
            return Result("image", paths["webp"].read_bytes())
        if paths["txt"].exists():
            return Result("text", paths["txt"].read_bytes())
        if paths["none"].exists():
            return Result("none")
        failed = paths["failed"]
        if failed.exists() and time.time() - failed.stat().st_mtime < FAILED_RETRY:
            return Result("none")
        return None

    def _store(self, path: Path, body: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{threading.get_ident()}")
        tmp.write_bytes(body)
        os.replace(tmp, path)

    def _lock(self, key: str) -> threading.Lock:
        with self._locks_lock:
            return self._locks.setdefault(key, threading.Lock())

    # Generation

    def thumbnail(self, meta: dict, size: str, wait: float | None = None) -> Result:
        file_id = str(meta["Id"])
        cached = self._cached(file_id, size)
        if cached:
            return cached
        kind = kind_of(meta)
        paths = self._paths(file_id, size)
        if kind is None:
            self._store(paths["none"], b"")
            return Result("none")
        lock = self._lock(f"{file_id}/{size}")
        with lock:
            cached = self._cached(file_id, size)
            if cached:
                return cached
            if not self.slots.acquire(timeout=self.config.queue_wait if wait is None else wait):
                return Result("busy")
            try:
                result = self._generate(kind, meta, size)
            except Exception as e:  # noqa: BLE001 - any bad file must not break the service
                print(f"thumbnail {file_id}/{size} ({kind}) failed: {e!r}", file=sys.stderr, flush=True)
                self._store(paths["failed"], b"")
                return Result("none")
            finally:
                self.slots.release()
            if result.kind == "image":
                self._store(paths["webp"], result.body)
            elif result.kind == "text":
                self._store(paths["txt"], result.body)
            else:
                self._store(paths["none"], b"")
            for stale in ("failed",):
                paths[stale].unlink(missing_ok=True)
            return result

    def _generate(self, kind: str, meta: dict, size: str) -> Result:
        file_id = str(meta["Id"])
        if kind == "text":
            name = str(meta.get("Name", "")).lower()
            markdown = name.endswith((".md", ".markdown"))
            preview = text_preview(self.read_file(file_id, TEXT_BYTES), markdown)
            return Result("text", preview.encode()) if preview else Result("none")
        if kind == "image":
            if int(meta.get("SizeBytes") or 0) > MAX_IMAGE_BYTES:
                return Result("none")
            return Result("image", image_thumbnail(self.read_file(file_id), size))
        return Result("none")

    # Housekeeping

    def prewarm(self) -> None:
        """Makes small thumbnails for new files and drops the cache of files no longer listed."""
        files = self.list_files()
        ids = {str(f["Id"]) for f in files}
        for f in files:
            # Don't hold up requests from people: give up a slot quickly when busy.
            self.thumbnail(f, "s", wait=1.0)
        if ids and self.config.cache_dir.exists():
            for entry in self.config.cache_dir.iterdir():
                if entry.is_dir() and entry.name not in ids:
                    shutil.rmtree(entry, ignore_errors=True)

    def prewarm_forever(self) -> None:
        while True:
            try:
                self.prewarm()
            except Exception as e:  # noqa: BLE001
                print(f"prewarm failed: {e!r}", file=sys.stderr, flush=True)
            time.sleep(self.config.prewarm_every)


def make_handler(thumbs: Thumbnailer):
    config = thumbs.config

    class Handler(BaseHTTPRequestHandler):
        server_version = "gokapi-thumbs"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):  # noqa: A002 - BaseHTTPRequestHandler's signature
            # One line per request, without query strings or headers.
            print(f"{self.command} {urllib.parse.urlsplit(self.path).path} {args[1] if len(args) > 1 else ''}", flush=True)

        def _cors(self) -> None:
            origin = self.headers.get("Origin")
            if origin and origin in config.cors_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Expose-Headers", "ETag")

        def _send(self, status: int, body: bytes = b"", content_type: str | None = None, headers: dict | None = None) -> None:
            self.send_response(status)
            if content_type:
                self.send_header("Content-Type", content_type)
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self._cors()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body and self.command != "HEAD":
                self.wfile.write(body)

        def _error(self, status: int, message: str) -> None:
            body = json.dumps({"Result": "error", "ErrorMessage": message}).encode()
            self._send(status, body, "application/json")

        def do_OPTIONS(self):  # noqa: N802
            if self.headers.get("Origin") not in config.cors_origins:
                return self._send(403)
            self._send(204, headers={
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "apikey",
                "Access-Control-Max-Age": "600",
            })

        def do_GET(self):  # noqa: N802
            url = urllib.parse.urlsplit(self.path)
            if url.path == "/healthz":
                return self._send(200, b"ok\n", "text/plain")
            match = ROUTE.match(url.path)
            if not match or not FILE_ID.match(match.group(1)):
                return self._error(404, "not found")
            query = urllib.parse.parse_qs(url.query)
            size = query.get("size", ["s"])[-1]
            if size not in SIZES or set(query) - {"size"}:
                return self._error(400, "size must be s or l")
            key = self.headers.get("apikey", "")
            if not key:
                return self._error(401, "Unauthorized")
            file_id = match.group(1)
            try:
                meta = thumbs.metadata(file_id, key)
            except GokapiError as e:
                return self._send(e.status, e.body, "application/json")
            except (urllib.error.URLError, OSError, ValueError):
                return self._error(502, "Gokapi is unreachable")
            etag = f'"{file_id}-{size}-v{GENERATOR_VERSION}"'
            cache = {"ETag": etag, "Cache-Control": "private, max-age=31536000, immutable"}
            if self.headers.get("If-None-Match") == etag and thumbs._cached(file_id, size):
                return self._send(304, headers=cache)
            result = thumbs.thumbnail(meta, size)
            if result.kind == "image":
                self._send(200, result.body, "image/webp", cache)
            elif result.kind == "text":
                self._send(200, result.body, "text/plain; charset=utf-8", cache)
            elif result.kind == "busy":
                self._send(503, json.dumps({"Result": "error", "ErrorMessage": "busy"}).encode(), "application/json", {"Retry-After": "10"})
            else:
                self._send(204, headers=cache)

        do_HEAD = do_GET

    return Handler


def main() -> None:
    config = Config.from_env()
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    thumbs = Thumbnailer(config)
    if config.prewarm_every > 0:
        threading.Thread(target=thumbs.prewarm_forever, name="prewarm", daemon=True).start()
    host = os.environ.get("THUMBS_HOST", "0.0.0.0")
    port = int(os.environ.get("THUMBS_PORT", "53845"))
    server = ThreadingHTTPServer((host, port), make_handler(thumbs))
    server.daemon_threads = True
    print(f"gokapi-thumbs v{GENERATOR_VERSION} listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
