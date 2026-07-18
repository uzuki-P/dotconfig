# Caddy

This directory contains the Caddy reverse proxy deployed on a tailnet node. It
serves private HTTPS endpoints below `*.<CADDY_TS_BASE_DOMAIN>` (default
`*.ts.example.com`) and uses Cloudflare DNS-01 validation for the wildcard
certificate. The bind address and base domain come from `.env` so no real
hostnames or IPs are committed.

## Files

| File | Purpose |
| --- | --- |
| `Caddyfile` | Host routing and upstream definitions |
| `compose.yaml` | Runs Caddy with host networking and persistent data |
| `Dockerfile` | Builds Caddy with the Cloudflare DNS module |
| `caddy.sh` | Manages the rootful Podman deployment |
| `.env.example` | Documents the required env vars (Cloudflare token, tailnet IP, base domain) |
| `subdomain-access-summary.md` | DNS, access-control, and routing details |

## Setup

Create the local environment file and fill in the Cloudflare API token, your
Tailscale IP, and the base domain you control:

```bash
cp .env.example .env
```

| Variable | Purpose |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare token with "Edit zone DNS" scope for your zone |
| `CADDY_TS_IP` | Tailnet IP Caddy should bind (and where ttyd is reachable) |
| `CADDY_TS_BASE_DOMAIN` | Base domain under the wildcard cert, e.g. `ts.example.com` |

Cloudflare must have a DNS-only wildcard A record for
`*.<CADDY_TS_BASE_DOMAIN>` pointing at `CADDY_TS_IP`. Do not proxy this record
through Cloudflare; the address is reachable only through the tailnet.

Build and start the rootful Podman service from this directory:

```bash
./caddy.sh setup
```

The helper uses `sudo podman` unless it is already running as root. `setup`
builds the image, starts or updates the container, and validates the active
configuration.

## Validate and reload

After changing only `Caddyfile`, validate and reload Caddy without rebuilding or
restarting the container:

```bash
./caddy.sh reload
```

Other available commands are:

```bash
./caddy.sh validate
./caddy.sh status
./caddy.sh logs
```

Run `./caddy.sh setup` again after changing the Dockerfile, Compose file, or
dependencies.

Do not commit `.env`; it contains the Cloudflare API token.

## Editing the Caddyfile

Routes are defined through the `(service)` snippet — each entry is one
`import service <name> <upstream>` line, and `<name>` doubles as the matcher
label and the subdomain prefix under `<CADDY_TS_BASE_DOMAIN>`. Read
`subdomain-access-summary.md` (especially "Caddyfile conventions" and "Adding
a route") before adding or changing routes. Always run `./caddy.sh validate`
after edits, and never hardcode real IPs or domains — go through the
`CADDY_TS_IP` / `CADDY_TS_BASE_DOMAIN` env placeholders.
