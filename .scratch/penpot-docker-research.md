# Penpot Docker deployment research

Checked 2026-07-19 against Penpot's current official documentation and the
`main` branch compose file. This note is implementation guidance, not a copied
compose file; re-check the upstream compose before a future upgrade.

## Current upstream stack

The official compose defines these services:

| Service | Current upstream image | Purpose / dependency |
| --- | --- | --- |
| `penpot-frontend` | `penpotapp/frontend:${PENPOT_VERSION:-2.16}` | Nginx frontend and the only host-published Penpot endpoint; depends on backend, exporter, and MCP |
| `penpot-backend` | `penpotapp/backend:${PENPOT_VERSION:-2.16}` | API, database access, assets, sessions, and WebSocket notification producer |
| `penpot-exporter` | `penpotapp/exporter:${PENPOT_VERSION:-2.16}` | Headless-browser export service |
| `penpot-mcp` | `penpotapp/mcp:${PENPOT_VERSION:-2.16}` | Penpot MCP service, enabled by the upstream `enable-mcp` flag |
| `penpot-postgres` | `postgres:15` | Persistent relational data; health checked with `pg_isready` |
| `penpot-valkey` | `valkey/valkey:8.1` | WebSocket coordination and cache; health checked with `valkey-cli ping` |
| `penpot-mailcatch` | `sj26/mailcatcher:latest` | Temporary development SMTP sink and mail UI, not a production mail provider |

Source: [official Penpot compose](https://github.com/penpot/penpot/blob/main/docker/images/docker-compose.yaml).

The application images share `PENPOT_VERSION`; upstream currently falls back to
`2.16`. Penpot recommends controlling the version explicitly rather than
implicitly tracking whatever is newest. For this repo, pinning `PENPOT_VERSION`
in a local `.env` is the reproducible choice. Upgrades should be made in small
increments. Source: [Install with Docker: start and update](https://help.penpot.app/technical-guide/getting-started/docker/).

## Ports, networks, and persistence

- Upstream publishes frontend container port `8080` as host port `9001`.
  Caddy should proxy the frontend only; backend/exporter/MCP remain reachable
  through the private compose network.
- For a host-local Caddy deployment, bind more narrowly as
  `127.0.0.1:9001:8080` rather than upstream's all-interface `9001:8080`. This is
  a local hardening adaptation, not an upstream requirement.
- The upstream mailcatch web UI publishes `1080:1080`. It is optional for local
  testing and should not be exposed publicly. Its SMTP port `1025` is only
  exposed inside the compose network.
- Named volumes are `penpot_postgres_v15` for PostgreSQL and `penpot_assets` for
  uploaded assets. These are the two persistent datasets that require backups.
- Valkey is intentionally memory-only. Upstream sets `maxmemory 128mb` and
  `maxmemory-policy volatile-lfu`; Penpot recommends those defaults for most
  deployments.

Sources: [official Penpot compose](https://github.com/penpot/penpot/blob/main/docker/images/docker-compose.yaml), [recommended Valkey settings](https://help.penpot.app/technical-guide/getting-started/recommended-settings/), and [Docker backup guidance](https://help.penpot.app/technical-guide/getting-started/docker/#backup-penpot).

## Required and security-relevant configuration

Minimum deployment-specific settings:

- `PENPOT_VERSION=2.16` (or another deliberately selected supported release).
- `PENPOT_PUBLIC_URI=https://<public-host>` shared by frontend, backend, and
  exporter. It must exactly match the browser-facing Caddy URL.
- `PENPOT_SECRET_KEY=<random 512-bit/base64-style secret>`. Penpot derives
  sessions and invitation keys from it; leaving it unset/random across restarts
  invalidates sessions and invitations. The official generator is
  `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`.
- PostgreSQL credentials must agree between `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD` and backend `PENPOT_DATABASE_URI`,
  `PENPOT_DATABASE_USERNAME`, `PENPOT_DATABASE_PASSWORD`. The upstream sample's
  `penpot` password must be replaced for a real installation.
- Backend `PENPOT_REDIS_URI=redis://penpot-valkey/0` and exporter equivalent.
- Backend filesystem storage:
  `PENPOT_OBJECTS_STORAGE_BACKEND=fs` and
  `PENPOT_OBJECTS_STORAGE_FS_DIRECTORY=/opt/data/assets`.
- Exporter `PENPOT_INTERNAL_URI=http://penpot-frontend:8080`; upstream explicitly
  recommends leaving this internal URL unchanged.
- Keep upstream body-size settings synchronized:
  `PENPOT_HTTP_SERVER_MAX_BODY_SIZE=367001600`. The compose also retains the
  deprecated `PENPOT_HTTP_SERVER_MAX_MULTIPART_BODY_SIZE` compatibility setting.

Sources: [Penpot configuration](https://help.penpot.app/technical-guide/configuration/) and [official Penpot compose](https://github.com/penpot/penpot/blob/main/docker/images/docker-compose.yaml).

The upstream compose's current flags are:

```text
disable-email-verification enable-smtp enable-prepl-server disable-secure-session-cookies enable-mcp
```

Do not deploy those defaults unchanged behind public HTTPS. The compose itself
warns internet-facing operators to remove `disable-secure-session-cookies` and
`disable-email-verification`. Keep `enable-prepl-server` if administrative
`manage.py` commands are desired. If using the bundled mailcatcher, remember
that its messages are only a temporary/test substitute; production invitations
should use a real SMTP provider. Consider `disable-registration` if open
self-registration is not wanted, then create profiles through `manage.py`.

## Caddy and WebSockets

Penpot strongly recommends HTTPS and documents Caddy as a proxy to the frontend
port:

```caddyfile
penpot.example.com {
    reverse_proxy 127.0.0.1:9001
}
```

In this repository, TLS is already managed by the shared Caddy setup, so the
Penpot service only needs to bind its frontend to the loopback upstream and the
Caddy service map/import should point at `127.0.0.1:9001`.

Penpot uses persistent WebSockets at `/ws/notifications`; MCP also uses
`/mcp/ws`. The official Nginx example explicitly upgrades both paths. The
official Caddy example uses only `reverse_proxy :9001`, meaning no path-specific
Caddy stanza is required: Caddy's reverse proxy performs the WebSocket upgrade.
Preserve the original host and HTTPS scheme by using the standard Caddy reverse
proxy rather than hand-written header overrides.

Source: [Penpot proxy/HTTPS examples, including Caddy and WebSocket paths](https://help.penpot.app/technical-guide/getting-started/docker/#configure-the-proxy-and-https).

## Startup and verification sequence

1. Create the dedicated compose directory and obtain/adapt the current official
   compose file.
2. Generate and store the secret and database password outside tracked files;
   set the public HTTPS URI and pinned Penpot version.
3. Start with `docker compose -p penpot -f compose.yaml up -d` (the official
   filename is `docker-compose.yaml`; a repo-local rename is harmless if every
   helper consistently uses it).
4. Check `docker compose -p penpot -f compose.yaml ps` and follow logs with
   `docker compose -p penpot -f compose.yaml logs -f`.
5. Verify the loopback frontend first at `http://127.0.0.1:9001`, then reload
   Caddy and verify the public HTTPS URL.
6. In browser developer tools, confirm `/ws/notifications` upgrades successfully
   (and `/mcp/ws` if MCP is exercised), not merely that the landing page returns
   HTTP 200.
7. Stop without deleting named volumes using
   `docker compose -p penpot -f compose.yaml down`. Pull and recreate containers
   for an upgrade only after backing up both persistent volumes.

Sources: [Install with Docker](https://help.penpot.app/technical-guide/getting-started/docker/) and [Penpot troubleshooting](https://help.penpot.app/technical-guide/troubleshooting/).
