# Speaches

[Speaches](https://github.com/speaches-ai/speaches) serves faster-whisper
models behind an OpenAI-compatible API. It runs as a rootless Podman Quadlet
managed by the user systemd instance and backs OpenWhispr's Self-Hosted
transcription mode (and any OpenAI SDK pointed at it).

- API: `http://127.0.0.1:9457/v1` (loopback only, container port 8000)
- Private tailnet URL: `https://whisper.<CADDY_TS_BASE_DOMAIN>/v1`, published
  with the sibling dev-router: `cd ../dev-router && just specific whisper 9457`
- Model: `Systran/faster-whisper-base`, fetched into the cache volume on
  first run (`just fetch-model`, also run by `just setup`) and kept resident
  (`WHISPER__TTL=-1`). Multilingual (~99 languages) with auto-detect.

The listener binds to `127.0.0.1` only, so the service is reachable from this
host and through the tailnet Caddy route; nothing else can connect. Caddy's
wildcard listeners already bind solely to loopback and the Tailscale address,
which keeps the published URL private to the tailnet.

## OpenWhispr client

Settings -> Transcription -> Self-Hosted:

| Field | Value |
| --- | --- |
| Server URL | `https://whisper.<CADDY_TS_BASE_DOMAIN>/v1` (tailnet) or `http://127.0.0.1:9457/v1` (local) |
| Model | `Systran/faster-whisper-base` |

No API key is required unless `API_KEY` is set in the Quadlet.

## Usage

Run `just setup` to install the Quadlet files and start it, `just status` to
inspect it, `just logs` while testing, and `just update` to move to a newer
image. Run `just` for the full command list. The `speaches-hf-cache` named
volume keeps downloaded Hugging Face models across restarts, so `just stop`
and reboots do not re-download the base model.

Test from the host:

```bash
curl http://127.0.0.1:9457/health
curl http://127.0.0.1:9457/v1/audio/transcriptions \
  -F file=@audio.wav -F model=Systran/faster-whisper-base
```

## Switching models

Ask the server to fetch another Hugging Face model id, then use that id in the
client's Model field:

```bash
curl -X POST 'http://127.0.0.1:9457/v1/models/Systran%2Ffaster-whisper-large-v3'
```

Models are cached in the `speaches-hf-cache` named volume. For a GPU, switch
the image tag to `latest-cuda` and add a `GlobalArgs=--gpu nvidia` quadlet
option (requires nvidia-container-toolkit with CDI enabled).
