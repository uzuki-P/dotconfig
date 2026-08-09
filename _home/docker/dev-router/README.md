# Dev router

This registry exposes local HTTP development servers through random, private
HTTPS hostnames on the tailnet. The existing rootful Caddy container remains
the only reverse proxy and TLS listener.

Route state and the generated `routes.caddy` fragment live in `.data/`, which
is ignored by Git and mounted read-only into Caddy. The unprivileged
`dev-route` CLI asks Caddy's loopback admin API to load changes gracefully, so
publishing does not invoke `sudo` or restart the container.

## Setup

First recreate or update the Caddy container so it receives the new fragment
mount:

```bash
cd ../caddy
just setup
```

That existing rootful helper may request `sudo`. Then initialize and apply the
route registry:

```bash
cd ../dev-router
just setup
```

The setup command reads only `CADDY_TS_BASE_DOMAIN` from the sibling Caddy
`.env`. Caddy's admin endpoint must remain available at `127.0.0.1:2019`.

## Routes

Publish a running local server and print its private URL:

```bash
dev-route publish 5173
```

Use `dev-route list`, `dev-route resolve <id-or-url>`, and
`dev-route remove <id-or-url>` to inspect or remove mappings. Use
`dev-route apply` to reconcile persistent mappings after an unusual manual
configuration change. Caddy reloads are graceful and preserve ordinary HTTP
traffic and WebSocket upgrades.
