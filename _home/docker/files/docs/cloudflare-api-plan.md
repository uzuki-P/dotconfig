# Plan: publish the Gokapi API to gokapi-android through Cloudflare

Status: planned, not implemented.

## Goal

gokapi-android can reach this Gokapi without Tailscale. The public hostname
serves only the API calls the app makes. The admin UI, setup pages, download
pages, and hotlinks stay tailnet-only. A request needs two credentials: a
Cloudflare Access service token and a Gokapi API key.

## Design

```text
gokapi-android
  -> https://files-api.<public-domain>    Cloudflare edge: DDoS protection,
                                          Access service-token check,
                                          rate-limit rule
  -> Cloudflare Tunnel (outbound only from this machine)
  -> cloudflared ingress path allowlist
  -> http://127.0.0.1:53842               Gokapi checks the API key
```

The tailnet route `files.<CADDY_TS_BASE_DOMAIN>` and Caddy stay unchanged.
cloudflared connects to Gokapi's loopback port directly.

### 1. Tunnel and hostname

- Use a locally managed tunnel, so the ingress rules live in a file in this
  directory and not only in the dashboard.
- Use a hostname outside the `*.<CADDY_TS_BASE_DOMAIN>` wildcard, such as
  `files-api.<public-domain>`. That wildcard is a DNS-only record that points
  at the tailnet address.
- The tunnel only makes outbound connections. No router port opens, and the
  home IP does not appear in DNS.
- Run cloudflared as a rootless Podman Quadlet next to `gokapi.container`,
  with a pinned `docker.io/cloudflare/cloudflared` image, `NoNewPrivileges`,
  and `DropCapability=all`.

### 2. Path allowlist

Only the routes gokapi-android calls (`GokapiClient.kt`) reach Gokapi:

```yaml
# deploy/cloudflared.yml.example. The real file is ignored by git.
tunnel: <TUNNEL_ID>
credentials-file: /etc/cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: files-api.<public-domain>
    path: ^/api/(info/(version|config)|files/(list(/[^/]+)?|download/[^/]+|delete)|chunk/(add|complete))$
    service: http://127.0.0.1:53842
  - service: http_status:404
```

Every other path returns 404 from cloudflared without reaching Gokapi. That
includes `/admin`, `/login`, `/setup`, `/d`, `/h`, `/apidocumentation`, and
the key, user, log, and file request parts of `/api`.

Before enabling the tunnel, check the regex against the app's current client
code. If the app adds an endpoint later, add it here too.

### 3. Cloudflare Access service token

- In Zero Trust, create a self-hosted Access application for
  `files-api.<public-domain>`, covering all paths.
- Give it one policy with the action Service Auth that includes one service
  token per device, such as `android-pixel`.
- Every request must send `CF-Access-Client-Id` and `CF-Access-Client-Secret`.
  Cloudflare answers requests without valid headers with 403 at the edge, so
  scanners and flood traffic never enter the tunnel.
- Set a token duration, for example one year, and note the expiry date. To
  revoke a lost phone, delete its token.

No setup can prove that a request comes from the gokapi-android APK. Anything
the app holds can be extracted from a device. Play Integrity needs Play Store
distribution, and this app is sideloaded. So the tokens are per-device
credentials typed into Settings, never built into the APK.

### 4. Gokapi API key

Use a separate Gokapi key for the public route with only View, Upload,
Download, and Delete. Without the API management permission, a stolen key
cannot create keys, and the ingress allowlist blocks those routes anyway.

### 5. Edge protection

- DDoS protection is on by default for proxied hostnames on every plan.
- Add the free plan's single rate-limit rule for this hostname. For example,
  allow 60 requests per 10 seconds per IP and block for 10 seconds. A 1 GB
  upload is about 23 sequential chunk requests at the 45 MB chunk size, so
  normal use stays far below the limit.
- Add a cache rule that bypasses the cache for this hostname, so Cloudflare
  never stores API responses or file bytes.
- Optional: a WAF custom rule that blocks countries or ASNs you never use.

### 6. Limits

- Cloudflare's free plan rejects request bodies over 100 MB. Gokapi's
  `ChunkSize` is 45 MB and the app uploads with the chunk API, so uploads
  work. Do not raise `ChunkSize` above about 95 MB.
- Responses still contain `UrlDownload` and `UrlHotlink` on the tailnet host.
  The app can show and copy them, but people outside the tailnet cannot open
  them.
- Cloudflare's terms discourage serving mostly large media through the CDN.
  Personal file transfer through a tunnel is normal use. Do not use this
  hostname for public video hosting.

## gokapi-android changes

- `data/server/CredentialStore.kt`: store an optional Access client ID and
  secret per server, encrypted like the API key.
- `data/server/GokapiClient.kt`: in the request builder at
  `.header("apikey", c.apiKey)`, also add the two `CF-Access-*` headers when
  they are set. The same headers go on chunk uploads and downloads.
- Settings, Server: add the two optional fields under the API key. Test
  connection should report a missing or wrong service token. Access answers
  with 403 and an HTML body, not Gokapi's JSON error.
- Error messages that mention Tailscale should not appear for the public
  hostname.
- Add tests: `GokapiClientTest` checks that the headers are sent when set and
  omitted when empty.

## Files in this directory

| Path | Purpose |
| --- | --- |
| `deploy/cloudflared.container` | Rootless Quadlet for cloudflared |
| `deploy/cloudflared.yml.example` | Ingress template with placeholders |
| `cloudflared/` (ignored) | Real `config.yml` and tunnel credentials JSON |
| `justfile` | `tunnel-install`, `tunnel-start`, `tunnel-status`, `tunnel-logs`, `tunnel-stop` |

Real hostnames, the tunnel ID, credentials, and service tokens never go in
tracked files.

## Steps

The Cloudflare steps need the account owner's login. A `wizard` script can
walk through the dashboard steps.

1. `cloudflared tunnel login`, then `cloudflared tunnel create gokapi-api`.
   Move the credentials JSON into `cloudflared/` with mode 0600.
2. Write `cloudflared/config.yml` from the example.
3. `cloudflared tunnel route dns gokapi-api files-api.<public-domain>`.
4. In Zero Trust, create the service token and the Access application with
   its Service Auth policy.
5. Add the rate-limit rule and the cache bypass rule.
6. `just tunnel-install` and `just tunnel-start`.
7. In Gokapi's API menu on the tailnet, create the limited key for the app.
8. Ship the app changes. Enter the URL, key, and service token in Settings.

## Verification

Run these from a machine outside the tailnet, such as a phone on mobile data:

| Request | Expected |
| --- | --- |
| `curl -i https://files-api.<public-domain>/api/info/version` | 403 from Access |
| The same with both `CF-Access-*` headers and no `apikey` | 401 from Gokapi |
| The same with headers and the app key | 200 with the version |
| `/admin` or `/d?id=x` with both headers | 404 from cloudflared |
| `/api/auth/create` with headers and the app key | 404 from cloudflared |
| App: test connection, list, 100 MB upload, download, delete | All succeed |

Also confirm `ss -ltn` shows no new public listener on this machine.

## Rollback

`just tunnel-stop`, then delete the DNS record and the Access application.
Gokapi and the tailnet route are unaffected.
