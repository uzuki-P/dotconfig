# Agent skill changes on 2026-10-01

Installed eight skills from [Poteto's original pstack](https://github.com/cursor/plugins/tree/2eb7ed4613cfc8f098dfe464a23680ea44d84c5e/pstack): interrogate, architect, tdd, teach, unslop, how, why, and arena. The source commit is `2eb7ed4613cfc8f098dfe464a23680ea44d84c5e`.

## Replacements

| Previous skill | Replacement |
| --- | --- |
| code-review | interrogate |
| codebase-design | architect |
| tdd | Poteto's tdd |
| teach | Poteto's teach |
| unslop | Poteto's unslop |

The previous code-review, codebase-design, and tdd were provided by the Matt Pocock plugin. That plugin also contained a teach duplicate. To retire only the replaced workflows, disabled the bundle in Codex and Claude and retained its other workflows as standalone skills. Existing standalone versions remain unchanged. Newly restored standalone skills are ask-matt, improve-codebase-architecture, to-spec, to-tickets, wayfinder, implement, handoff, to-questionnaire.

Other skills, including diagnosing-bugs, domain-modeling, research, prototype, resolving-merge-conflicts, and frontend-design, remain installed.

## Vercel removal

Removed these nine skills and their Claude links: deploy-to-vercel, vercel-cli-with-tokens, vercel-composition-patterns, vercel-optimize, vercel-react-best-practices, vercel-react-native-skills, vercel-react-view-transitions, web-design-guidelines, writing-guidelines. This includes the React, React Native, composition, and transition guidance published under Vercel names, plus both guideline skills from vercel-labs/agent-skills.

No Vercel MCP registration was found in the active global Codex, Claude, or OpenCode configuration or the checked workspace configuration. No remote Vercel resources or project deployments were changed.

## Layout and behavior

The tracked source is `_home/.agents/pstack/`. Shared skill links live in `_home/.agents/skills/`; Claude links point to the shared directory. Codex discovers the shared directory, and OpenCode already has it configured in skills.paths.

The eight upstream workflows are explicitly invoked. This change does not install poteto-mode, automatic routing hooks, or a new MCP. Architect proceeds to implementation unless asked to stop at the design. Interrogate returns review findings without applying fixes. Poteto's teach explains code and design decisions instead of maintaining the previous multi-session teaching workspace. Tdd focuses on a cheap failing regression check.

The upstream workflows use Cursor tool names and model defaults. Each selected SKILL.md points to RUNTIME.md for mappings to the current tools and models. The 23 principle references are bundled privately so the selected workflows can read them without registering additional public skills. Upstream content is otherwise unchanged, and its MIT license is included. SOURCE.json records provenance and source hashes.

## Recovery

Removed active folders and links, plus copies of changed configuration files, are backed up outside skill-discovery directories at `/home/uzuki_p/.local/share/agent-skill-backups/1790854316-poteto`. That backup includes the previous teach and unslop source folders. Restore only the relevant files if reverting this change, since configurations can acquire later edits.

New skills should be available on the next turn or after starting a fresh agent session. Already-running sessions may retain their previous skill catalog until refreshed.

## Verification

Verified all eight shared and Claude skill links, the OpenCode shared-path configuration, TOML and JSON parsing, explicit invocation metadata, source content preservation apart from the runtime pointers, and all 23 bundled principle references. Checked that the disabled plugin's remaining workflows still have standalone skill files and that Vercel skills and lock entries are absent. Compared the changed configuration files with backups to confirm that only the intended plugin enablement fields changed.

These are installation checks. The newly installed workflows have not yet been exercised on a project task, and no claim of cross-model execution has been tested.

## Subsequent user deletions and Claude sync

The user later removed optional workflows from the shared source directory. The remaining 27 user skills were synchronized with Claude, and stale links and installation-lock entries were removed. No deleted skill was restored. See [skill-deletion-audit.md](skill-deletion-audit.md) for the dependency findings and retained optional references.
