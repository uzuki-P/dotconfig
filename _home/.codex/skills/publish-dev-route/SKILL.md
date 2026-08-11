---
name: publish-dev-route
description: Publish and inspect localhost development servers through private Tailscale HTTPS URLs. Use when a user wants a random share URL or a stable named route for a local dev port, refers to a dev-route URL, or wants the agent to list, resolve, validate, or remove routes managed by the local dev-router service.
---

# Publish Dev Route

Use the installed `dev-route` CLI. Choose the route lifetime before changing
anything: both route types are registry-managed. Treat CLI output as the source
of truth; do not infer mappings from chat history.

Use **random** for an ad-hoc share URL. Use **specific** when the requester
names a desired subdomain or wants the route to persist. Both use the generated
dev-router fragment and Caddy's loopback admin API; neither edits Caddyfile.

## Publish

1. Confirm the development server is intended for private tailnet access.
2. Determine its listening port from the request, project output, or a
   read-only listener check. Do not start or restart it unless that is already
   part of the request.
3. Run `dev-route publish <port>`. Use an explicit
   `http://localhost:<port>` or `https://localhost:<port>` target only when the
   upstream scheme differs from plain HTTP.
4. Return the exact HTTPS URL printed by the command and mention that it is
   reachable only from devices with access to the tailnet.

Completion criterion: the CLI prints a URL, Caddy accepts the updated
configuration, and `dev-route resolve <url>` reports the intended target.

## Set a specific route

Use a specific route only when the project needs a stable hostname. It must be
stored in the generated `dev-router` registry:

1. Confirm the target is a loopback HTTP(S) listener with an explicit port.
2. Run `cd ~/docker/dev-router && just specific <name> <port-or-url>`.
3. Return the URL printed by the command and mention that Caddy accepted the
   generated registry change through its loopback admin API.

Completion criterion: the CLI prints the intended URL and `dev-route resolve`
reports the intended named target.

Specific routes accept the same loopback HTTP(S) targets as random routes.
Use a static Caddyfile route only when the service needs a redirect, a
tailnet-address upstream, or a custom matcher.

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
