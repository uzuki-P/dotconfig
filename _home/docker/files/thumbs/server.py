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
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageOps

import apk_icon

# Bump when the output of any generator changes; old cache entries and client ETags expire.
GENERATOR_VERSION = 4

SIZES = {"s": 160, "l": 960}
FILE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ROUTE = re.compile(r"^/api/thumbnail/([^/]+)$")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".log"}
VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".3gp"}
PE_EXTENSIONS = {".exe", ".dll", ".msi"}
APK_CONTENT_TYPE = "application/vnd.android.package-archive"
MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_ICON_BYTES = 4 * 1024 * 1024
VIDEO_TIMEOUT = 60
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
    if ext == ".apk" or content_type == APK_CONTENT_TYPE:
        return "apk"
    if ext in VIDEO_EXTENSIONS or content_type.startswith("video/"):
        return "video"
    if ext == ".pdf" or content_type == "application/pdf":
        return "pdf"
    if ext == ".zip" or content_type in ("application/zip", "application/x-zip-compressed"):
        return "zip"
    if ext in PE_EXTENSIONS - {".msi"} or content_type in ("application/x-msdownload", "application/vnd.microsoft.portable-executable"):
        return "exe"
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


def image_thumbnail(data: bytes, size: str, crop: bool = True, top: bool = False) -> bytes:
    """A WebP of the image: cropped square for `s` (when [crop]), fitted for `l`. Never upscaled."""
    side = SIZES[size]
    with Image.open(io.BytesIO(data)) as img:
        if img.format == "JPEG":
            img.draft("RGB", (side * 2, side * 2))
        img.seek(0)
        frame = ImageOps.exif_transpose(img)
        has_alpha = frame.mode in ("RGBA", "LA", "PA") or (frame.mode == "P" and "transparency" in frame.info)
        frame = frame.convert("RGBA" if has_alpha else "RGB")
        if size == "s" and crop:
            frame = ImageOps.fit(frame, (side, side), Image.Resampling.LANCZOS, centering=(0.5, 0.0 if top else 0.5))
        else:
            frame.thumbnail((side, side), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        frame.save(out, "WEBP", quality=80, method=4)
        return out.getvalue()


# Windows executables -----------------------------------------------------------------------

RT_ICON = 3
RT_GROUP_ICON = 14


def _u16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def _u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


def pe_icon(read, file_size: int) -> bytes | None:
    """The largest image of the first icon group in a PE file's resources, as an .ico file.

    [read] (offset, length) -> bytes reads part of the file, so only the headers and the
    resource section are fetched. None when the file has no icon.
    """
    head = read(0, 4096)
    if len(head) < 0x40 or head[:2] != b"MZ":
        return None
    pe = _u32(head, 0x3C)
    if pe + 24 > len(head):
        if pe > 1 << 20:
            return None
        head = read(0, pe + 4096)
    if head[pe:pe + 4] != b"PE\0\0":
        return None
    coff = pe + 4
    sections, opt_size = _u16(head, coff + 2), _u16(head, coff + 16)
    opt = coff + 20
    magic = _u16(head, opt)
    dirs = opt + (96 if magic == 0x10B else 112 if magic == 0x20B else -1)
    if dirs < opt or _u32(head, dirs - 4) < 3:  # NumberOfRvaAndSizes
        return None
    rsrc_rva, rsrc_size = _u32(head, dirs + 16), _u32(head, dirs + 20)
    if not rsrc_rva:
        return None
    table = opt + opt_size
    if table + sections * 40 > len(head):
        head = read(0, table + sections * 40)
    start = length = None
    for i in range(sections):
        sec = table + i * 40
        vsize, va, raw_size, raw_ptr = _u32(head, sec + 8), _u32(head, sec + 12), _u32(head, sec + 16), _u32(head, sec + 20)
        if va <= rsrc_rva < va + max(vsize, raw_size):
            start = raw_ptr + (rsrc_rva - va)
            length = min(raw_size - (rsrc_rva - va), max(rsrc_size, 1))
            break
    if start is None or length <= 0 or start + length > file_size:
        return None

    # Installers often keep their payload in the resource section, so it can be hundreds of
    # megabytes. Only the 64 KB blocks the directory walk and the icon touch are fetched.
    blocks: dict[int, bytes] = {}

    def at(offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > length:
            raise ValueError("resource offset outside the section")
        out = bytearray()
        while size > 0:
            block = offset // 65536
            if block not in blocks:
                if len(blocks) > 128:
                    raise ValueError("resource directory too large")
                blocks[block] = read(start + block * 65536, min(65536, length - block * 65536))
            chunk = blocks[block][offset % 65536:offset % 65536 + size]
            if not chunk:
                raise ValueError("short read")
            out += chunk
            offset += len(chunk)
            size -= len(chunk)
        return bytes(out)

    def entries(offset: int):
        header = at(offset, 16)
        count = _u16(header, 12) + _u16(header, 14)
        table = at(offset + 16, count * 8) if count else b""
        for i in range(min(count, 4096)):
            name, target = _u32(table, i * 8), _u32(table, i * 8 + 4)
            yield (None if name & 0x80000000 else name), bool(target & 0x80000000), target & 0x7FFFFFFF

    def first_leaf(offset: int, depth: int = 0) -> bytes | None:
        # Name and language levels: take the first entry that resolves to data.
        for _, is_dir, target in entries(offset):
            if is_dir and depth < 3:
                found = first_leaf(target, depth + 1)
                if found is not None:
                    return found
            elif not is_dir:
                leaf = at(target, 8)
                rva, size = _u32(leaf, 0), _u32(leaf, 4)
                if 0 < size <= MAX_ICON_BYTES:
                    return at(rva - rsrc_rva, size)
        return None

    def by_type(type_id: int) -> dict:
        for name, is_dir, target in entries(0):
            if name == type_id and is_dir:
                return {n: t for n, d, t in entries(target) if d}
        return {}

    groups, icons = by_type(RT_GROUP_ICON), by_type(RT_ICON)
    if not groups or not icons:
        return None
    group = first_leaf(next(iter(groups.values())))
    if not group or len(group) < 6:
        return None
    best = None
    for i in range(_u16(group, 4)):
        e = 6 + i * 14
        if e + 14 > len(group):
            break
        width = group[e] or 256
        bits = _u16(group, e + 6)
        icon_id = _u16(group, e + 12)
        key = (width, bits)
        if icon_id in icons and (best is None or key > best[0]):
            best = (key, group[e:e + 12], icon_id)
    if best is None:
        return None
    image = first_leaf(icons[best[2]])
    if not image:
        return None
    # An .ico with one entry: ICONDIR, then the ICONDIRENTRY with the image's offset.
    entry = best[1][:8] + struct.pack("<II", len(image), 22)
    return struct.pack("<HHH", 0, 1, 1) + entry + image


def ico_thumbnail(ico: bytes, size: str) -> bytes:
    with Image.open(io.BytesIO(ico)) as img:
        img.load()
        return icon_thumbnail(img, size)


class RangeFile(io.RawIOBase):
    """A read-only, seekable file over partial reads, for zipfile. Reads whole 256 KB blocks
    and keeps up to 64 of them, so the ZIP directory and a few entries cost a few requests."""

    BLOCK = 256 * 1024

    def __init__(self, read, size: int):
        super().__init__()
        self._read, self._size, self._pos = read, size, 0
        self._blocks: dict[int, bytes] = {}
        self.fetched = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self._pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._pos, io.SEEK_END: self._size}[whence]
        self._pos = max(0, base + offset)
        return self._pos

    def _block(self, index: int) -> bytes:
        if index not in self._blocks:
            if len(self._blocks) >= 64:
                self._blocks.pop(next(iter(self._blocks)))
            start = index * self.BLOCK
            data = self._read(start, min(self.BLOCK, self._size - start))
            self.fetched += len(data)
            self._blocks[index] = data
        return self._blocks[index]

    def read(self, size=-1):
        if size is None or size < 0:
            size = self._size - self._pos
        size = max(0, min(size, self._size - self._pos))
        out = bytearray()
        while size > 0:
            block = self._block(self._pos // self.BLOCK)
            chunk = block[self._pos % self.BLOCK:self._pos % self.BLOCK + size]
            if not chunk:
                break
            out += chunk
            self._pos += len(chunk)
            size -= len(chunk)
        return bytes(out)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def icon_thumbnail(img: Image.Image, size: str) -> bytes:
    side = SIZES["s"] if size == "s" else 256
    frame = img.convert("RGBA")
    if frame.size != (side, side):
        frame = frame.resize((side, side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    frame.save(out, "WEBP", quality=85, method=4)
    return out.getvalue()


# Documents ---------------------------------------------------------------------------------


def human_size(n: float) -> str:
    for unit in ("B", "kB", "MB", "GB"):
        if n < 1000 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} GB"


def zip_listing(fileobj) -> str | None:
    """'N files · size' and the first entries, from the ZIP's central directory only."""
    try:
        with zipfile.ZipFile(fileobj) as archive:
            files = [i for i in archive.infolist() if not i.is_dir()]
    except (zipfile.BadZipFile, OSError, ValueError):
        return None
    if not files:
        return "Empty archive"
    total = sum(i.file_size for i in files)
    count = f"{len(files)} file{'s' if len(files) != 1 else ''} · {human_size(total)}"
    names = [i.filename for i in files[: TEXT_LINES - 1]]
    return "\n".join([count, *names])[:TEXT_CHARS]


def pdf_first_page(data: bytes) -> bytes:
    """A PNG of page 1, at most 960 px on its long side."""
    result = subprocess.run(["pdftoppm", "-png", "-f", "1", "-l", "1", "-scale-to", "960", "-singlefile", "-"],
                            input=data, capture_output=True, timeout=VIDEO_TIMEOUT, check=False)
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError(f"pdftoppm exited {result.returncode}")
    return result.stdout


# Video -------------------------------------------------------------------------------------


def video_frame(url: str, key: str) -> bytes | None:
    """A PNG of one frame, 10% in (at most 5 s), read over HTTP with partial requests."""
    headers = f"apikey: {key}\r\n"
    # The key is in ffmpeg's arguments, visible only inside this container; never log the command.
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-headers", headers, "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", url],
        capture_output=True, timeout=VIDEO_TIMEOUT, check=False,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe exited {probe.returncode}")
    info = json.loads(probe.stdout or b"{}")
    if not any(s.get("codec_type") == "video" for s in info.get("streams", [])):
        return None
    duration = float(info.get("format", {}).get("duration") or 0)
    at = min(duration * 0.1, 5.0) if duration > 0 else 0
    grab = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{at:.2f}", "-headers", headers, "-i", url,
         "-frames:v", "1", "-an", "-f", "image2pipe", "-c:v", "png", "-"],
        capture_output=True, timeout=VIDEO_TIMEOUT, check=False,
    )
    if grab.returncode != 0 or not grab.stdout:
        raise RuntimeError(f"ffmpeg exited {grab.returncode}")
    return grab.stdout


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

    def read_file(self, file_id: str, limit: int | None = None, offset: int = 0) -> bytes:
        headers = {"Range": f"bytes={offset}-{offset + limit - 1}"} if limit else None
        return self._request(f"files/download/{urllib.parse.quote(file_id)}", self.config.service_key, headers, limit)

    def download_url(self, file_id: str) -> str:
        return f"{self.config.gokapi_url}/api/files/download/{urllib.parse.quote(file_id)}"

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
        if kind == "video":
            frame = video_frame(self.download_url(file_id), self.config.service_key)
            return Result("image", image_thumbnail(frame, size)) if frame else Result("none")
        if kind == "pdf":
            if int(meta.get("SizeBytes") or 0) > MAX_PDF_BYTES:
                return Result("none")
            # Pages show from the top in the square tile, where the title is.
            return Result("image", image_thumbnail(pdf_first_page(self.read_file(file_id)), size, top=True))
        if kind == "zip":
            listing = zip_listing(RangeFile(lambda offset, length: self.read_file(file_id, length, offset), int(meta.get("SizeBytes") or 0)))
            return Result("text", listing.encode()) if listing else Result("none")
        if kind == "apk":
            source = RangeFile(lambda offset, length: self.read_file(file_id, length, offset), int(meta.get("SizeBytes") or 0))
            icon = apk_icon.apk_icon(source)
            return Result("image", icon_thumbnail(icon, size)) if icon else Result("none")
        if kind == "exe":
            ico = pe_icon(lambda offset, length: self.read_file(file_id, length, offset), int(meta.get("SizeBytes") or 0))
            # Icons keep their whole square, never cropped.
            return Result("image", ico_thumbnail(ico, size)) if ico else Result("none")
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
            current = f"v{GENERATOR_VERSION}-"
            for entry in self.config.cache_dir.iterdir():
                if entry.is_dir() and entry.name not in ids:
                    shutil.rmtree(entry, ignore_errors=True)
                elif entry.is_dir():
                    for old in entry.iterdir():
                        if not old.name.startswith((current, ".")):
                            old.unlink(missing_ok=True)

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
