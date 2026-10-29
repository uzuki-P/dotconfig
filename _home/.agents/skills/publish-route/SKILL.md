---
name: publish-route
description: Publish and inspect localhost development servers through private Tailscale HTTPS URLs. Defaults to a stable named route for the current project and can pick a free dev port for it. Use when a user wants to run or share a dev server on the tailnet, wants a named or random route for a local dev port, refers to a dev-route URL, or wants the agent to list, resolve, validate, or remove routes managed by the local dev-router service.
---

# Publish Route

Use the installed `dev-route` CLI. Treat CLI output as the source of truth; do
not infer mappings from chat history. Both route types live in the generated
dev-router registry and load through Caddy's loopback admin API; neither edits
Caddyfile.

**Named routes are the default.** Use a random `dev-<hex>` route only when the
request says "random", "share link", or "temporary".

## Read the arguments

- No arguments: named route, name = the current project directory name.
- One word, such as `/publish-route crm-3`: named route with that name.
- A number, such as `/publish-route 5173`: named route for that port, name =
  the project directory name.
- A word and a number: named route with that name and port.
- `random` with or without a port: random route.

`dev-route port` derives the default name the same way: it lowercases the
directory name and turns other characters into hyphens. A name that already
exists keeps its registered port.

## Named route (default)

1. Confirm the development server is intended for private tailnet access.
2. If the dev server is not running yet and starting it is part of the request,
   run `dev-route port [name]`. It prints the URL on stderr and the port on
   stdout. For an existing name it returns the registered port. For a new name
   it picks a free port in 20000-59999 and creates the route. Start the dev
   server on that port, bound to localhost. Prefer a project `dev-share`
   recipe when one exists, since it does both steps.
3. If the dev server is already running on a port the user or project chose,
   run `dev-route set <name> <port-or-url>`. When the name already maps to a
   different port, tell the user before you overwrite it. Use an explicit
   `https://localhost:<port>` target only when the upstream speaks HTTPS.
4. Return the exact HTTPS URL and mention that only tailnet devices can reach it.

Completion criterion: the CLI prints the URL, Caddy accepts the change, and
`dev-route resolve <name>` reports the intended target.

Use a static Caddyfile route only when the service needs a redirect, a
tailnet-address upstream, or a custom matcher.

## Random route

1. Confirm the development server is intended for private tailnet access.
2. Determine its listening port from the request, project output, or a
   read-only listener check. Do not start or restart it unless that is already
   part of the request.
3. Run `dev-route publish <port-or-url>`.
4. Return the exact HTTPS URL and mention that only tailnet devices can reach it.

Completion criterion: the CLI prints a URL, Caddy accepts the updated
configuration, and `dev-route resolve <url>` reports the intended target.

## Inspect and reference

- Run `dev-route list` before describing currently published random routes;
  run `dev-route list-named` for persistent named routes.
- Run `dev-route resolve <id-or-url>` before tying any route to a project,
  port, or working directory.
- Preserve the full HTTPS URL in chat so it is clickable.
- If the CLI says the router is uninitialized or unavailable, report that
  state. Do not silently edit Caddy, start Podman, or activate services unless
  the user asked for setup or repair.

## Remove

Run `dev-route remove <id-or-url>` or `dev-route remove-named <name>` only
when the user explicitly asks to remove that route or cleanup is an explicit
part of the current task. Report the removed URL and target. Removing a named
route applies the generated fragment through Caddy's loopback admin API.

## Diagnose

- Run `dev-route validate` to check random and named registry entries and the
  generated Caddy fragment without changing live services.
- The router accepts only loopback HTTP(S) targets with explicit ports.
- Rootful Caddy owns tailnet TLS. The unprivileged CLI loads changes through
  Caddy's loopback admin API and rolls files back when Caddy rejects a change.
- If Caddy restarted without loading the fragment, run `dev-route apply` to
  reconcile all persistent dev routes.
- Browser verification requires the user's permission before using browser
  automation. CLI validation does not prove another tailnet device can load
  the URL.
