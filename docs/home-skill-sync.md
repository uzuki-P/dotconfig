# Home skill synchronization

The source for shared user skills is `_home/.agents/skills/`. On 2026-10-01, moved `chrome-extensions` into this directory and linked its home installation to the repository. Its two instructions that required the deleted `modern-web-guidance` skill now point to official Chrome documentation.

Run `just sync-skills` after adding or removing a source skill. Existing skill edits appear through the links immediately. Run `just validate-skills` to check for drift without writing files. `setup.sh` also runs the synchronization. These commands never download skills.

The synchronization covers these home directories:

- `~/.agents/skills`
- `~/.claude/skills`
- `~/.codex/skills`
- `~/.zcode/skills`
- `~/.hermes/skills`
- `~/.openwiki/skills`
- `~/.config/goose/skills`
- `~/.config/opencode/skills`

Every source skill has a link in every listed directory. The script removes obsolete links owned by this shared installation and prunes installation-lock entries whose skills no longer exist in the source. It refuses to overwrite independent directories or unrecognized links. Move a newly installed standalone skill into the source directory before running synchronization.

Codex's `.system`, Claude's `synced`, bundled application skills such as PostHog's and Gemini's, plugin caches, and Codex memories remain application-managed. Private Poteto principle references remain in `_home/.agents/pstack/skills/`.

## Deleted skill protection

`modern-web-guidance` is absent from the source and the installation lock. Its dangling Claude link was removed. The synchronization explicitly rejects that skill if it reappears in the source. Stow cannot restore it from this checkout because the source has no such entry.

The lock still records `GoogleChrome/modern-web-guidance` as the upstream repository for `chrome-extensions`. That is provenance for the retained extension skill, not an installed skill named `modern-web-guidance`. An explicit future installation from that upstream repository can add skills independently of this synchronization.

## Verification and recovery

Validated all 26 skills across the eight directories, with no dangling user skill links or remaining `modern-web-guidance` link. A second synchronization made no changes. Just parsing and Git whitespace checks passed.

Original extension files and records of changed home links are backed up under `~/.local/share/agent-skill-backups/`. The synchronization writes a recovery record before changing links or pruning lock entries.

A full `_home` Stow dry run reported existing conflicts outside the skill folders. Those files were left untouched. The skill synchronization does not depend on a successful full Stow run.
