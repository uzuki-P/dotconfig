# Relay: the Gokapi API for gokapi-android outside the tailnet

Status: implemented on the server side, not yet deployed. `relay/` (the
Worker), `deploy/cloudflared.container`, `bin/setup-relay`, `bin/pair`, and
the `relay-*`, `tunnel-*`, and `pair` recipes are in this directory. Devices
get their credentials through a pairing link.

## Goal

gokapi-android can reach this Gokapi without Tailscale. The public hostname
serves only the API calls the app makes. The admin UI, setup pages, download
pages, and hotlinks stay tailnet-only. A request needs two credentials: a
per-device relay secret and a per-device Gokapi API key.

## Design

```text
gokapi-android
  -> https://<relay domain>             Worker (relay/src/worker.js):
                                        per-IP rate limit, device secret,
                                        per-device rate limit, path allowlist
  -> Workers VPC service binding        private; no public hostname exists
  -> Cloudflare Tunnel                  remotely managed, outbound only
  -> cloudflared (rootless Podman, pasta forwards only port 53842)
  -> http://127.0.0.1:53842             Gokapi checks the API key
```

Everything on the Cloudflare side is managed with wrangler (pinned to
4.156.0 through `npx`). The tailnet route `files.<CADDY_TS_BASE_DOMAIN>` and
Caddy stay unchanged.

### Workers VPC facts this relies on

Workers VPC is in beta. From Cloudflare's docs, checked 2026-10-31:

| Fact | Source |
| --- | --- |
| Binding: `"vpc_services": [{ "binding": "GOKAPI", "service_id": "<id>" }]` (`"remote": true` only matters for `wrangler dev`) | [VPC Services](https://developers.cloudflare.com/workers-vpc/configuration/vpc-services/) |
| `env.GOKAPI.fetch(url, init)` takes an absolute URL. The VPC service's host and port always decide where the request goes; the URL's host only sets the `Host` header (and SNI for https), and its port is ignored. | [Workers Binding API](https://developers.cloudflare.com/workers-vpc/api/) |
| `wrangler vpc service create <name> --type http --tunnel-id <id> --ipv4 <ip> --http-port <port>` | [Get started](https://developers.cloudflare.com/workers-vpc/get-started/), `wrangler vpc service create --help` |
| Ingress rules are not required; routing comes from the VPC service. Remotely managed tunnels are recommended. cloudflared 2025.7.0 or later. | [Tunnel configuration](https://developers.cloudflare.com/workers-vpc/configuration/tunnel/) |
| `fetch()` throws when the service can't be reached (the relay answers 502). | [VPC Services](https://developers.cloudflare.com/workers-vpc/configuration/vpc-services/) |
| Free on all Workers plans during the beta; 1000 VPC services per account; otherwise standard Workers limits | [Limits](https://developers.cloudflare.com/workers-vpc/reference/limits/) |
| Workers limits: request bodies up to 100 MB on Free and Pro zones, no response size limit, no duration limit while the client is connected, 10 ms CPU on Workers Free, 100,000 requests a day on Workers Free | [Workers limits](https://developers.cloudflare.com/workers/platform/limits/) |
| Rate limiting binding: `ratelimits` with `name`, `namespace_id`, `simple.limit`, `simple.period` (10 or 60); approximate and counted per Cloudflare location | [Rate Limiting](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/) |

Not confirmed by the docs, so check them during the first deployment:

- `--ipv4 127.0.0.1`. The get-started page lists `localhost` as an example
  host, but never says loopback is accepted. Here cloudflared dials its own
  container's 127.0.0.1:53842, which pasta forwards to the host's.
- Whether VPC traffic needs a private network (CIDR) route on the tunnel.
  The docs mention none; don't add one.
- Request body streaming through the binding and any VPC-specific size or
  time limit. The Worker streams both directions; the 100 MB edge limit is
  the one known cap.

### 1. Tunnel

- `just relay-tunnel` runs `wrangler tunnel create gokapi-relay`, which
  creates a remotely managed tunnel (`config_src: cloudflare`). It has no
  public hostname and no ingress rules, so nothing can reach it from the
  internet; only the VPC binding uses it.
- wrangler's OAuth login has no tunnel permission (wrangler 4.156 says so
  when `tunnel create` runs). Tunnel commands use an API token with only
  Account > Cloudflare Tunnel > Edit, kept in `secrets/cf-tunnel-api-token`
  (mode 0600). Everything else uses the OAuth login.
- No wrangler command prints the tunnel's run token (`wrangler tunnel run`
  fetches it internally). `just relay-tunnel-token` gets it from
  `GET /accounts/{account}/cfd_tunnel/{tunnel}/token` with that API token
  and writes `secrets/tunnel-token` with mode 0600. The dashboard's tunnel install command shows the same
  token if that ever fails.
- cloudflared runs as a rootless Podman Quadlet (`deploy/cloudflared.container`)
  with a pinned image, `NoNewPrivileges`, `DropCapability=all`, and a
  read-only root filesystem. The token file is bind-mounted read-only and read
  with `--token-file`, so the token is never in the container's environment,
  argv, or `podman inspect` output. An `EnvironmentFile=` would put it in all
  three; a Podman secret would need an extra `podman secret create` step for
  the same result as the mount.
- Networking: `Network=pasta:-T,53842`. The container keeps its own network
  namespace, and pasta forwards only its loopback port 53842 to the host's
  `127.0.0.1:53842`. Even if someone added routes or ingress rules to this
  remotely managed tunnel, it could reach nothing else on the host.
- `UserNS=keep-id:uid=65532,gid=65532` lets the image's nonroot user read the
  user-owned mode 0600 token file.

### 2. Worker

`relay/src/worker.js` is plain JavaScript with no dependencies. For every
request it:

1. Applies the per-IP rate limit (`IP_LIMITER`, keyed on `CF-Connecting-IP`).
2. Authenticates: `X-Relay-Id` and `X-Relay-Secret` headers. KV key
   `device:<id>` in `DEVICES` holds `{"name","hash","created"}`, where `hash`
   is the hex SHA-256 of the secret. The Worker hashes the presented secret
   and compares the two digests in constant time. Missing or wrong
   credentials get 401 with `X-Relay-Error: unauthorized`, on every path, so
   probes learn nothing about the routes.
3. Applies the per-device rate limit (`DEVICE_LIMITER`).
4. Allows only the routes `GokapiClient.kt` calls; everything else is 404
   with `X-Relay-Error: not-allowed`:

   | Method | Path |
   | --- | --- |
   | GET | `/api/info/version`, `/api/info/config` |
   | GET | `/api/files/list`, `/api/files/list/{id}`, `/api/files/download/{id}` |
   | DELETE | `/api/files/delete` |
   | POST | `/api/chunk/add`, `/api/chunk/complete` |

   `{id}` is `[A-Za-z0-9_-]{1,128}`, which keeps percent-encoded slashes and
   dots out.
5. Forwards method, path, query, and the streamed body to
   `http://127.0.0.1:53842` through the binding with `redirect: "manual"`.
   It drops hop-by-hop headers, `X-Relay-*`, `CF-*`, `X-Forwarded-*`,
   `Forwarded`, `Host`, and `Cookie`, and sets `X-Forwarded-For` to
   `CF-Connecting-IP`. Gokapi trusts that header only from 127.0.0.1
   (`GOKAPI_TRUSTED_PROXIES`), which is where the tunnel connects from, so
   its logs show the real client instead of the tunnel.
6. Streams Gokapi's response back with `Cache-Control: no-store` and without
   `Set-Cookie`. Gokapi's own errors, such as 401 for a bad API key, pass
   through unchanged and without `X-Relay-Error`.

A tunnel that's down gives 502 with `X-Relay-Error: upstream-unreachable`.
There are no other routes. A login page could be dispatched in
`handleRequest` before the API allowlist later.

KV reads are cached at the edge for 60 seconds, so an unpaired device can
keep working for up to a minute. Both rate limits are 240 requests a minute
per location; a 1 GB upload is about 23 chunk requests.

`relay/test/worker.test.js` (`just relay-test`, run by `just validate`) runs
the Worker against fake KV, VPC, and rate limiter bindings with `node --test`.

#### Config without the domain or IDs in git

`relay/wrangler.template.jsonc` is tracked with `__RELAY_DOMAIN__`,
`__RELAY_VPC_SERVICE_ID__`, and `__RELAY_KV_NAMESPACE_ID__` placeholders.
`just relay-config` fills them from `.env` into `relay/wrangler.jsonc`, which
is ignored, and `relay-deploy` and `relay-logs` run it first. The IDs aren't
secrets, but this repository is public and the earlier relay design kept
them out too, so all relay values live in the one ignored `.env` that
`bin/pair` already reads. The domain is a Workers custom domain
(`routes[].custom_domain`), so its zone must be on the account.

### 3. Gokapi API key

Each device gets its own Gokapi key with only `PERM_VIEW`, `PERM_UPLOAD`,
`PERM_DOWNLOAD`, and `PERM_DELETE`. Without the API management permission, a
stolen key cannot create keys, and the Worker blocks those routes anyway.
`bin/pair` creates these keys on loopback with an admin key in
`secrets/admin-api-key` that has only API management (`PERM_API_MOD`).
`PERM_DOWNLOAD` is missing from the v2.2.4 OpenAPI enum, but the server
defines it and `/api/files/download/{id}` requires it.

No setup can prove that a request comes from the gokapi-android APK.
Anything the app holds can be extracted from a device, so the credentials are
per device and delivered by a pairing link, never built into the APK.

## Pairing

`just pair <device>` (`bin/pair add`) does, in order:

1. `POST /api/auth/create` with `friendlyName: gokapi-<device>` and
   `basicPermissions: false`, then one `PUT /api/auth/modify` per permission
   above with `permissionModifier: GRANT`.
2. Generates the relay ID `<device>-<8 random hex>` and a 32-byte random
   secret (unpadded base64url), and writes `device:<id>` with the secret's
   SHA-256 through `wrangler kv key put --namespace-id <id> --remote`.
3. Records the device, relay ID, the key's public ID, and the date in
   `secrets/pairs.json` (mode 0600). No secret is written to disk.
4. Prints a pairing link and, when `qrencode` is installed, a terminal QR
   code.

If a step fails, the script deletes the Gokapi key it created. `just unpair
<device>` deletes the KV entry first (which revokes relay access), then the
Gokapi key, then the state entry. `WRANGLER` overrides the wrangler command.

The link is `${GOKAPI_PUBLIC_URL}/pair#<payload>`, where the payload is
unpadded base64url of UTF-8 JSON:

```json
{"v":1,"name":"<device>","url":"<GOKAPI_PUBLIC_URL>","key":"<gokapi key>","relay":"https://<relay domain>","relayId":"<relay id>","relaySecret":"<relay secret>"}
```

The app sends `X-Relay-Id` and `X-Relay-Secret` on every request to the
relay, including chunk uploads and downloads, and uses the tailnet URL when
it's reachable. The secrets sit in the fragment, which browsers never send
to a server. The link is a credential: open it only on the device it was
made for. `bin/test-pair.py` runs the script against a fake Gokapi and a fake
wrangler and checks the payload, the KV record, and the rollback.

## Limits

- Request bodies over 100 MB are rejected at the edge on Free and Pro zones.
  Gokapi's `ChunkSize` is 45 MB and the app uploads with the chunk API, so
  uploads work. Do not raise `ChunkSize` above about 95 MB.
- Workers Free allows 100,000 requests a day and 10 ms of CPU per request.
  The Worker only hashes one secret and streams bodies, which costs little
  CPU, but heavy use belongs on Workers Paid.
- KV Free allows 100,000 reads a day; the 60-second edge cache keeps a
  device's reads low.
- Responses still contain `UrlDownload` and `UrlHotlink` on the tailnet
  host. People outside the tailnet cannot open them.

## Files

| Path | Purpose |
| --- | --- |
| `relay/src/worker.js` | The relay Worker |
| `relay/test/worker.test.js` | Worker tests (`just relay-test`) |
| `relay/wrangler.template.jsonc` | Worker config with placeholders |
| `relay/wrangler.jsonc` (ignored) | Generated by `just relay-config` |
| `deploy/cloudflared.container` | Rootless Quadlet for the tunnel |
| `bin/setup-relay` | One-time setup wizard (`just relay-setup`) |
| `bin/pair` | Per-device credentials and pairing links (`just pair`, `unpair`, `pairs`) |
| `bin/test-pair.py` | Offline test of `bin/pair`, run by `just validate` |
| `.env` (ignored) | `RELAY_DOMAIN`, `RELAY_TUNNEL_ID`, `RELAY_VPC_SERVICE_ID`, `RELAY_KV_NAMESPACE_ID` |
| `secrets/tunnel-token` (ignored) | Tunnel run token, mode 0600 |
| `secrets/cf-tunnel-api-token` (ignored) | API token for tunnel commands, mode 0600 |
| `secrets/admin-api-key` (ignored) | Gokapi key with only API management |
| `secrets/pairs.json` (ignored) | Paired devices and IDs, no secrets |

## Setup

`just relay-setup` runs `bin/setup-relay`, which walks through each step and
skips the ones already done:

1. Checks the tools, Gokapi on loopback, and the wrangler login.
2. Gokapi admin key with only API management, saved to
   `secrets/admin-api-key`.
3. Relay domain (its zone must be on the account), saved as `RELAY_DOMAIN`.
4. A tunnel API token (Account > Cloudflare Tunnel > Edit) saved to
   `secrets/cf-tunnel-api-token`, then `just relay-tunnel`, saved as
   `RELAY_TUNNEL_ID`.
5. `just relay-tunnel-token` into `secrets/tunnel-token`.
6. `just relay-vpc`, saved as `RELAY_VPC_SERVICE_ID`.
7. `just relay-kv`, saved as `RELAY_KV_NAMESPACE_ID`.
8. `just relay-deploy`.
9. `just tunnel-install` and `just tunnel-start`.
10. `just relay-smoke`, then `just pair <device>` for each device.

## Verification

Run these from a machine outside the tailnet, such as a phone on mobile data.
`id` and `secret` are a paired device's relay credential.

| Request | Expected |
| --- | --- |
| `curl -i https://<relay>/api/info/version` | 401, `X-Relay-Error: unauthorized` |
| The same with `X-Relay-Id: <id>` and a wrong `X-Relay-Secret` | 401, `X-Relay-Error: unauthorized` |
| The same with the right secret and no `apikey` | 401 JSON from Gokapi, no `X-Relay-Error` |
| The same with the right secret and `apikey: <device key>` | 200 with the version |
| `/admin` with the right secret | 404, `X-Relay-Error: not-allowed` |
| `/api/auth/create` with the right secret and key | 404, `X-Relay-Error: not-allowed` |
| The tunnel itself | Nothing to request: it has no public hostname |
| App: test connection, list, 100 MB upload, download, delete | All succeed |
| After `just unpair <device>` and a minute, the same request | 401, `X-Relay-Error: unauthorized` |

Also confirm `ss -ltn` shows no new listener on this machine, and that the
tunnel has no public hostname in the dashboard.

## Rollback

`just tunnel-stop` and `just unpair` each device. Then delete the Worker
(`wrangler delete --name gokapi-relay`), the VPC service
(`wrangler vpc service delete <id>`), the KV namespace, and the tunnel
(`wrangler tunnel delete gokapi-relay`). Gokapi and the tailnet route are
unaffected.
