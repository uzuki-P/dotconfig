"""Tests for gokapi-thumbs against a fake Gokapi. Run: python3 -m unittest -v (in thumbs/)."""

import io
import json
import shutil
import struct
import subprocess
import zipfile
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

import apk_icon
import server

TESTDATA = Path(__file__).parent / "testdata"

CALLER = "caller-key"
SERVICE = "service-key"


def png(width=400, height=200, mode="RGB"):
    out = io.BytesIO()
    Image.new(mode, (width, height), (200, 30, 30) if mode == "RGB" else (200, 30, 30, 128)).save(out, "PNG")
    return out.getvalue()


def file_meta(file_id, name, content_type="application/octet-stream", size=100, **extra):
    return {"Id": file_id, "Name": name, "ContentType": content_type, "SizeBytes": size,
            "IsEncrypted": False, "RequiresClientSideDecryption": False, "IsPendingDeletion": False,
            "IsSavedOnLocalStorage": True, **extra}


class FakeGokapi:
    def __init__(self):
        self.files = {}  # id -> (meta, bytes)
        self.downloads = []  # (id, range header)
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _json(self, status, body):
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):  # noqa: N802
                key = self.headers.get("apikey")
                if key not in (CALLER, SERVICE):
                    return self._json(401, {"Result": "error", "ErrorMessage": "Unauthorized", "ErrorCode": 2})
                if self.path == "/api/files/list":
                    return self._json(200, [meta for meta, _ in fake.files.values()])
                if self.path.startswith("/api/files/list/"):
                    entry = fake.files.get(self.path.rsplit("/", 1)[1])
                    return self._json(200, entry[0]) if entry else self._json(404, {"Result": "error"})
                if self.path.startswith("/api/files/download/"):
                    if key != SERVICE:
                        return self._json(401, {"Result": "error"})
                    file_id = self.path.rsplit("/", 1)[1]
                    data = fake.files[file_id][1]
                    rng = self.headers.get("Range")
                    fake.downloads.append((file_id, rng))
                    status, total = 200, len(data)
                    headers = {"Accept-Ranges": "bytes"}
                    if rng:
                        first, _, last = rng.removeprefix("bytes=").partition("-")
                        start = int(first)
                        end = min(int(last), total - 1) if last else total - 1
                        data, status = data[start:end + 1], 206
                        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
                    self.send_response(status)
                    for k, v in headers.items():
                        self.send_header(k, v)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    try:
                        self.wfile.write(data)
                    except (BrokenPipeError, ConnectionResetError):
                        pass  # ffmpeg stops reading once it has its frame
                    return None
                return self._json(404, {})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"

    def add(self, meta, data):
        self.files[meta["Id"]] = (meta, data)


class TextPreviewTest(unittest.TestCase):
    def test_markdown_is_cleaned(self):
        md = b"---\ntitle: x\n---\n\n# Register lockout\n\n> **Status:** draft, see [the spec](http://x).\n\n- `retry` after 5 min\n- more\n"
        self.assertEqual(server.text_preview(md, True), "Register lockout\nStatus: draft, see the spec.\nretry after 5 min")

    def test_code_fences_and_tables(self):
        md = b"```kotlin\nval x = 1\n```\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        self.assertEqual(server.text_preview(md, True), "val x = 1\na · b\n1 · 2")

    def test_plain_text_keeps_symbols(self):
        self.assertEqual(server.text_preview(b"# not a heading\n\n*keep*\n", False), "# not a heading\n*keep*")

    def test_length_cap(self):
        out = server.text_preview(("word " * 200).encode(), False)
        self.assertLessEqual(len(out), server.TEXT_CHARS + 1)
        self.assertTrue(out.endswith("…"))

    def test_cut_multibyte_and_last_line(self):
        data = ("line one\n" + "é" * (server.TEXT_BYTES // 2)).encode()[: server.TEXT_BYTES]
        self.assertEqual(server.text_preview(data, False), "line one")

    def test_separators_skipped(self):
        self.assertEqual(server.text_preview(b"Crash Report\n=========\nVendor: x\n", False), "Crash Report\nVendor: x")

    def test_latin1_fallback(self):
        self.assertEqual(server.text_preview(b"caf\xe9 \xe9t\xe9\n", False), "café été")


def pe_with_icon(icon: bytes, filler: int = 300000) -> bytes:
    """A minimal PE32+ file whose resource section holds one icon group with [icon],
    stored after [filler] bytes so reads cross a 64 KB block."""
    def directory(entries):  # entries: [(id, offset, is_dir)]
        out = struct.pack("<IIHHHH", 0, 0, 0, 0, 0, len(entries))
        for ident, offset, is_dir in entries:
            out += struct.pack("<II", ident, offset | (0x80000000 if is_dir else 0))
        return out
    rva = 0x1000
    group = struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHIH", 64, 64, 0, 0, 1, 32, len(icon), 1)
    icon_at = 160 + filler
    group_at = icon_at + len(icon)
    rsrc = (directory([(3, 32, True), (14, 80, True)])        # 0: types
            + directory([(1, 56, True)])                       # 32: RT_ICON names
            + directory([(0x409, 128, False)])                 # 56: language
            + directory([(1, 104, True)])                      # 80: RT_GROUP_ICON names
            + directory([(0x409, 144, False)])                 # 104: language
            + struct.pack("<IIII", rva + icon_at, len(icon), 0, 0)    # 128
            + struct.pack("<IIII", rva + group_at, len(group), 0, 0)  # 144
            + b"\0" * filler + icon + group)
    dos = b"MZ" + b"\0" * 58 + struct.pack("<I", 0x40)
    coff = b"PE\0\0" + struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 240, 0x22)
    opt = bytearray(240)
    struct.pack_into("<H", opt, 0, 0x20B)
    struct.pack_into("<I", opt, 108, 16)
    struct.pack_into("<II", opt, 112 + 16, rva, len(rsrc))
    section = b".rsrc\0\0\0" + struct.pack("<IIII", len(rsrc), rva, len(rsrc), 0x400) + b"\0" * 16
    headers = dos + coff + bytes(opt) + section
    return headers + b"\0" * (0x400 - len(headers)) + rsrc


class PeIconTest(unittest.TestCase):
    def test_reads_icon_with_partial_reads(self):
        exe = pe_with_icon(png(64, 64, "RGBA"))
        reads = []

        def read(offset, length):
            reads.append(length)
            return exe[offset:offset + length]

        ico = server.pe_icon(read, len(exe))
        self.assertEqual(Image.open(io.BytesIO(ico)).size, (64, 64))
        self.assertLess(sum(reads), len(exe))
        thumb = Image.open(io.BytesIO(server.ico_thumbnail(ico, "s")))
        self.assertEqual((thumb.size, thumb.mode), ((160, 160), "RGBA"))

    def test_not_a_pe(self):
        data = b"MZ" + b"\0" * 100
        self.assertIsNone(server.pe_icon(lambda o, n: data[o:o + n], len(data)))
        self.assertIsNone(server.pe_icon(lambda o, n: b"PK\3\4"[o:o + n], 4))


@unittest.skipUnless(shutil.which("resvg"), "needs resvg")
class ApkIconTest(unittest.TestCase):
    def test_adaptive_icon_with_vector_and_gradient(self):
        # testdata/build.sh: green background (black at night), a white bar, and a
        # yellow-to-orange gradient bar moved down by a group transform.
        img = apk_icon.apk_icon(open(TESTDATA / "adaptive.apk", "rb"))
        self.assertEqual(img.size, (256, 256))
        self.assertEqual(img.getpixel((30, 128))[:3], (46, 125, 50))
        self.assertEqual(img.getpixel((128, 96))[:3], (255, 255, 255))
        left, right = img.getpixel((70, 170)), img.getpixel((186, 170))
        self.assertGreater(left[1], 200)   # yellow end: lots of green
        self.assertLess(right[1], 120)     # orange end
        self.assertEqual(img.getpixel((1, 1))[3], 0)  # masked corner

    def test_densest_bitmap_wins(self):
        img = apk_icon.apk_icon(open(TESTDATA / "bitmap.apk", "rb"))
        self.assertEqual((img.size, img.getpixel((10, 10))[:3]), ((192, 192), (0, 0, 220)))

    def test_not_an_apk(self):
        self.assertIsNone(apk_icon.apk_icon(io.BytesIO(b"not a zip")))

    def test_range_file_reads_only_what_zipfile_needs(self):
        data = (TESTDATA / "adaptive.apk").read_bytes()  # smaller than one block
        reads = []
        f = server.RangeFile(lambda o, n: reads.append(n) or data[o:o + n], len(data))
        self.assertIsNotNone(apk_icon.apk_icon(f))
        self.assertEqual(len(reads), 1)
        f.seek(-4, io.SEEK_END)
        self.assertEqual(f.read(), data[-4:])


class KindTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(server.kind_of(file_meta("a", "notes.MD")), "text")
        self.assertEqual(server.kind_of(file_meta("a", "crash", "text/plain")), "text")
        self.assertEqual(server.kind_of(file_meta("a", "pic.png", "image/png")), "image")
        self.assertIsNone(server.kind_of(file_meta("a", "logo.svg", "image/svg+xml")))
        self.assertEqual(server.kind_of(file_meta("a", "app.apk")), "apk")
        self.assertEqual(server.kind_of(file_meta("a", "clip.MP4")), "video")
        self.assertEqual(server.kind_of(file_meta("a", "setup.exe")), "exe")
        self.assertIsNone(server.kind_of(file_meta("a", "pic.png", IsEncrypted=True)))


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.gokapi = FakeGokapi()
        self.tmp = tempfile.TemporaryDirectory()
        config = server.Config(self.gokapi.url, SERVICE, Path(self.tmp.name), prewarm_every=0,
                               cors_origins=frozenset({"https://admin.example"}))
        self.thumbs = server.Thumbnailer(config)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.make_handler(self.thumbs))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.gokapi.httpd.shutdown()
        self.gokapi.httpd.server_close()
        self.tmp.cleanup()

    def get(self, path, key=CALLER, headers=None):
        request = urllib.request.Request(self.base + path, headers={**({"apikey": key} if key else {}), **(headers or {})})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def test_image_sizes(self):
        self.gokapi.add(file_meta("img1", "pic.png", "image/png"), png())
        status, headers, body = self.get("/api/thumbnail/img1")
        self.assertEqual((status, headers["Content-Type"]), (200, "image/webp"))
        self.assertEqual(Image.open(io.BytesIO(body)).size, (160, 160))
        status, _, body = self.get("/api/thumbnail/img1?size=l")
        self.assertEqual(Image.open(io.BytesIO(body)).size, (400, 200))  # never upscaled
        self.assertEqual(headers["ETag"], f'"img1-s-v{server.GENERATOR_VERSION}"')

    def test_transparency_kept(self):
        self.gokapi.add(file_meta("img2", "a.png", "image/png"), png(mode="RGBA"))
        _, _, body = self.get("/api/thumbnail/img2")
        self.assertEqual(Image.open(io.BytesIO(body)).mode, "RGBA")

    def test_text_uses_partial_read_and_is_cached(self):
        self.gokapi.add(file_meta("md1", "notes.md"), b"# Title\n\nBody text\n" + b"x" * 20000)
        status, headers, body = self.get("/api/thumbnail/md1")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/plain; charset=utf-8"))
        self.assertEqual(body.decode().split("\n")[:2], ["Title", "Body text"])
        self.get("/api/thumbnail/md1")
        self.assertEqual(self.gokapi.downloads, [("md1", f"bytes=0-{server.TEXT_BYTES - 1}")])

    def test_etag_revalidation(self):
        self.gokapi.add(file_meta("md2", "a.txt", "text/plain"), b"hello\n")
        _, headers, _ = self.get("/api/thumbnail/md2")
        status, _, body = self.get("/api/thumbnail/md2", headers={"If-None-Match": headers["ETag"]})
        self.assertEqual((status, body), (304, b""))

    def test_exe_icon(self):
        self.gokapi.add(file_meta("exe1", "setup.exe", size=0), b"")
        exe = pe_with_icon(png(64, 64, "RGBA"))
        self.gokapi.files["exe1"][0]["SizeBytes"] = len(exe)
        self.gokapi.files["exe1"] = (self.gokapi.files["exe1"][0], exe)
        status, headers, body = self.get("/api/thumbnail/exe1")
        self.assertEqual((status, headers["Content-Type"]), (200, "image/webp"))
        self.assertTrue(all(rng for _, rng in self.gokapi.downloads))  # partial reads only

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
    def test_video_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "clip.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=10:duration=2",
                            "-pix_fmt", "yuv420p", str(clip)], check=True)
            self.gokapi.add(file_meta("vid1", "clip.mp4", size=clip.stat().st_size), clip.read_bytes())
        status, _, body = self.get("/api/thumbnail/vid1")
        self.assertEqual(status, 200)
        self.assertEqual(Image.open(io.BytesIO(body)).size, (160, 160))
        _, _, body = self.get("/api/thumbnail/vid1?size=l")
        self.assertEqual(Image.open(io.BytesIO(body)).size, (320, 180))

    def test_audio_only_video_is_204(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("needs ffmpeg")
        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "sound.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1", str(clip)], check=True)
            self.gokapi.add(file_meta("aud1", "sound.mp4"), clip.read_bytes())
        self.assertEqual(self.get("/api/thumbnail/aud1")[0], 204)

    @unittest.skipUnless(shutil.which("resvg"), "needs resvg")
    def test_apk_icon(self):
        apk = (TESTDATA / "adaptive.apk").read_bytes()
        self.gokapi.add(file_meta("apk2", "app.apk", size=len(apk)), apk)
        status, headers, body = self.get("/api/thumbnail/apk2")
        self.assertEqual((status, headers["Content-Type"]), (200, "image/webp"))
        self.assertEqual(Image.open(io.BytesIO(body)).size, (160, 160))
        self.assertTrue(all(rng for _, rng in self.gokapi.downloads))

    def test_zip_listing(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("docs/", "")
            z.writestr("docs/readme.md", "x" * 1500)
            z.writestr("logo.png", "y" * 500)
            z.writestr("more.txt", "z")
        data = buf.getvalue()
        self.gokapi.add(file_meta("zip1", "bundle.zip", size=len(data)), data)
        status, _, body = self.get("/api/thumbnail/zip1")
        self.assertEqual(status, 200)
        self.assertEqual(body.decode(), "3 files · 2.0 kB\ndocs/readme.md\nlogo.png")

    @unittest.skipUnless(shutil.which("pdftoppm"), "needs pdftoppm")
    def test_pdf_first_page(self):
        out = io.BytesIO()
        Image.new("RGB", (300, 600), (255, 255, 255)).save(out, "PDF")
        data = out.getvalue()
        self.gokapi.add(file_meta("pdf1", "doc.pdf", "application/pdf", size=len(data)), data)
        status, headers, body = self.get("/api/thumbnail/pdf1?size=l")
        self.assertEqual((status, headers["Content-Type"]), (200, "image/webp"))
        self.assertEqual(Image.open(io.BytesIO(body)).size, (480, 960))

    def test_no_preview_is_204(self):
        self.gokapi.add(file_meta("apk1", "data.bin"), b"PK")
        status, _, body = self.get("/api/thumbnail/apk1")
        self.assertEqual((status, body), (204, b""))
        self.assertEqual(self.gokapi.downloads, [])

    def test_broken_image_is_204_and_not_retried(self):
        self.gokapi.add(file_meta("bad", "bad.png", "image/png"), b"not a png")
        self.assertEqual(self.get("/api/thumbnail/bad")[0], 204)
        self.assertEqual(self.get("/api/thumbnail/bad")[0], 204)
        self.assertEqual(len(self.gokapi.downloads), 1)

    def test_auth_passes_through(self):
        self.gokapi.add(file_meta("md3", "a.md"), b"x\n")
        self.assertEqual(self.get("/api/thumbnail/md3", key=None)[0], 401)
        status, _, body = self.get("/api/thumbnail/md3", key="wrong")
        self.assertEqual(status, 401)
        self.assertEqual(json.loads(body)["ErrorCode"], 2)
        self.assertEqual(self.get("/api/thumbnail/missing")[0], 404)

    def test_bad_requests(self):
        self.assertEqual(self.get("/api/thumbnail/a?size=xl")[0], 400)
        self.assertEqual(self.get("/api/thumbnail/a?size=s&x=1")[0], 400)
        self.assertEqual(self.get("/api/thumbnail/a.b")[0], 404)
        self.assertEqual(self.get("/api/files/list")[0], 404)

    def test_cors(self):
        self.gokapi.add(file_meta("md4", "a.md"), b"x\n")
        _, headers, _ = self.get("/api/thumbnail/md4", headers={"Origin": "https://admin.example"})
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "https://admin.example")
        _, headers, _ = self.get("/api/thumbnail/md4", headers={"Origin": "https://evil.example"})
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_prewarm_generates_and_cleans(self):
        self.gokapi.add(file_meta("md5", "a.md"), b"hi\n")
        stale = Path(self.tmp.name) / "gone"
        stale.mkdir()
        (Path(self.tmp.name) / "md5").mkdir()
        old = Path(self.tmp.name) / "md5" / "v0-s.webp"
        old.write_bytes(b"old")
        self.thumbs.prewarm()
        self.assertFalse(old.exists())
        self.assertTrue((Path(self.tmp.name) / "md5" / f"v{server.GENERATOR_VERSION}-s.txt").exists())
        self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
