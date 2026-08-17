# opencode-api

Publishes the local [opencode](https://opencode.ai) server (GLM via the
Z.AI coding plan) as an OpenAI-compatible chat API so OpenWhispr's custom
LLM provider (dictation cleanup / text processing) can use it.

Two user systemd services:

| Unit | Purpose |
| --- | --- |
| `opencode-serve.service` | `opencode serve` on `127.0.0.1:14096` (opencode's own REST API) |
| `opencode-llm.service` | stdlib-Python shim on `127.0.0.1:14097` exposing `POST /v1/chat/completions`, `GET /v1/models`, `GET /health` |

Each completion creates a throwaway opencode session, prompts it with the
joined OpenAI messages, waits for the reply, returns the assistant text in an
OpenAI envelope (real token usage included), and deletes the session. Both
`stream` and non-stream requests are supported; streaming emits the full reply
as one chunk. Requests to the opencode server carry `OPENCODE_SERVER_PASSWORD`
when set; incoming requests must present `SHIM_API_KEY` as a Bearer token when
set.

- Local endpoint: `http://127.0.0.1:14097/v1`
- Private tailnet URL: `https://llm.<CADDY_TS_BASE_DOMAIN>/v1`, published with
  the sibling dev-router: `cd ../dev-router && just specific llm 14097`
- Default model: `zai-coding-plan/glm-4.7` with the read-only `plan` agent
  (`OC_AGENT` in the env file to change)

Both listeners bind to loopback only, so the API is reachable from this host
and through the tailnet Caddy route; nothing else can connect.

## OpenWhispr client

Settings -> AI Text Processing (dictation cleanup) -> provider **Custom**:

| Field | Value |
| --- | --- |
| Base URL | `https://llm.<CADDY_TS_BASE_DOMAIN>/v1` (tailnet) or `http://127.0.0.1:14097/v1` (local) |
| Model | `zai-coding-plan/glm-4.7` (or bare `glm-4.7`) |
| API key | `SHIM_API_KEY` from `~/.config/opencode-api/env` (`just key` prints it) |

## Usage

Run `just setup` to generate the env file, install the units, and start both
services. `just status`, `just logs`, `just restart`, and `just stop` manage
them; `just` lists everything. The env file holds both random keys and is
never committed (`env.example` documents the variables).

Test from the host:

```bash
KEY=$(cd ~/opencode-api && just key)
curl http://127.0.0.1:14097/v1/models -H "authorization: Bearer $KEY"
curl http://127.0.0.1:14097/v1/chat/completions \
  -H "authorization: Bearer $KEY" -H 'content-type: application/json' \
  -d '{"model":"glm-4.7","messages":[{"role":"user","content":"Say hello"}]}'
```

## Notes

- The shim intentionally exposes only models and chat completions; the rest of
  opencode's API (sessions, files, config — which includes provider keys)
  stays on loopback, unreachable through the published route.
- Sessions are created per request; concurrent requests each get their own.
- The opencode binary is reached through the mise shim at
  `~/.local/share/mise/shims/opencode`; if the install moves, update
  `ExecStart` in `opencode-serve.service`.
