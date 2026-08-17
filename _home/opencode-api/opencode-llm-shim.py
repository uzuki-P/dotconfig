#!/usr/bin/env python3
"""OpenAI-compatible facade over the opencode server API.

Speaks the subset OpenWhispr's custom LLM provider needs:
POST /v1/chat/completions (+ /chat/completions), GET /v1/models, GET /health.
Each completion creates a throwaway opencode session, prompts it, waits for
the reply, extracts the assistant text, and deletes the session.

Environment:
  SHIM_PORT               listen port (default 14097)
  SHIM_API_KEY            required Bearer key for incoming requests (optional)
  OC_BASE_URL             opencode server base (default http://127.0.0.1:14096)
  OPENCODE_SERVER_PASSWORD Bearer key for the opencode server (optional)
  OC_DEFAULT_PROVIDER     provider when the model string has no slash
  OC_DEFAULT_MODEL        model when the request omits one
  OC_AGENT                opencode agent used for completions (default plan)
  OC_WAIT_TIMEOUT         seconds to wait for a reply (default 120)
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OC_BASE = os.environ.get("OC_BASE_URL", "http://127.0.0.1:14096").rstrip("/")
OC_USERNAME = os.environ.get("OC_USERNAME", "opencode")
OC_PASSWORD = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
SHIM_API_KEY = os.environ.get("SHIM_API_KEY", "")
OC_PROVIDER = os.environ.get("OC_DEFAULT_PROVIDER", "zai-coding-plan")
OC_MODEL = os.environ.get("OC_DEFAULT_MODEL", "glm-4.7")
OC_AGENT = os.environ.get("OC_AGENT", "plan")
SHIM_PORT = int(os.environ.get("SHIM_PORT", "14097"))
WAIT_TIMEOUT = int(os.environ.get("OC_WAIT_TIMEOUT", "120"))


def oc_request(method, path, body=None, timeout=WAIT_TIMEOUT):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(OC_BASE + path, data=data, method=method)
    req.add_header("content-type", "application/json")
    if OC_PASSWORD:
        token = base64.b64encode(f"{OC_USERNAME}:{OC_PASSWORD}".encode()).decode()
        req.add_header("authorization", "Basic " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read()
            if not payload:
                return None
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                raise RuntimeError(
                    f"opencode {method} {path}: non-JSON response "
                    + payload[:200].decode(errors="replace")
                ) from None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"opencode {method} {path}: {exc.code} {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"opencode {method} {path}: {exc}") from exc


def resolve_model(model):
    model = (model or "").strip()
    if not model:
        return OC_PROVIDER, OC_MODEL
    if "/" in model:
        provider, _, mid = model.partition("/")
        return provider, mid
    return OC_PROVIDER, model


def build_prompt(messages):
    lines = []
    for msg in messages:
        role = (msg.get("role") or "user").lower()
        content = msg.get("content")
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        content = (content or "").strip()
        if not content:
            continue
        if role == "system":
            lines.append("System instructions:\n" + content)
        else:
            lines.append(role.capitalize() + ":\n" + content)
    return "\n\n".join(lines)


def run_completion(model_str, messages):
    provider, model = resolve_model(model_str)
    prompt = build_prompt(messages)
    session_id = None
    try:
        session = oc_request(
            "POST", "/session", {"title": "llm-shim"}, timeout=30
        )
        session_id = session["id"]
        oc_request(
            "POST",
            f"/session/{session_id}/message",
            {
                "model": {"providerID": provider, "modelID": model},
                "agent": OC_AGENT,
                "parts": [{"type": "text", "text": prompt}],
            },
        )
        # The message POST is synchronous; it returns once the reply completes.
        history = oc_request("GET", f"/session/{session_id}/message", timeout=30)
        text, usage = "", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        for message in history or []:
            info = message.get("info") or {}
            if info.get("role") != "assistant":
                continue
            parts = [
                part.get("text", "")
                for part in message.get("parts") or []
                if part.get("type") == "text"
            ]
            if parts:
                text = "\n".join(parts)
            tokens = info.get("tokens") or {}
            usage = {
                "prompt_tokens": tokens.get("input", 0),
                "completion_tokens": tokens.get("output", 0),
                "total_tokens": tokens.get("total", 0),
            }
        return text, usage, f"{provider}/{model}"
    finally:
        if session_id:
            try:
                oc_request("DELETE", f"/session/{session_id}", timeout=30)
            except RuntimeError:
                pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "opencode-llm-shim/1.0"

    def log_message(self, fmt, *args):
        print("shim: " + (fmt % args), flush=True)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, message):
        self.send_json(status, {"error": {"message": message, "type": "shim_error"}})

    def authorized(self):
        if not SHIM_API_KEY:
            return True
        header = self.headers.get("authorization", "")
        return header == "Bearer " + SHIM_API_KEY

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if not self.authorized():
            self.send_error_json(401, "Invalid API key")
            return
        if path in ("/v1/models", "/models"):
            try:
                config = oc_request("GET", "/config/providers", timeout=30)
            except RuntimeError as exc:
                self.send_error_json(502, str(exc))
                return
            models = []
            for provider in (config or {}).get("providers") or []:
                for mid in provider.get("models") or {}:
                    models.append({"id": f"{provider['id']}/{mid}", "object": "model", "owned_by": provider["id"]})
            self.send_json(200, {"object": "list", "data": models})
            return
        self.send_error_json(404, f"Unknown path {path}")

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        if not self.authorized():
            self.send_error_json(401, "Invalid API key")
            return
        if path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error_json(404, f"Unknown path {path}")
            return
        try:
            length = int(self.headers.get("content-length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self.send_error_json(400, "Invalid JSON body")
            return
        try:
            text, usage, model = run_completion(body.get("model"), body.get("messages") or [])
        except RuntimeError as exc:
            self.send_error_json(502, str(exc))
            return
        completion_id = "chatcmpl-" + uuid.uuid4().hex[:24]
        created = int(time.time())
        if body.get("stream"):
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-cache")
            self.end_headers()
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}],
            }
            final = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            for payload in (chunk, final):
                self.wfile.write(b"data: " + json.dumps(payload).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            return
        self.send_json(
            200,
            {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": usage,
            },
        )


def main():
    server = ThreadingHTTPServer(("127.0.0.1", SHIM_PORT), Handler)
    print(f"shim: listening on http://127.0.0.1:{SHIM_PORT} -> {OC_BASE}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
