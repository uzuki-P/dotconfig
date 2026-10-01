# Runtime compatibility for the selected Poteto skills

This installation uses Poteto's original Cursor skills. Apply these runtime mappings before executing their workflows in Codex, Claude Code, or OpenCode. User instructions, repository conventions, and the current runtime's tool contracts take precedence.

- Resolve named installed skills through `~/.agents/skills/<name>/SKILL.md`. Supporting principle references are in `~/.agents/pstack/skills/principle-<name>/SKILL.md`. They are references, not additional registered public skills.
- Map Cursor's Task tool and generalPurpose agents to the runtime's exposed subagent mechanism. Use its actual arguments and concurrency limits. A read-only role means the worker should inspect and report without editing. It does not require a tool mode that prevents access to relevant MCPs.
- Use models the runtime actually exposes. If no role configuration exists, inherit the parent model. Do not assume Cursor's model identifiers work in another runtime. If reviewers share a model, report that limitation rather than describing them as different-model reviewers.
- Discover evidence sources through the current tool catalog or its tool-search mechanism. Use Git for source history and the actual repository host for PRs. Bitbucket repositories require Bitbucket access rather than GitHub CLI commands.
- Reuse the project's justfile recipes and existing development server. Use T3 Code preview tools for browser verification when available. Map todo lists, file reads, search, edits, and shell execution to the current runtime's tools.
- If delegation is unavailable, execute the required investigation or comparison sequentially and report the limitation. An unavailable source is a documented evidence gap. Preserve why's separation between facts and inference.

The eight public skills retain upstream's explicit-invocation setting. Codex metadata also sets `allow_implicit_invocation: false`. Reading a companion skill's instructions for an explicitly requested workflow remains part of that workflow. Global writing instructions can still require unslop.
