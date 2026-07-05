# Herdr documentation snapshot

- Herdr version: `0.7.1`
- Documentation last updated: `2026-07-05`
- Upstream release: `v0.7.1`
- Upstream commit: `dbc45f6306bda3eee681d73a14b48ffbb39f3fcc`
- Sources: [herdr.dev](https://herdr.dev/) and [ogulcancelik/herdr](https://github.com/ogulcancelik/herdr)

This directory is a local reference for AI agents working with the Herdr configuration in this repository. The snapshot is pinned to the locally installed Herdr version instead of the moving `master` documentation.

## Contents

- `upstream/`: documentation pages copied from `website/src/content/docs` at the `v0.7.1` tag. These retain their original MDX frontmatter and markup.
- `cli-help.txt`: output from the installed `herdr 0.7.1` binary's top-level and command-group `--help` flags.
- `man-pages.md`: result of checking for local and upstream man pages.

Start with `upstream/index.mdx`, `upstream/concepts.mdx`, and `upstream/cli-reference.mdx`. For exact commands accepted by the installed binary, prefer `cli-help.txt`.

## Refreshing

When Herdr is upgraded, refresh this directory from the matching upstream tag, recapture all `--help` output, and update the version, date, tag, and commit above.
