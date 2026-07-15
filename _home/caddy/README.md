# Caddy

This directory contains the Caddy reverse proxy deployed on the Tailscale
address `127.0.0.1`. It serves private HTTPS endpoints below
`*.ts.example.com` and uses Cloudflare DNS-01 validation for the wildcard
certificate.

## Files

| File | Purpose |
| --- | --- |
| `Caddyfile` | Host routing and upstream definitions |
| `compose.yaml` | Runs Caddy with host networking and persistent data |
| `Dockerfile` | Builds Caddy with the Cloudflare DNS module |
| `caddy.sh` | Manages the rootful Podman deployment |
| `.env.example` | Documents the required Cloudflare API token |
| `subdomain-access-summary.md` | DNS, access-control, and routing details |

## Setup

Create the local environment file and add a Cloudflare API token scoped to DNS
edits for `example.com`:

```bash
cp .env.example .env
```

Cloudflare must have a DNS-only wildcard A record for `*.ts.example.com`
pointing to `127.0.0.1`. Do not proxy this record through Cloudflare; the
address is reachable only through the tailnet.

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
