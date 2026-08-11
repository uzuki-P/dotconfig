# Dev router

This tooling exposes local HTTP development servers through private HTTPS
hostnames on the tailnet. Choose the route lifetime deliberately:

- **Random / ephemeral:** `dev-route publish` creates a `dev-<8 hex>` hostname
  in the dev-router registry.
- **Specific / persistent:** `dev-route set <name> <target>` writes a named
  entry to the same generated registry.

The existing rootful Caddy container remains the only reverse proxy and TLS
listener.

Choose **random** for an ad-hoc share URL. Choose **specific** when a project
needs a known hostname. Both are applied through Caddy's loopback admin API
without reloading the container.

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

## Random routes

Publish a running local server and print its private URL:

```bash
dev-route publish 5173
```

Use `dev-route list`, `dev-route resolve <id-or-url>`, and
`dev-route remove <id-or-url>` to inspect or remove mappings. Use
`dev-route apply` to reconcile persistent mappings after an unusual manual
configuration change. Caddy reloads are graceful and preserve ordinary HTTP
traffic and WebSocket upgrades.

## Specific routes

Use a named route for a stable project address. It is stored in the generated
registry and applied through Caddy's loopback admin API:

```bash
cd ../dev-router
just specific myapp 5173
```

The above creates `https://myapp.<CADDY_TS_BASE_DOMAIN>` pointing to
`http://127.0.0.1:5173`. `just list-named` and `just remove-specific myapp`
inspect and change the generated registry. The command accepts only loopback
HTTP(S) upstreams with explicit ports; use a static Caddyfile route when a
service needs an advanced upstream, redirect, or Caddy matcher.
