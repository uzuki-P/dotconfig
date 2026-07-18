# Subdomain Access and Routing

## Access model

All endpoints in this Caddy instance are private tailnet services:

- Cloudflare provides a DNS-only wildcard record for `*.<CADDY_TS_BASE_DOMAIN>`.
- The record points to the tailnet address `CADDY_TS_IP` (configured in `.env`).
- Caddy binds only to that address, so the endpoints are not reachable from the
  public internet.
- Caddy uses the Cloudflare DNS module and `CLOUDFLARE_API_TOKEN` to complete
  DNS-01 validation and obtain a wildcard TLS certificate.
- Requests for wildcard hostnames that are not explicitly configured return
  HTTP 404.

The actual values are intentionally not committed. See `.env.example` for the
variables and `Caddyfile` for how they are substituted.

## Routes

| Host | Project/service | Upstream |
| --- | --- | --- |
| `t3.<CADDY_TS_BASE_DOMAIN>` | T3 | `127.0.0.1:3773` |
| `ttyd.<CADDY_TS_BASE_DOMAIN>` | ttyd | `<CADDY_TS_IP>:7681` |
| `il.<CADDY_TS_BASE_DOMAIN>` | IssueLane web application | `[::1]:3000` |
| `il-api.<CADDY_TS_BASE_DOMAIN>` | IssueLane API | `127.0.0.1:3220` |
| `il-site.<CADDY_TS_BASE_DOMAIN>` | IssueLane public site | `127.0.0.1:3221` |
| `il-dash.<CADDY_TS_BASE_DOMAIN>` | IssueLane dashboard | `127.0.0.1:6792` |

Because the container uses host networking, loopback upstreams refer to services
running on the host.

## Caddyfile conventions

- Each route is one `import service <name> <upstream>` line. `<name>` becomes both the matcher label (`@<name>`) and the subdomain prefix (`<name>.<CADDY_TS_BASE_DOMAIN>`).
- The `(service)` snippet near the top of `Caddyfile` defines the matcher and `reverse_proxy` handler once. Edit it to change the matcher/handler shape for every route at the same time.
- Env vars use the parse-time form `{$VAR:default}` so the file validates on a fresh checkout without leaking anything:
  - `CADDY_TS_BASE_DOMAIN` (default `ts.example.com`) — base domain for the wildcard cert and every host matcher.
  - `CADDY_TS_IP` (default `127.0.0.1`) — address Caddy binds to, and the host ttyd is reached through.
- `{env.CLOUDFLARE_API_TOKEN}` (runtime form, no default) is read by the Cloudflare DNS plugin when issuing the cert; it must be set in `.env`.
- To add a new env var: declare it in `.env.example` with a safe default (committed) and in `.env` with the real value (gitignored).
- Don't hardcode real IPs or domains in `Caddyfile`; always go through the env placeholders.

## Adding a route

Add one `import service` line inside the `*.{$CADDY_TS_BASE_DOMAIN:ts.example.com}` block, before the final `respond 404`:

```caddyfile
import service myapp 127.0.0.1:8000
```

This expands to a host matcher for `myapp.<CADDY_TS_BASE_DOMAIN>` proxying to `127.0.0.1:8000`. If the upstream is the tailnet node itself rather than loopback, use `{$CADDY_TS_IP:127.0.0.1}:<port>` (see the `ttyd` line). No additional DNS record is needed while the wildcard record remains in place.

After editing, update the Routes table above and run `./caddy.sh validate` then `./caddy.sh reload` (see `README.md`).

## Testing

From a device connected to the tailnet, substitute your configured base domain:

```bash
curl -I https://il.<CADDY_TS_BASE_DOMAIN>
curl -I https://il-api.<CADDY_TS_BASE_DOMAIN>
curl -I https://il-site.<CADDY_TS_BASE_DOMAIN>
curl -I https://il-dash.<CADDY_TS_BASE_DOMAIN>
```

An unconfigured hostname should return 404:

```bash
curl -I https://unknown.<CADDY_TS_BASE_DOMAIN>
```
