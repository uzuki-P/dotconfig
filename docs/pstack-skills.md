# Current installation

The active installation is the full upstream pstack at `4dd1d05`, with 34 public skills and 24 private principle references. Agents never post to team chat or change tickets. Unslop is no longer injected into every session. See the 2026-10-30 section at the end. Earlier sections describe the installation history.

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

## Full integration on 2026-10-05

Extended the selected installation to all 26 public skills and 24 private principle references from upstream commit `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`. This supersedes the eight-skill installation scope above. The update follows [pstack's setup guide](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/docs/guide/01-setup.md), with native discovery instead of Cursor's add-plugin command.

### Start a task

Start a fresh agent session after installation.

| Agent | Configure models | Start a task |
| --- | --- | --- |
| Codex | `$setup-pstack` | `$poteto-mode <goal and verification criteria>` |
| Claude Code | `/setup-pstack` | `/poteto-mode <goal and verification criteria>` |
| OpenCode | `/setup-pstack` | `/poteto-mode <goal and verification criteria>` |

For example, ask poteto-mode to add a JSON output flag while preserving the current text output, then verify both. The workflow picks a playbook and reads companion skills as needed. Mode persistence is an instruction within the session, not a Cursor hook.

### Models and reasoning

`~/.agents/pstack/MODELS.json` stores separate profiles for standalone Codex, Claude Code, OpenCode, and T3 Code. Since 2026-11-05, T3 and Claude Code roles are tiered by how cheaply the parent can catch a mistake, all with medium reasoning. `how explorer` runs on Claude Haiku 5.5 (`claude-haiku-5-5` on T3's `claudeAgent`, the `haiku` alias in Claude Code). `feature, refactoring` runs on Claude Sonnet 5.5 (`claude-sonnet-5-5` on T3's `claudeAgent`, the `sonnet` alias in Claude Code). Every other role, including bug-fix, perf, review, design, and verification, stays on Claude Opus 5.5 (`claude-opus-5-5` in T3, the `opus` alias in Claude Code). Interrogate has two Opus reviewers in T3 and three in Claude Code. Architect has three Opus runners. Those panels are independent same-model attempts rather than cross-model evidence. The standalone Codex and OpenCode profiles cannot run Opus natively, so they still inherit the parent model and reasoning settings.

Reasoning budget controls internal reasoning, affects latency and usage, and does not set reply length or a spending limit. Setup offers current settings, medium, high, extra-high, and the model's highest supported level. It stores reasoning separately from model IDs and applies only settings the delegation tool supports. Inheritance aliases retain the session settings. Rerunning setup preserves other runtime profiles and role overrides.

Every skill reads RUNTIME.md and the model profile before using upstream instructions. The compatibility guide overrides Cursor model defaults, tool names, transcript paths, cloud agents, polling, and skill locations. T3 uses its app-owned delegation for cross-provider work, preview tools for browser work, and PR wakeups when exposed. A missing capability remains a reported limitation.

### Maintained files

The shared source remains `_home/.agents/pstack/`. SOURCE.json records the source commit and SHA-256 hashes of upstream skill resources before adaptation. Public links live under `_home/.agents/skills/`. The existing `just sync-skills` recipe installs shared skills across all eight home directories managed by that recipe.

Claude and OpenCode have native poteto-agent and comment-sicko definitions under their tracked agents directories. OpenCode also has 26 command wrappers. Its V2 invocation metadata preserves explicit skill invocation and slash availability. Agent and command files have home links to their tracked sources. Codex passes the shared agent instructions through its native delegation prompts.

Project-local verification skills now use `.agents/skills/` so all three agents can discover them. Setup offers a verification skill for an app only when one is needed. It does not generate one for this dotfiles repository. No recurring job, Cursor plugin, or external MCP was installed.

The pre-update pstack source and global instructions are backed up at `/home/uzuki_p/.local/share/agent-skill-backups/20261005-113026-pstack-full`. Link recovery records are at `/home/uzuki_p/.local/share/agent-skill-backups/1791174831194002319-home-sync`. Preserve subsequent edits when restoring either backup.

### Validation

Codex's app-server skills/list discovered all 26 public skills without load errors. The shared link check passed for 46 total user skills across all eight managed directories. All 50 bundled skill frontmatters passed the skill-creator validator on temporary copies with only Claude's supported disable-model-invocation field omitted, because that validator does not recognize it. The installed files retain it. Checked the four model profiles and 26 OpenCode command definitions. An authenticated private OpenCode v2.0.22 server discovered all 26 pstack skills, all 26 commands, and both native agents after catalog initialization. The existing server returned empty catalogs even for built-ins, so verification used a separate temporary server and did not restart the user-owned process. Start a fresh session to load the installation.

These checks verify installation and discovery. They do not prove every playbook or cross-provider model panel on a real project task. Claude's files have been checked structurally; no paid Claude task was launched for this installation.

The native discovery layout follows [Codex skill documentation](https://developers.openai.com/codex/skills/), [Claude skill documentation](https://code.claude.com/docs/en/skills), and OpenCode V2 documentation for [skills](https://dev.opencode.ai/v2/docs/skills/), [commands](https://dev.opencode.ai/v2/docs/commands/), and [agents](https://dev.opencode.ai/v2/docs/agents/).

## Requested pruning on 2026-10-05

Removed arena, swarm, no-comments, and make-bot-ui from the shared skill source, all eight managed home skill directories, and OpenCode commands. Removed the comment-sicko agent from shared, Claude, and OpenCode definitions because no retained workflow uses it. Removed the three obsolete arena and swarm model roles from every profile. There are now 14 model roles.

Checked dependencies before removal. Architect called arena and linked its instructions from its rationale template. Poteto-mode and its feature, evaluation, orchestration, and shipping preparation playbooks invoked arena, swarm, or no-comments. Blast-radius and figure-it-out also referenced arena. Make-bot-ui had no callers.

Architect now compares design alternatives directly. It delegates designers only when the user requests independent designers. The affected playbooks use native delegation for their existing verification tasks and no longer invoke removed skills. Removed the automatic comment-stripping step. Updated setup, runtime mappings, plan templates, and the plan validator's model label. No removed workflow survives as a private skill dependency.

Matt Pocock's plugin was already disabled in Codex and Claude. Teach and unslop resolve to pstack, and technical-writing is also pstack. No Matt teaching or writing skill was found in active shared skills or Claude's synced skills. The disabled plugin cache remains inactive. Other Matt-derived workflows, including the local Markdown tracker setup, were preserved because they do not conflict with teach or writing.

Recovery files are outside skill discovery at `/home/uzuki_p/.local/share/agent-skill-backups/20261005-163204-pstack-prune`. The shared link synchronizer also recorded removal links at `/home/uzuki_p/.local/share/agent-skill-backups/1791192725199733726-home-sync`.

Pruning checks passed. Codex and a fresh private OpenCode server discover all 22 retained pstack skills and none of the four removed skills. OpenCode discovers the 22 remaining command wrappers and poteto-agent, with comment-sicko absent. All 46 retained skill definitions passed frontmatter validation on temporary copies without the Claude-only invocation field. Shared link validation passed for 42 user skills across eight home directories. Remaining relative resource links and model profiles passed. The plan validator passed its syntax check. No paid workflow execution was performed.

## Poteto help addition

Installed `poteto-help` from upstream revision `df581122cde17e6e27686b5a448bde23e4ad4318` on 2026-10-06. Other workflows retain their existing revisions and local adaptations. SOURCE.json records this supplemental revision and the original file hashes.

Use `$poteto-help` in Codex or `/poteto-help` in Claude Code and OpenCode. The skill stays explicit-only. Its help and prompt examples use the local runtime mappings, MODELS.json, and retained workflows. Removed skills remain absent. The OpenCode command wrapper and shared links follow the existing installation layout.

## Local adaptations and future updates

On 2026-10-07, removed the shared chrome-extensions skill and Poteto's private opening-a-pr playbook. Ordinary tasks now finish with the requested result and verification. PR creation follows project and session instructions when requested. No installed workflow grants permission for unsolicited team messages, ticket changes, or evaluation jobs.

Poteto and companion workflows use RUNTIME.md and the active MODELS.json profile. Missing selections inherit the parent. They do not guess Cursor or Grok defaults. Planning and orchestration use the host's available delegation, browser, history, and scheduler tools. Panels and checks scale to the task. The portable plan checker validates concrete unit fields without requiring ten cloud workers or benchmarks for every change.

Worktree cleanup remains available. The previous helper could treat CLOSED unmerged PRs as safe and missed ignored files. The replacement is read-only and reports tracked, untracked, and ignored entries. It holds locked or known-active worktrees and the main checkout. Activity remains unknown until checked separately. A clean, merged candidate is not deletion approval. For broad cleanup, present exact paths, commit preservation, file disposition, and activity evidence before asking for approval. Existing approval for those exact targets remains valid. New findings need a new disposition decision. No actual worktrees were removed during this skill adaptation.

`just validate-pstack` checks LOCAL_POLICY.json against installed skill resources, agent prompts, and RUNTIME.md. It rejects removed skills and resources, changed or new installed files, and known unsupported model and cloud instructions. `just sync-skills` and `just validate-skills` run this check before inspecting or changing home links. MODELS.json remains user configuration and is excluded from the content baseline. SOURCE.json retains original upstream hashes for provenance. The baseline detects changes, but it cannot prove that new instructions match user intent.

For the next upstream update:

1. Stage a named upstream revision outside the active skill directories. Compare it with the original hashes and revisions in SOURCE.json and the current local files. Do not overwrite the installation directly.
2. Preserve the removals in LOCAL_POLICY.json, local runtime mappings, user model profiles, external-action authorization rules, cleanup safeguards, and ordinary task completion behavior. Adapt tool names and paths to the actual host. Read the changed instructions and scripts before accepting them.
3. Validate frontmatter and referenced resources. Run `python3 -m unittest discover -s _home/.agents/tests -v` and `node --check _home/.agents/pstack/skills/poteto-mode/scripts/check-plan.mjs`. Test changed helpers against isolated fixtures. Do not execute deployment, forge writes, or cleanup merely to test instructions.
4. Update SOURCE.json with the staged revision and its original hashes. After reviewing the adapted files, explicitly update LOCAL_POLICY.json's installedFiles using the validator's installed_files function. Keep the removal lists. Do not accept new hashes just to silence a failure.
5. Run `just validate-pstack`, then `just sync-skills` and `just validate-skills`. Restart discovery only when the host needs it.

The pre-adaptation backup is `/home/uzuki_p/.local/share/agent-skill-backups/20261007-202649-poteto-portable`. The installation retains 23 public pstack skills. Chrome removal leaves 45 shared public skills. The home synchronizer preserves Claude's existing `.trash` recovery archive as a reserved directory.

## Full upstream restore on 2026-10-30

Reinstalled every pstack skill from upstream commit `4dd1d05818d19792e7cd6e818f1667f95f7e1dbe` and dropped the 2026-10-05 pruning and the 2026-10-07 rewrite of poteto-mode. Arena, swarm, no-comments, make-bot-ui, the opening-a-pr playbook, and the comment-sicko agent are back. New since the last install: in-your-own-words, sharpen, ketchup, ketchup-video, statechart, create-formal-verification-skill, and maintain-formal-verification-skill. Interrogate now has adversaries prove each finding with a run, and it calls arena. Orchestrate no longer uses the `orch/` scripts, which upstream deleted.

The installed text is upstream with these local changes:

- Every SKILL.md and agent prompt starts with the RUNTIME.md pointer. Public skills carry the OpenCode metadata and a Codex `agents/openai.yaml` that keeps them explicit-only.
- Every Cursor model slug reads `inherit-parent`. MODELS.json picks the real model. Every profile gains `arena runners`, `arena cross-judge pool`, and `swarm workers`.
- Swarm and Orchestrate run their workers locally, each in its own git worktree, within the three-subagent limit.
- Agents never post to team chat or change tickets. Poteto-mode's Autonomy section and RUNTIME.md say so, and `validate-pstack.py` fails when either rule disappears. Reading those sources as evidence is still allowed. PR descriptions and review-thread replies are part of the PR workflow. Upstream's Benny automations are not installed.
- Opening a PR, babysitting, and shipping follow upstream again. Deploys and data deletion still pause for the user.
- Worktree cleanup keeps the local read-only `worktree-audit.py` and its approval-gated playbook.
- setup-pstack stays native to Codex, Claude Code, OpenCode, and T3. It now lists the arena and swarm roles and offers a formal verification skill.
- poteto-help and poteto-agent point at `~/.agents/skills/` instead of the Cursor plugin cache. Upstream's README and guide pages, without images, are under `~/.agents/pstack/`.

Removed the unslop session hooks from `~/.claude/settings.json` (SessionStart and SubagentStart) and `~/.codex/hooks.json`, and set the zcode hook to `enabled: false`. The script `~/.agents/hooks/unslop-session.sh` and the `unslop` skill remain, so `/unslop` and pstack workflows that cite it still work. The global AGENTS.md no longer lists unslop as a replacement. New sessions pick up the change.

Checks run: `just validate-pstack`, `python3 -m unittest discover -s _home/.agents/tests` (14 tests, including upstream's `check-plan.test.ts` through bun), upstream's watch-pr and check-plan bun suites in a temporary copy (61 pass), frontmatter and relative-link checks for all 58 skills and the agent and command wrappers, then `just sync-skills` and `just validate-skills` (57 skills across 7 home directories). The statechart tests were not run, because they install Java and TLC on first use. No paid workflow run was made.

Backups of the previous pstack tree, shared links, OpenCode commands, AGENTS.md, and the three hook configs are at `/home/uzuki_p/.local/share/agent-skill-backups/20261030-064326-pstack-full-restore`. Link recovery records are at `/home/uzuki_p/.local/share/agent-skill-backups/1793317597287633387-home-sync`.

To update again, stage upstream outside the repo, copy its `skills` and `agents`, then rerun the adaptation steps above. `just validate-pstack` lists every changed file and any slug, cloud, or missing-rule problem. Refresh `LOCAL_POLICY.json` with `installed_files` only after reviewing those files.

## Codex removal and statechart setup on 2026-10-30

Codex is no longer used. MODELS.json drops the `codex` profile and keeps `t3`, `claude`, and `opencode`. RUNTIME.md and setup-pstack no longer offer Codex as a host, and `just sync-skills` no longer manages `~/.codex/skills`. Its existing links were left in place. Outside pstack, Zed's commit-message model moved from `openai-subscribed` to Anthropic `claude-haiku-5-5`, matching T3's text generation model, Zed's `codex-acp` agent server was removed, and T3's two Codex favorites became Claude Sonnet 5.5 and Claude Fable 5.1. T3's codex provider was already disabled.

Statechart's tools are installed with mise: `java@temurin-25` and `http:tla2tools@1.7.4`, the exact versions `run.ts` asks for. They are installed but not added to any mise config, which is how statechart finds them. A run on the upstream MediaPlayer example matched its committed report. The statechart suite passed 367 of 367 tests with `TLA2TOOLS` and `JAVA` set, run in a temporary copy so no `node_modules` landed in this repository.

## Bitbucket pull requests

Agents push over SSH and open Bitbucket PRs, such as capital-crm's, with `_home/.local/bin/bb-pr` (`create`, `view`, `list`, `edit`, `check`). It has no merge, decline or approve command; those stay in the Bitbucket UI.

`bb-pr` authenticates with a scoped Atlassian API token (Bitbucket app passwords are retired). Setup:

1. At https://id.atlassian.com/manage-profile/security/api-tokens choose "Create API token with scopes", app Bitbucket, an expiry of 90 days or less, and only these scopes: `read:user:bitbucket`, `read:repository:bitbucket`, `read:pullrequest:bitbucket`, `write:pullrequest:bitbucket`. Leave out `write:repository` (pushes use SSH), `delete:*` and `admin:*`.
2. Run `secret-tool store --label='Bitbucket API token (bb-pr)' service bb-pr` in your own terminal and paste the token at the hidden prompt. It stays in the login keyring, never in a file or the environment.
3. Write the Atlassian account email to `~/.config/bb-pr/email`.
4. Run `bb-pr check` inside a Bitbucket clone.

The script reads the token at call time and hands it to curl through a file descriptor, so it does not appear in `ps` output or the environment. `~/.claude/settings.json` denies `secret-tool lookup` and `secret-tool search` so agents cannot read the token directly. The token can still act on every repository the account can reach, and `write:pullrequest` allows merging through the raw API, so revoke it at the same Atlassian page if it leaks. To rotate it, create a new token and run step 2 again.

When `bb-pr check` fails, RUNTIME.md tells agents to push the branch and reply with a `pull-requests/new?source=<branch>&dest=<base>` link plus a ready-to-paste title and description, and the user opens the PR.

## Third-party skill updates on 2026-11-03

Compared every installed third-party skill with its upstream. pstack had no changes since `4dd1d05`.

- Updated from upstream: grilling, research, and wizard from `mattpocock/skills` at `4ae2317`, and frontend-design from `anthropics/skills` at `ca45fc4`. Their lock entries now record the new folder hashes.
- diagnosing-bugs gained only upstream's new "Watch it fail" step. Upstream renamed `CONTEXT.md` to `GLOSSARY.md` in diagnosing-bugs, domain-modeling, and triage, but local projects use `CONTEXT.md`, so the rename was not taken. domain-modeling and triage stay at their installed versions.
- setup-matt-pocock-skills and handoff keep their local rewrites. Upstream's setup changes target the GitHub and GitLab trackers the local version removed.
- Removed design-taste-frontend and resolving-merge-conflicts from the source, every home skill directory including the unsynced `~/.codex/skills`, and the installation lock. Upstream had dropped resolving-merge-conflicts. Backups are at `/home/uzuki_p/.local/share/agent-skill-backups/20261103-105130-remove-taste-merge`.
- Refreshed the `RUNTIME.md` hash in `LOCAL_POLICY.json` after reviewing the Bitbucket change from `29619b9`, which had left `just validate-pstack` failing.

`just validate-pstack`, `just validate-skills`, and `just sync-skills` pass with 55 skills across 7 home directories.
