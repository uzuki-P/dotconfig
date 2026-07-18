# Repository Guide

This repository stores personal dotfiles managed with GNU Stow.

## Layout

- Top-level packages such as `fish/`, `herdr/`, `nvim/`, and `zed/` are stowed into `~/.config` with `stow .`.
- `_home/` contains files that are stowed directly into `$HOME` with `stow _home --target="$HOME"`.
- `setup.sh` applies both sets of links.

## Editing Rules

- Edit the tracked files in this repository, not the symlinks under `~/.config` or `$HOME`.
- Preserve unrelated local changes; this is a personal, actively edited configuration tree.
- Keep application-specific formatting and comments intact.
- When a color is requested by a Material token such as `pink-300` or `pink-A200`, verify it against the Material Design 2 color palette and use its exact value.
- Do not add generated files, caches, credentials, machine-specific state, or plugin downloads.
- Validate changed configuration with the owning application's checker or reload command when available.
- Do not run `stow --adopt`, `git reset --hard`, or other destructive commands unless explicitly requested.

## Privacy and Secrets

This is a **public** repository. Never leak private information.

- Do not commit real IP addresses, hostnames, domains, emails, usernames, passwords, API keys, tokens, SSH keys, certificates, or any PII / personally identifying data.
- Loopback (`127.0.0.1`, `::1`), link-local, and `example.com` / `example.tld` placeholders are fine.
- Upstream copyright/contact notices already present in third-party scripts (e.g. under `i3/scripts/`) are intentional and must be left as-is; do not introduce new personal identifiers.
- When a configuration needs a sensitive or machine-specific value, read it from an environment variable or a `.env` file and **always provide a sensible default** so the config works on a fresh checkout without leaking anything. Example:
  ```sh
  MY_HOST="${MY_HOST:-127.0.0.1}"
  MY_TOKEN="${MY_TOKEN:-}"
  ```
- Commit only `*.env.example` templates with empty placeholders; add real `.env` files to `.gitignore` (never the values themselves).
- Before committing, scan the diff for secrets: `rg -n '\b(\d{1,3}\.){3}\d{1,3}\b|(?i)(password|secret|token|api[_-]?key)\s*[:=]|@[a-z0-9.-]+\.[a-z]{2,}'` and review any matches. Only loopback addresses and upstream attribution notices should remain.

## Applying Changes

From the repository root:

```sh
stow .
stow _home --target="$HOME"
```

For Herdr configuration changes, reload a running server with:

```sh
herdr server reload-config
```

## Herdr Reference

Before changing or operating Herdr, consult `docs/herdr/README.md`. The pinned upstream documentation is under `docs/herdr/upstream/`, and help output from the installed binary is in `docs/herdr/cli-help.txt`. Prefer the captured CLI help when it differs from general or newer online documentation.

## Caddy Reference

Before changing the Caddy reverse proxy under `_home/docker/caddy/`, consult `_home/docker/caddy/README.md` and `_home/docker/caddy/subdomain-access-summary.md`. Routes are defined through a `(service)` snippet as `import service <name> <upstream>` lines; `<name>` doubles as the matcher label and the subdomain prefix. The bind address and base domain come from `CADDY_TS_IP` and `CADDY_TS_BASE_DOMAIN` (parse-time `{$VAR:default}` placeholders, with safe defaults); never hardcode real IPs or domains in `Caddyfile`. Validate with `./caddy.sh validate` and apply with `./caddy.sh reload` from the caddy directory.
