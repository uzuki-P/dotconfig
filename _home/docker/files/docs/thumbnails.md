# Thumbnail service

Status, 2026-11-08: stage 1 is running (text and image previews on the tailnet,
`https://files-thumbs.<tailnet base>`). Stages 2 to 5 are still design.

A small loopback service, `gokapi-thumbs`, that makes previews for files on the
Gokapi server: an icon for APK and EXE files, a frame for videos, a scaled image
for pictures, and the first lines of text for Markdown and plain text. The
Android and desktop apps (`~/projects/_sandbox/gokapi-android`) load them over
Tailscale and over the relay with the same request. gokapi-admin can use it too.

## Goals

- One implementation for every client. The apps only fetch and cache what the
  service returns.
- Works on the tailnet and through the relay with the same path,
  `/api/thumbnail/{id}`. On the tailnet it has its own host, `files-thumbs`;
  through the relay it shares the relay's host.
- No new credentials on devices. The app's existing Gokapi API key decides
  access.
- No change to Gokapi itself, and no reliance on its storage layout.

Non-goals: rendering whole documents, video playback, encrypted files.

## Request flow

```
Tailscale:  app -> Caddy (files-thumbs.<tailnet>) --> 127.0.0.1:53845 gokapi-thumbs
            app -> Caddy (files.<tailnet>)        --> 127.0.0.1:53842 Gokapi
Relay:      app -> Worker (checks X-Relay-*, allowlist)
                   -- /api/thumbnail/{id} --> VPC service THUMBS -> tunnel -> 127.0.0.1:53845
                   -- other /api routes   --> VPC service GOKAPI -> tunnel -> 127.0.0.1:53842
gokapi-thumbs -> Gokapi API on 127.0.0.1:53842 (auth check, metadata, file bytes)
```

## API

`GET /api/thumbnail/{id}?size=s|l`

- `size=s` (default): 160 px square, center-cropped, for list rows.
- `size=l`: fits within 960 px, not cropped, for the details pane.
- Header `apikey`: the caller's Gokapi API key, exactly as the app already
  sends it.

Responses:

| Status | Body | Meaning |
|---|---|---|
| 200 `image/webp` | Thumbnail | Images, video frames, APK/EXE icons |
| 200 `text/plain; charset=utf-8` | First lines | Markdown and plain text (see below) |
| 204 | none | No preview for this file (unknown type, encrypted, icon not found). The client shows its type badge and remembers the answer. |
| 401 / 403 / 404 | Gokapi-style JSON error | Passed through from Gokapi's answer to the auth check |
| 503 | JSON error | Generation timed out or the queue is full; the client retries later |

Every 200 carries `ETag: "<id>-<size>-v<generator version>"`. Gokapi files never
change content under an ID, so the client can cache by that tag indefinitely.
The relay Worker sets `cache-control: no-store`, so clients keep their own
disk cache and do not rely on HTTP caching.

Text previews are returned as text, not drawn into an image, so the apps render
them in their own fonts and in light and dark themes. The service takes the
first 8 KB, decodes it as UTF-8 (falling back to Latin-1), skips blank lines and
front matter, strips Markdown syntax (`#`, `>`, list markers, emphasis, link
targets, code fences), and returns up to 3 lines and 240 characters. The list
row shows 2 lines, and the details pane shows all 3.

## Access control

For every request the service calls Gokapi's
`GET /api/files/list/{id}` with the caller's `apikey`:

- If Gokapi refuses it, the service returns the same status. So a thumbnail is
  exactly as visible as the file's metadata (VIEW permission), and revoking a
  key or unpairing a device revokes thumbnails too.
- A 200 answer gives the name, content type, size, and encryption flags that
  pick the generator.

The service never stores callers' keys. To read file contents it uses its own
key, `secrets/thumbs-api-key`, with VIEW and DOWNLOAD only. That key never
leaves the host.

Successful auth checks are cached in memory for 60 seconds per (key hash, ID),
so opening a list of 40 files costs at most 40 quick loopback calls.

## Reading files

Gokapi's API does not expose the stored file's SHA1 name, so the service does
not read `data/` directly. It uses `GET /api/files/download/{id}` on loopback
with its own key. That route serves partial requests and does not change the
download count unless asked to (checked in Gokapi v2.2.4,
`internal/storage/FileServing.go`).

| Kind | Detection | How |
|---|---|---|
| Image | `image/*` | Download (cap 40 MB), Pillow: EXIF rotate, crop or fit, WebP |
| Video | `video/*` or `.mp4/.mkv/.mov/.webm` | `ffmpeg -ss <10% of duration, max 5 s> -i <download URL with headers> -frames:v 1`. ffmpeg uses partial requests, so it reads only the index and a few frames. |
| APK | `.apk` or the APK content type | Download to a temp file. androguard reads the manifest and follows `android:icon`/`roundIcon` through `resources.arsc`. Bitmap icons: the highest density PNG/WebP. Adaptive icons: each layer is a bitmap or a VectorDrawable; vector layers are converted to SVG (colors and `@color` references resolved from `resources.arsc`) and rasterized, then foreground and background are composited on a rounded square. Clients only ever get WebP: they could not draw a VectorDrawable fetched at runtime, and a rasterized icon costs only a few KB more. |
| EXE | `.exe/.dll`, PE magic | Download to a temp file. pefile reads `RT_GROUP_ICON`/`RT_ICON`, takes the largest image (PNG or BMP entry), and encodes WebP. |
| Text | `.md/.markdown/.txt/.log` or `text/*` | Partial request for the first 8 KB, then the text rules above |
| Other | anything else | 204 |

Encrypted files (`IsEncrypted` or `RequiresClientSideDecryption`) and files
still being processed get 204 without a download.

## Generation and caching

- **On demand**, with results stored under `thumbs-cache/<id>/v<version>-<size>.webp`
  (or `.txt`, or a `.none` marker for 204). Generation is serialized per ID, so
  ten devices asking at once trigger one job.
- **Pre-warming**: every 5 minutes the service lists files with its own key
  and generates `s` for files it has not seen, so new uploads are usually ready
  before anyone opens the list. The same pass deletes cache folders for IDs no
  longer listed (deleted or expired).
- Two workers at a time, 512 MB of memory for the container. Images over 40 MB
  are skipped. Later stages add per-job time limits for ffmpeg and APK
  parsing. A failed job leaves a `failed` marker that is retried after
  an hour.
- Raising the generator version (`GENERATOR_VERSION`) changes the ETag and
  invalidates old thumbnails after a change to how they are made.

Disk use: about 10–40 KB per file for `s`, about 100 KB for `l`. A few
megabytes for the current file count.

## Deployment

New files under `~/docker/files`:

| Path | Purpose |
|---|---|
| `thumbs/` | Service source (`server.py`: Python 3 stdlib HTTP server and Pillow; later androguard, pefile, ffmpeg), `Containerfile`, `test_server.py` |
| `deploy/gokapi-thumbs.container` | Rootless Quadlet, image `localhost/gokapi-thumbs:<n>` |
| `thumbs-cache/` | Cache directory (ignored) |
| `secrets/thumbs-api-key` | The service's VIEW+DOWNLOAD key (ignored) |

Quadlet, modeled on `cloudflared.container`:

- `PublishPort=127.0.0.1:53845:53845`. (53843 and 53844 are taken by other
  services on this host.)
- `Network=pasta:-T,53842`, so the container reaches only Gokapi on host
  loopback, and nothing else on the host. The service needs no internet
  access. Blocking outbound internet entirely needs a further pasta option or
  firewall rule, to be checked.
- `ReadOnly=true`, `NoNewPrivileges=true`, `DropCapability=all`, UID 10001
  mapped to the host user (`UserNS=keep-id`), the cache volume as the only
  writable mount, and `--memory=512m --pids-limit=128`.
- `Wants=`/`After=gokapi.service`.

Justfile recipes: `thumbs-key` (creates the VIEW+DOWNLOAD key with
`secrets/admin-api-key`), `thumbs-test`, `thumbs-build`, `thumbs-install`
(build, install the Quadlet, restart), `thumbs-route`, `thumbs-status`, and
`thumbs-logs`. `validate` runs the Quadlet checks and the service's tests.

## Tailscale routing

A separate host, `files-thumbs`, from `just thumbs-route`
(`just specific files-thumbs 53845` in the dev-router). Caddy's wildcard DNS
record and certificate already cover it, so no Tailscale, DNS, or Caddyfile
change was needed.

The apps find the thumbnail host by adding `-thumbs` to the first label of
`serverUrl` (`files.<base>` becomes `files-thumbs.<base>`). Later, pairing links
carry it as an optional `thumbs` field, and server settings get an override.

Because it is a different origin from the files UI, the service answers CORS
requests from the origins listed in `THUMBS_CORS_ORIGINS` (none by default).

## Relay changes

The Worker already passes the `apikey` header through and strips `X-Relay-*`.

1. `just relay-vpc` gains a second VPC service, `gokapi-thumbs`: HTTP, the same
   tunnel, `127.0.0.1:53845`. Saved as `RELAY_THUMBS_VPC_SERVICE_ID`. This adds
   no new tunnel or public hostname, and VPC services are free during the beta.
2. `cloudflared.container`: `Network=pasta:-T,53842,-T,53845`, so the tunnel
   can reach the new port. Not a port range: 53843 and 53844 belong to other
   services.
3. `wrangler.template.jsonc`: a `THUMBS` binding next to `GOKAPI`.
4. `src/worker.js`: allow `GET ^/api/thumbnail/{FILE_ID}$` with an optional
   `size=s|l` query, and send it to `env.THUMBS`. Everything else stays on
   `env.GOKAPI`. Tests cover the new route, a bad `size`, and an unreachable
   service (502).
5. `docs/relay.md`: the new route and the port.

Load: about 40 requests per device to fill an empty cache, then about one per
new upload. Relay traffic for 2026-11-01 to 2026-11-08 peaked at 938 requests
a day, against the 100,000 a day free limit. The rate limiters (240 a minute)
leave room for a full list's burst. Requests only pass through the Worker, so
CPU time stays near today's (p99 4–7 ms, limit 10 ms).

## Client changes (gokapi-android and desktop)

- `GokapiClient.thumbnail(c, file, size)`: the same tailnet-then-relay
  routing as other calls. Returns `Image(bytes)`, `Text(lines)`, or `None`.
- A shared disk cache: `thumbs/<id>-<size>` with the ETag. Negative answers
  are kept for a day. Entries are dropped when the ID leaves the file list.
- Android: decode the bytes into a Coil image (a small custom fetcher keyed by
  ID and size). Desktop: extend `Thumbnails.kt` to use the client instead of
  hotlinks.
- `FileThumbnail` and `FileDetailsPane`: show the image, show text cards for
  text answers (2 lines in rows, 3 in the pane), and keep the badge for `None`,
  while loading, and offline.
- Images also move to the service. Today the apps load image hotlinks, and each
  view raises the file's download count. Thumbnails from the service do not.
- Old servers without the service answer 404 on this path. The client treats
  that as "no thumbnails" for the session.

## Rollout

1. Service with text and image previews, Quadlet, `files-thumbs` route (done
   2026-11-08). Apps use it on the tailnet only.
2. Video frames and EXE icons.
3. APK icons: bitmap, adaptive, and vector layers rasterized.
4. Relay: VPC service, tunnel port, Worker route and tests.
5. Optional: PDF first pages, ZIP file lists, pairing `thumbs` field and
   settings override.

## Decisions

- Tailscale: a separate `files-thumbs` host rather than a path route on
  `files`.
- Access: VIEW is enough, matching what the file list already shows.
- APK icons: vector layers are rasterized on the server; clients get WebP.

## Open questions

- Whether pre-warming should also make `l` thumbnails, or only on demand. Today
  `l` is made on demand.
