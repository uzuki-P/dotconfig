# Pstack for Codex, Claude Code, and OpenCode

Read this file before running any pstack workflow. These mappings override the bundled Cursor instructions. User instructions, repository conventions, and the runtime's tool contracts take precedence over both. Invoking a skill authorizes its in-scope workflow and companion skills. It does not authorize unrelated messages, tickets, publication, deployment, deletion, or merges. Apply authorization already given in the session without asking again.

## Skills and files

Public skills resolve through `~/.agents/skills/<name>/SKILL.md`. Principle references resolve through `~/.agents/pstack/skills/principle-<name>/SKILL.md`. Principles remain private references. Read supporting files relative to the real skill directory. Resolve `pstack/skills/...`, `scripts/...`, and `git show origin/main:pstack/...` references against this installation, not the application repository. Use application Git history only for application files.

Codex uses `$setup-pstack` and `$poteto-mode`. Claude Code uses `/setup-pstack` and `/poteto-mode`. OpenCode has command wrappers for every public pstack skill with the same slash names. Natural-language requests to use a named skill also work. Cursor's mode flag is a session convention here. After an explicit poteto-mode invocation, keep applying its routing across turns until the user opts out. No startup hook or background automation is installed.

Use `.agents/skills/` for new project-local skills shared across these runtimes. Discover existing `.claude/skills/`, `.opencode/skills/`, and `.codex/skills/` as appropriate. For new personal skills in this dotconfig installation, write under `~/dotconfig/_home/.agents/skills/` and run `just sync-skills` from dotconfig. Preserve an existing skill's placement. Map Cursor's built-in create-skill to Codex's skill-creator when available, or the current runtime's skill authoring capability. Preserve the requested scope and validate frontmatter and references.

## Models and reasoning

Read `~/.agents/pstack/MODELS.json` whenever a workflow selects a delegate or reviewer. It replaces every pstack-models.mdc rule and hardcoded Cursor model default in the upstream text. Choose profile `t3` when T3 orchestration is available, otherwise `codex`, `claude`, or `opencode` for the current host. Never use another host's profile as a fallback.

The JSON has `version: 1` and a `profiles` object. Each profile has `budget` and `roles`. Role labels match setup-pstack. Scalar roles take one selection. `architect runners` and `interrogate reviewers` take nonempty lists. Runner and reviewer list lengths set the panel size.

`inherit-parent` and `auto` mean omit the explicit model and inherit the current session settings. An absent scalar role also inherits. An absent panel role uses three inherited seats. A selection object has `model` and, for T3, `providerInstanceId`. It may have `options` with the exact settings accepted by that runtime's delegation tool. Do not convert reasoning settings into model-name suffixes.

Budget labels are `inherit`, `small`, `medium`, `large`, and `unlimited`. Their target reasoning levels are unchanged, medium, high, xhigh, and the highest supported level. They are preferences for explicit selections, not spend caps. Only apply an effort or variant that the selected model and tool support. Keep inheritance aliases unchanged. If effort cannot be set per delegate, retain the runtime setting and report that limitation. Never change the main session or global agent configuration just to apply a role budget.

Discover actual models before writing explicit selections. T3 uses orchestrator_capabilities and providers with canRunChildTask enabled. Codex uses its exposed native subagent catalog. Claude uses the actual Agent tool's supported model choices and configured aliases. OpenCode uses its provider/model catalog, such as `opencode models`, and the delegation tool's model controls. Discovery is not a request to make a paid model call. An unavailable or rejected configured selection is a setup mismatch. Report it, use parent inheritance for that seat, and preserve its scope. Never substitute a guessed Cursor model. Same-model panels are independent attempts, not cross-model evidence.

## Delegation

Map Task, generalPurpose, readonly, run_in_background, and wait to the current runtime's exposed mechanisms and concurrency limits. Read-only workers inspect and report without changing files. If delegation is unavailable, run independent investigations sequentially and report that limitation. Preserve separate candidate outputs and facts versus inference.

In T3 Code, use native subagents only when they support the chosen same-provider model. Otherwise use delegate_task with the selected provider instance and model. Cross-provider work uses delegate_task. Retain each taskId and use task_status or task_cancel. A new review round is a new delegate_task call with the original brief, prior findings, responses, and unresolved objections. Use a stable clientRequestId for retries of that round. Child threads are backing storage. Do not launch ordinary top-level threads for delegated work or continue a round by sending to childThreadId.

In standalone Codex, use the native spawn mechanism and include `~/.agents/pstack/agents/poteto-agent.md` as a prompt reference when those roles apply. Do not pass unsupported Cursor subagent_type values. Claude Code and OpenCode have native poteto-agent definitions. Map generalPurpose to the host's general-purpose agent. OpenCode may not expose a per-call model override. Use a supported mechanism or report the inherited-model limitation rather than editing shared agent definitions during concurrent runs. Claude subagents may lack nested delegation. Return that work to the parent instead of inventing a nested capability.

## Verification and external tools

Reuse project justfile recipes and an existing development server. In T3 Code, prefer preview tools. First call preview_status, then preview_open if no automation-capable preview is attached. Use another browser only when T3 preview tools are absent or explicitly unavailable, or the user requests it. Map Cursor control-ui and control-cli to available browser and terminal capabilities or an existing verification harness. Map deslop to a scoped review for unnecessary code and unrequested changes when that external skill is absent. Report missing capabilities when they prevent required proof.

Use the repository's actual forge. GitHub CLI is suitable for GitHub, not Bitbucket. Discover MCP evidence sources from the tool catalog. Missing sources are evidence gaps. Do not install cursor-team-kit or another plugin implicitly. No installed skill grants blanket permission to send messages to others.

For PR work in T3, register every relevant PR with link_pull_request. For a request to watch or babysit, use watch_pull_request when available and end the turn so T3 can wake it. This overrides the upstream polling watcher. Map /loop to an exposed scheduler only when the user requests recurring work. T3 schedule_task requires a structured schedule object. Claude can use its supported scheduling tools. If no scheduler exists, report that persistence is unavailable. Do not claim an ordinary agent turn will keep running after exit.

Bundled poteto-mode scripts are optional helpers. Read the relevant helper and its prerequisites before executing it. Do not run bootstrap.ts as an installation step. It configures project orchestration rather than skill discovery. Worktree cleanup and process cleanup require the exact authorized targets. Never stop a user-owned server or bulk-delete a parent directory as a skill side effect.

## History and audit evidence

Ignore Cursor transcript path formulas. In T3, use current-project thread search/read tools and explicitly supplied handoffs. For standalone runtimes, use a session API or a user-provided workspace-scoped export. Inspect only the current project and requested time range. Do not search all global session stores or pretend their schemas match Cursor JSONL. If a transcript is unavailable, use supplied context and the current checkout, name the gap, and skip transcript-dependent evaluation claims. Never fabricate a transcript ID, citation, or tool-read receipt.
