"""Tests for gokapi-thumbs against a fake Gokapi. Run: python3 -m unittest -v (in thumbs/)."""

import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

import server

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
                    status = 200
                    if rng:
                        end = int(rng.split("-")[1])
                        data, status = data[: end + 1], 206
                    self.send_response(status)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
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


class KindTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(server.kind_of(file_meta("a", "notes.MD")), "text")
        self.assertEqual(server.kind_of(file_meta("a", "crash", "text/plain")), "text")
        self.assertEqual(server.kind_of(file_meta("a", "pic.png", "image/png")), "image")
        self.assertIsNone(server.kind_of(file_meta("a", "logo.svg", "image/svg+xml")))
        self.assertIsNone(server.kind_of(file_meta("a", "app.apk")))
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
        self.assertEqual(headers["ETag"], '"img1-s-v1"')

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

    def test_no_preview_is_204(self):
        self.gokapi.add(file_meta("apk1", "app.apk"), b"PK")
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
        self.thumbs.prewarm()
        self.assertTrue((Path(self.tmp.name) / "md5" / "v1-s.txt").exists())
        self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
