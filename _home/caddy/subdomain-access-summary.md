# Subdomain Access and Routing

## Access model

All endpoints in this Caddy instance are private tailnet services:

- Cloudflare provides a DNS-only wildcard record for `*.ts.example.com`.
- The record points to the Tailscale address `127.0.0.1`.
- Caddy binds only to that address, so the endpoints are not reachable from the
  public internet.
- Caddy uses the Cloudflare DNS module and `CLOUDFLARE_API_TOKEN` to complete
  DNS-01 validation and obtain a wildcard TLS certificate.
- Requests for wildcard hostnames that are not explicitly configured return
  HTTP 404.

## Routes

| Host | Project/service | Upstream |
| --- | --- | --- |
| `t3.ts.example.com` | T3 | `127.0.0.1:3773` |
| `ttyd.ts.example.com` | ttyd | `127.0.0.1:7681` |
| `il.ts.example.com` | IssueLane web application | `127.0.0.1:3000` |
| `il-api.ts.example.com` | IssueLane API | `127.0.0.1:3220` |
| `il-site.ts.example.com` | IssueLane public site | `127.0.0.1:3221` |
| `il-dash.ts.example.com` | IssueLane dashboard | `127.0.0.1:6792` |

Because the container uses host networking, loopback upstreams refer to services
running on the host.

## Adding a route

Add a named host matcher and handler before the final `respond 404` directive:

```caddyfile
@service host service.ts.example.com
handle @service {
	reverse_proxy 127.0.0.1:PORT
}
```

No additional DNS record is necessary while the wildcard record remains in
place. Validate and reload Caddy after editing; see `README.md` for commands.

## Testing

From a device connected to the tailnet:

```bash
curl -I https://il.ts.example.com
curl -I https://il-api.ts.example.com
curl -I https://il-site.ts.example.com
curl -I https://il-dash.ts.example.com
```

An unconfigured hostname should return 404:

```bash
curl -I https://unknown.ts.example.com
```
