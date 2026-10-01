# User skill sync and deletion audit

Checked on 2026-10-01 after the user removed skills from `_home/.agents/skills`.

All 27 remaining shared user skills now have valid Claude links. Added publish-html and publish-route. Kept Claude's independently synced skill directory unchanged.

Removed ten dangling links from the shared directory and the matching ten Claude links. Removed their ten stale installation-lock entries. No deleted skill was restored.

## Deleted skills

- ask-matt
- handoff
- implement
- improve-codebase-architecture
- t3-shadcn-bootstrap
- to-questionnaire
- to-spec
- to-tickets
- wait-what
- wayfinder
- writing-for-agents

The first audit found dangling links for all listed names except t3-shadcn-bootstrap. That skill's tracked files appear as deletions in Git and no live link remains.

## Dependency findings

No deleted skill is an execution dependency of the remaining user skills. The global AGENTS.md shared by Codex, Claude, and OpenCode does not require any deleted skill. Its Poteto skill replacements and runtime-guide paths all still resolve.

All eight public Poteto skills and their 23 private principle references remain. Architect uses how, why, arena, and interrogate. Teach uses how, why, and unslop. Those companion skills are installed.

Grill-with-docs and triage require grilling and domain-modeling, which remain. Triage's setup dependency remains as setup-matt-pocock-skills.

Setup-matt-pocock-skills contains mentions of removed optional workflows. These are descriptions and reference templates rather than commands that invoke missing skills:

| Reference | Removed name | Meaning |
| --- | --- | --- |
| SKILL.md | to-spec, to-tickets | Examples of consumers of the configured issue tracker |
| domain.md | improve-codebase-architecture | Example of an entry point that could call domain-modeling |
| issue-tracker-local.md | wayfinder | Documentation for its map and ticket layout |
| issue-tracker-github.md | wayfinder | Map and ticket layout, including label names |
| issue-tracker-gitlab.md | wayfinder | Map and ticket layout, including label names |

These references were left unchanged during the deletion audit. The subsequent local Markdown update described below removes them from the setup skill and its templates.

Checked local Markdown links in the remaining skill sources. The only absent targets were illustrative project paths in domain-modeling/CONTEXT-FORMAT.md, such as src/ordering/CONTEXT.md. They are template examples, not missing skill resources.

## Synchronization scope

Claude links point to the current ~/.agents/skills sources rather than copying skill contents. The only Codex-specific user skill is a share-file link to that same source, and OpenCode's harness-specific skill directory is empty. Built-in skills, disabled plugin caches, and Claude's synced package were excluded from the user-skill synchronization.

This audit covers current shared user skill sources and global agent instructions. It does not scan unrelated project repositories for project-specific references to deleted skills.

## Recovery

Installation-lock backup and a record of removed link targets are stored at /home/uzuki_p/.local/share/agent-skill-backups/1790863590-claude-sync. The removed links pointed to paths that were already absent. No skill content was deleted by this synchronization.

## Subsequent local Markdown setup update

Updated setup-matt-pocock-skills to configure only repository-local Markdown issues. Removed the provider-selection branch and the GitHub and GitLab templates. Removed the stale to-spec, to-tickets, wayfinder, and improve-codebase-architecture mentions from its remaining instructions and templates. Local triage uses Category and Status fields.

Setup has no mandatory skill dependency. Triage is detected only to decide whether to generate state settings, and domain-modeling consumes the domain conventions without being invoked by setup. Existing shared and Claude links automatically use the modified source.

Reference links, shared links, invocation metadata, and diff whitespace checks passed. The bundled skill validator does not recognize Claude's retained disable-model-invocation field. Its remaining frontmatter checks passed on a temporary validation copy with only that field omitted. The installed source retains both Claude and Codex explicit invocation settings.

The previous skill files are backed up at /home/uzuki_p/.local/share/agent-skill-backups/1790864134-local-markdown-setup. This change updates the skill definition only; it does not run setup or rewrite any project's existing tracker configuration.
