---
name: publish-dev-route
description: Publish and inspect localhost development servers through random private Tailscale HTTPS URLs. Use when a user wants tailnet access to a local dev port, asks for a shareable dev URL, refers to a dev-route URL, or wants the agent to list, resolve, validate, or remove routes managed by the local dev-router service.
---

# Publish Dev Route

Use the installed `dev-route` CLI. Treat its output as the source of truth for
live route IDs, targets, and URLs; do not infer a route from chat history.

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

## Inspect and reference

- Run `dev-route list` before describing currently published routes.
- Run `dev-route resolve <id-or-url>` before tying a route to a project, port,
  or working directory.
- Preserve the full HTTPS URL in chat so it is clickable.
- If the CLI says the router is uninitialized or unavailable, report that
  state. Do not silently edit Caddy, start Podman, or activate services unless
  the user asked for setup or repair.

## Remove

Run `dev-route remove <id-or-url>` only when the user explicitly asks to remove
that route or cleanup is an explicit part of the current task. Report the
removed URL and target.

## Diagnose

- Run `dev-route validate` to check the registry and generated Caddy fragment
  without changing live services.
- The router accepts only loopback HTTP(S) targets with explicit ports.
- Rootful Caddy owns tailnet TLS. The unprivileged CLI loads changes through
  Caddy's loopback admin API and rolls files back when Caddy rejects a change.
- If Caddy restarted without loading the fragment, run `dev-route apply` to
  reconcile the persisted registry.
- Browser verification requires the user's permission before using browser
  automation. CLI validation does not prove another tailnet device can load
  the URL.
