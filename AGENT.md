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
