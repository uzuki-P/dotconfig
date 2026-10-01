#!/usr/bin/env python3
"""Exercise notification publishing against a local server with fake credentials."""
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

BIN = Path(__file__).resolve().parent
FILE_INFO = {"Id": "fixture-id", "Name": "fixture.txt", "Size": "7 B", "ContentType": "text/plain", "HotlinkId": ""}


class Handler(http.server.BaseHTTPRequestHandler):
    records = []
    fail_push = False

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        Handler.records.append((self.path, dict(self.headers), data))
        if self.path == "/api/files/add":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"Result": "OK", "FileInfo": FILE_INFO}).encode())
        else:
            self.send_response(503 if Handler.fail_push else 200)
            self.end_headers()
            self.wfile.write(b"{}")

    def log_message(self, *args):
        pass


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gokapi-notify-")
        self.root = Path(self.temp.name)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        Handler.records.clear()
        Handler.fail_push = False
        self.token = self.root / "token"
        self.token.write_text("fake-publisher-token")
        self.token.chmod(0o600)
        self.response = self.root / "response.json"
        self.response.write_text(json.dumps({"Result": "OK", "FileInfo": FILE_INFO}))
        self.env = {key: value for key, value in os.environ.items() if not key.startswith(("NTFY_", "GOKAPI_"))}
        self.env["NTFY_TOKEN_FILE"] = str(self.token)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def notify(self):
        return subprocess.run([BIN / "notify-upload", self.response, "https://files.example.com/d?id=fixture-id"], env=self.env, capture_output=True, text=True)

    def test_disabled_is_noop(self):
        self.assertEqual(0, self.notify().returncode)
        self.assertEqual([], Handler.records)

    def test_device_endpoint_receives_json_and_auth(self):
        endpoints = self.root / "endpoints"
        endpoints.write_text(f"# phone\n{self.url}/up-device\n")
        endpoints.chmod(0o600)
        self.env["NTFY_ENDPOINTS_FILE"] = str(endpoints)
        self.assertEqual(0, self.notify().returncode)
        path, headers, body = Handler.records[0]
        self.assertEqual("/up-device", path)
        self.assertEqual("Bearer fake-publisher-token", headers["Authorization"])
        self.assertEqual("1", headers["X-UnifiedPush"])
        self.assertEqual("fixture-id", json.loads(body)["Id"])
        self.assertEqual("https://files.example.com/d?id=fixture-id", json.loads(body)["UrlDownload"])

    def test_rejects_world_readable_token(self):
        self.env["NTFY_URL"] = f"{self.url}/topic"
        self.token.chmod(0o644)
        self.assertNotEqual(0, self.notify().returncode)
        self.assertEqual([], Handler.records)

    def test_failed_publish_does_not_fail_upload(self):
        Handler.fail_push = True
        self.env.update(NTFY_URL=f"{self.url}/topic", GOKAPI_API_URL=self.url,
                        GOKAPI_PUBLIC_URL="https://files.example.com", GOKAPI_API_KEY="fake-android-key",
                        GOKAPI_ENV_FILE=str(self.root / "absent.env"))
        file = self.root / "fixture.txt"
        file.write_text("fixture")
        result = subprocess.run([BIN / "share", file], env=self.env, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("upload succeeded, but notification publishing failed", result.stderr)
        self.assertIn("https://files.example.com/d?id=fixture-id", result.stdout)
        self.assertEqual(["/api/files/add", "/topic"], [x[0] for x in Handler.records])


if __name__ == "__main__":
    unittest.main()
