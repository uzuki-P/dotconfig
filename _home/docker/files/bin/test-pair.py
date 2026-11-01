#!/usr/bin/env python3
"""Exercise bin/pair against a local fake of Gokapi and a fake wrangler."""
import base64
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import urlsplit

BIN = Path(__file__).resolve().parent
NAMESPACE = "0123456789abcdef0123456789abcdef"
ADMIN_KEY = "fake-admin-key"

# Stands in for `wrangler kv key put|delete KEY [VALUE] --namespace-id ID --remote`.
# The namespace lives in a JSON file and every call is logged.
FAKE_WRANGLER = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["FAKE_KV_LOG"], "a") as log:
    log.write(json.dumps({"argv": args, "cwd": os.getcwd()}) + "\n")
if os.environ.get("FAKE_KV_FAIL"):
    print("X [ERROR] injected failure")
    sys.exit(1)
assert args[:2] == ["kv", "key"], args
rest = args[3:]
assert "--remote" in rest, args
i = rest.index("--namespace-id")
assert rest[i + 1] == os.environ["FAKE_KV_NAMESPACE"], args
positional = [a for j, a in enumerate(rest) if j not in (i, i + 1) and a != "--remote"]
store = Path(os.environ["FAKE_KV"])
data = json.loads(store.read_text()) if store.exists() else {}
if args[2] == "put":
    data[positional[0]] = positional[1]
elif args[2] == "delete":
    data.pop(positional[0], None)
else:
    sys.exit(2)
store.write_text(json.dumps(data))
print("Success")
'''


class Fake:
    def reset(self):
        self.records = []
        self.keys = {}
        self.fail = set()
        self.counter = 0


FAKE = Fake()


class Handler(http.server.BaseHTTPRequestHandler):
    def handle_any(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        path = urlsplit(self.path).path
        FAKE.records.append((self.command, path, dict(self.headers), body))
        if f"{self.command} {path}" in FAKE.fail:
            return self.reply(500, {"Result": "error", "ErrorMessage": "injected"})
        if not path.startswith("/api/"):
            return self.reply(404, {})
        if self.headers.get("apikey") != ADMIN_KEY:
            return self.reply(401, {"Result": "error"})
        FAKE.counter += 1
        if self.command == "POST" and path == "/api/auth/create":
            public_id = f"public{FAKE.counter}"
            FAKE.keys[public_id] = {"key": f"secretkey{FAKE.counter}", "perms": [],
                                    "name": self.headers.get("friendlyName"),
                                    "basic": self.headers.get("basicPermissions")}
            return self.reply(200, {"Result": "OK", "Id": FAKE.keys[public_id]["key"], "PublicId": public_id})
        target = self.headers.get("targetKey")
        if target not in FAKE.keys:
            return self.reply(404, {})
        if self.command == "PUT" and path == "/api/auth/modify":
            assert self.headers.get("permissionModifier") == "GRANT"
            FAKE.keys[target]["perms"].append(self.headers.get("permission"))
            return self.reply(200, {"Result": "OK"})
        if self.command == "DELETE" and path == "/api/auth/delete":
            del FAKE.keys[target]
            return self.reply(200, {"Result": "OK"})
        self.reply(404, {})

    def reply(self, status, payload):
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    do_GET = do_POST = do_PUT = do_DELETE = handle_any

    def log_message(self, *args):
        pass


def decode_link(link):
    prefix = "https://files.example.ts.net/pair#"
    assert link.startswith(prefix), link
    payload = link[len(prefix):]
    assert "=" not in payload and "+" not in payload and "/" not in payload
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


class PairTests(unittest.TestCase):
    def setUp(self):
        FAKE.reset()
        self.temp = tempfile.TemporaryDirectory(prefix="gokapi-pair-")
        self.root = Path(self.temp.name)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.state = self.root / "secrets" / "pairs.json"
        self.kv = self.root / "kv.json"
        self.kv_log = self.root / "kv.log"
        (self.root / "admin").write_text(ADMIN_KEY + "\n")
        (self.root / "admin").chmod(0o600)
        wrangler = self.root / "fake-wrangler"
        wrangler.write_text(FAKE_WRANGLER)
        wrangler.chmod(0o700)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("GOKAPI_", "RELAY_", "PAIR_", "WRANGLER"))}
        self.env.update(
            GOKAPI_ENV_FILE=str(self.root / "absent.env"),
            GOKAPI_API_URL=f"http://127.0.0.1:{self.server.server_port}",
            GOKAPI_PUBLIC_URL="https://files.example.ts.net/", RELAY_DOMAIN="files-api.example.com",
            RELAY_KV_NAMESPACE_ID=NAMESPACE, WRANGLER=str(wrangler),
            FAKE_KV=str(self.kv), FAKE_KV_LOG=str(self.kv_log), FAKE_KV_NAMESPACE=NAMESPACE,
            GOKAPI_ADMIN_API_KEY_FILE=str(self.root / "admin"), PAIR_STATE_FILE=str(self.state))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def pair(self, *args, **extra_env):
        return subprocess.run([BIN / "pair", *args], env={**self.env, **extra_env}, capture_output=True, text=True)

    def link(self, stdout):
        return next(line for line in stdout.splitlines() if "/pair#" in line)

    def kv_data(self):
        return json.loads(self.kv.read_text()) if self.kv.exists() else {}

    def kv_calls(self):
        if not self.kv_log.exists():
            return []
        return [json.loads(line) for line in self.kv_log.read_text().splitlines()]

    def test_add_prints_contract_link_and_saves_no_secrets(self):
        result = self.pair("add", "pixel-9")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = decode_link(self.link(result.stdout))
        key = next(iter(FAKE.keys.values()))
        self.assertEqual(["v", "name", "url", "key", "relay", "relayId", "relaySecret"], list(payload))
        self.assertEqual({"v": 1, "name": "pixel-9", "url": "https://files.example.ts.net", "key": key["key"],
                          "relay": "https://files-api.example.com"},
                         {k: payload[k] for k in ("v", "name", "url", "key", "relay")})
        self.assertRegex(payload["relayId"], r"^pixel-9-[0-9a-f]{8}$")
        secret = payload["relaySecret"]
        self.assertRegex(secret, r"^[A-Za-z0-9_-]{43}$")  # 32 bytes, unpadded base64url
        self.assertEqual(32, len(base64.urlsafe_b64decode(secret + "=")))

        record = json.loads(self.kv_data()[f"device:{payload['relayId']}"])
        self.assertEqual({"name", "hash", "created"}, set(record))
        self.assertEqual("pixel-9", record["name"])
        self.assertEqual(hashlib.sha256(secret.encode()).hexdigest(), record["hash"])

        calls = self.kv_calls()
        self.assertEqual(1, len(calls))
        self.assertTrue(calls[0]["cwd"].endswith("/relay"))
        self.assertNotIn(secret, json.dumps(calls))

        self.assertEqual(["PERM_VIEW", "PERM_UPLOAD", "PERM_DOWNLOAD", "PERM_DELETE"], key["perms"])
        self.assertEqual(("gokapi-pixel-9", "false"), (key["name"], key["basic"]))
        self.assertEqual(0o600, self.state.stat().st_mode & 0o777)
        state = self.state.read_text()
        for value in (key["key"], secret, ADMIN_KEY):
            self.assertNotIn(value, state)
        self.assertIn(payload["relayId"], state)
        self.assertIn("is a credential", result.stdout)
        if not shutil.which("qrencode"):
            self.assertIn("dnf install qrencode", result.stdout)
        listing = self.pair("list")
        self.assertIn("pixel-9", listing.stdout)
        self.assertIn(payload["relayId"], listing.stdout)

    def test_each_pairing_gets_fresh_credentials(self):
        first = decode_link(self.link(self.pair("add", "phone").stdout))
        second = decode_link(self.link(self.pair("add", "tablet").stdout))
        self.assertNotEqual(first["relaySecret"], second["relaySecret"])
        self.assertEqual(2, len(self.kv_data()))
        self.assertNotEqual(0, self.pair("add", "phone").returncode)
        self.assertEqual(2, len(self.kv_data()))

    def test_kv_failure_rolls_back_key(self):
        result = self.pair("add", "pixel-9", FAKE_KV_FAIL="1")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("injected failure", result.stderr)
        self.assertEqual({}, FAKE.keys)
        self.assertFalse(self.state.exists())
        self.assertNotIn("/pair#", result.stdout)

    def test_permission_failure_rolls_back_key_before_kv(self):
        FAKE.fail.add("PUT /api/auth/modify")
        self.assertNotEqual(0, self.pair("add", "pixel-9").returncode)
        self.assertEqual({}, FAKE.keys)
        self.assertEqual([], self.kv_calls())
        self.assertFalse(self.state.exists())

    def test_remove_revokes_kv_entry_and_key(self):
        self.assertEqual(0, self.pair("add", "phone").returncode)
        self.assertEqual(0, self.pair("add", "tablet").returncode)
        result = self.pair("remove", "phone")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, len(FAKE.keys))
        self.assertEqual(1, len(self.kv_data()))
        self.assertTrue(next(iter(self.kv_data())).startswith("device:tablet-"))
        self.assertEqual(["tablet"], [d["name"] for d in json.loads(self.state.read_text())["devices"]])
        self.assertEqual(0, self.pair("remove", "tablet").returncode)
        self.assertEqual(({}, {}), (FAKE.keys, self.kv_data()))
        self.assertIn("No paired devices", self.pair("list").stdout)

    def test_remove_keeps_device_when_kv_delete_fails(self):
        self.assertEqual(0, self.pair("add", "phone").returncode)
        result = self.pair("remove", "phone", FAKE_KV_FAIL="1")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(1, len(FAKE.keys))
        self.assertEqual(["phone"], [d["name"] for d in json.loads(self.state.read_text())["devices"]])

    def test_rejects_bad_names_config_and_loose_secret_files(self):
        for name in ("Pixel", "pixel_9", "../x", "-x", ""):
            self.assertNotEqual(0, self.pair("add", name).returncode, name)
        self.assertNotEqual(0, self.pair("add", "pixel-9", RELAY_KV_NAMESPACE_ID="").returncode)
        self.assertNotEqual(0, self.pair("add", "pixel-9", RELAY_DOMAIN="https://x.example.com").returncode)
        (self.root / "admin").chmod(0o644)
        self.assertNotEqual(0, self.pair("add", "pixel-9").returncode)
        self.assertEqual([], FAKE.records)
        self.assertEqual([], self.kv_calls())


if __name__ == "__main__":
    unittest.main()
