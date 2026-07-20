# Penpot

This directory runs Penpot with rootless Podman Compose and exposes only its
frontend on `127.0.0.1:9001`. The repo-managed Caddy proxies the private HTTPS
endpoint at `https://penpot.<CADDY_TS_BASE_DOMAIN>`.

The stack follows Penpot's official Docker deployment: frontend, backend,
exporter, MCP server, PostgreSQL 15, and Valkey. Persistent data lives in the
`penpot_postgres_v15` and `penpot_assets` named volumes.

## Setup

Copy the environment template if `.env` does not exist, set the public Caddy
URL, and generate a stable secret key:

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
```

Put the generated value in `PENPOT_SECRET_KEY`, then start the stack:

```bash
just setup
```

From `_home/docker/caddy`, activate the tracked route:

```bash
./caddy.sh reload
```

Open the URL from `PENPOT_PUBLIC_URI` and register the first account. Email is
logged by the backend because this private deployment has no SMTP service.

## Operations

Run `just` to list all commands. Common operations are:

```bash
just status
just logs
just stop
```

`just stop` preserves both named volumes. Back up both volumes before upgrades,
and update `PENPOT_VERSION` in small increments.

## References

- [Penpot: install with Docker](https://help.penpot.app/technical-guide/getting-started/docker/)
- [Penpot configuration](https://help.penpot.app/technical-guide/configuration/)
- [Official Compose file](https://github.com/penpot/penpot/blob/main/docker/images/docker-compose.yaml)
