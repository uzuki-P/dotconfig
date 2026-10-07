---
name: poteto-help
description: Explain pstack setup, task prompts, and skill or playbook selection. Use only when explicitly asked to use poteto-help.
disable-model-invocation: true
metadata:
  opencode/autoinvoke: 'false'
  opencode/slash: 'true'
---

# Poteto help

Read `~/.agents/pstack/RUNTIME.md` and the active profile in `~/.agents/pstack/MODELS.json` before following this workflow. These mappings override upstream Cursor instructions. Use `$skill-name` in Codex examples and `/skill-name` in Claude Code or OpenCode examples. Natural-language requests to use a named skill also work.

Answer the user's question about pstack, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and a pstack run spends real tokens, so let them send the prompt.

A message that asks for work, such as "use pstack to fix this bug", is not a help question. Read [`poteto-mode`](../poteto-mode/SKILL.md), do the work under it, and apply the session persistence described in RUNTIME.md.

This file maps questions to the skills and guide pages that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. Link the installed file when explaining local adaptations. For general upstream guidance, link its public copy under `https://github.com/cursor/plugins/blob/main/pstack/`. Public docs describe Cursor and may differ from this installation.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a PR?", goes straight to its section. If the need is still unclear, ask one short question about whether they need setup, help choosing a workflow, or help with a failed run. Use a structured question when the host supports it.

Check the state that changes the answer, and mention it only when it does:

- Read the active profile in `~/.agents/pstack/MODELS.json`. A missing profile uses inherited roles. Do not infer missing setup from an absent Cursor rule. Existing inheritance is a valid configuration.
- No `verify-*` skill or existing app harness means there may be no scripted way to drive the app. Mention `create-verification-skill` when proving app behavior matters.

If the model profile is missing and the question is about setup or cost, offer once to use `setup-pstack` now or keep inherited settings. Do not ask again when the session already supplies preferences.

## Get set up

This installation uses shared skill links managed by dotconfig's `just sync-skills`, not Cursor's add-plugin command. Read [`setup-pstack`](../setup-pstack/SKILL.md) for configuring the active host's model profile. Start a real task with `poteto-mode`, a goal, and a check that can pass or fail.

For cost questions, explain that subagents and review panels consume extra tokens. Smaller panel lists run fewer independent workers. `inherit-parent` and `auto` use the session's model and settings. A reasoning budget is a preference, not a spend cap. Read the actual profile before describing its choices. Do not recommend upstream model defaults or change settings during a help question.

The [upstream setup guide](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/01-setup.md) describes Cursor. RUNTIME.md and the installed `setup-pstack` workflow define this installation's behavior.

## Start a task with `/poteto-mode`

`/poteto-mode` matches the task to a playbook, copies the playbook's steps into the todo list, and runs the other skills as the steps need them. A step it skips stays in the list as `skip: <reason>`. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](references/prompting.md) before you help word one. [Guide page 2](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/02-poteto-mode.md) has examples.

After an explicit `poteto-mode` invocation, this installation keeps its routing active across turns until the user opts out. Start a new chat with another explicit invocation. Say "new task" to select a fresh playbook within the session. This is a session instruction. It does not install a runtime hook or background job.

Use native delegation or T3 child tasks according to RUNTIME.md. Do not prescribe Cursor `subagent_type` values to other hosts. Same-model reviewers are independent attempts, not evidence from different models.

## Pick a skill

The default answer is `/poteto-mode`, which runs most of the others when its steps need them. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Do any non-trivial task with rigor | [`/poteto-mode`](../poteto-mode/SKILL.md) |
| Know how code works now, or where new code should live | [`/how`](../how/SKILL.md) |
| Know why code is shaped this way, or where a number came from | [`/why`](../why/SKILL.md) |
| Understand a change or subsystem, explained plainly | [`/teach`](../teach/SKILL.md) |
| Catch up on their own recent work on a topic | [`/recall`](../recall/SKILL.md) |
| Know what a small diff could break outside itself | [`/blast-radius`](../blast-radius/SKILL.md) |
| Settle types and module shape before code that crosses a function boundary | [`/architect`](../architect/SKILL.md) |
| Have independent reviewers try to break a diff | [`/interrogate`](../interrogate/SKILL.md) |
| Fix a bug test-first when a cheap local test exists | [`/tdd`](../tdd/SKILL.md) |
| Apply TypeScript rules to `.ts` or `.tsx` work | [`/typescript-best-practices`](../typescript-best-practices/SKILL.md) |
| Clean AI tells out of prose | [`/unslop`](../unslop/SKILL.md) |
| Write docs, an RFC, a README, a PR description, or a commit message to a standard | [`/technical-writing`](../technical-writing/SKILL.md) |
| Hear the last reply again in plain words | [`/bro`](../bro/SKILL.md) |
| Give agents a scripted way to drive the app and prove behavior | [`/create-verification-skill`](../create-verification-skill/SKILL.md) |
| Bring a verification skill and its feature map back in line with the app | [`/maintain-verification-skill`](../maintain-verification-skill/SKILL.md) |
| Vet a performance number before reporting or acting on it | [`/benchmark-checklist`](../benchmark-checklist/SKILL.md) |
| Run a large or cross-cutting change, or one to review after stepping away | [`/figure-it-out`](../figure-it-out/SKILL.md) |
| Keep a decision log during a run, and review it afterward | [`/show-me-your-work`](../show-me-your-work/SKILL.md) |
| Pick a model for each role and a reasoning budget | [`/setup-pstack`](../setup-pstack/SKILL.md) |
| Turn their own working habits into a personal mode skill | [`/automate-me`](../automate-me/SKILL.md) |
| Turn what a finished task taught into skill edits | [`/reflect`](../reflect/SKILL.md) |
| Stop agents from repeating the same mistakes in this repo | [`/correct`](../correct/SKILL.md) |
| Find their way around pstack | `/poteto-help` |

Route only to installed public skills. This installation intentionally removes arena, swarm, no-comments, and make-bot-ui. Do not restore them or recommend them as available workflows. The `principle-*` directories are private references, covered below.

Close calls:

- `/how` explains what the code does. `/why` explains the reasons. `/teach` runs one or both and explains the result plainly.
- Read the installed `/architect` before describing its sequence. It compares alternatives directly and delegates designers only when the user requests them. Add "with checkpoint" to review the design before implementation.
- `/interrogate` reviews the diff. `/blast-radius` looks for breakage outside the diff and proves the one fact that makes the change safe.
- `/recall` rebuilds context across recent chats. Resuming one specific chat or branch is the Session pickup playbook.
- `/figure-it-out` designs one rigorous run. The Orchestrate playbook runs a program that spans days and many PRs. The Autonomous run playbook drives one task to a finish condition.

Runtime-dependent capabilities:

- `deslop`, `control-cli`, and `control-ui` are external Cursor tools. Use the verification and browser mappings in RUNTIME.md instead.
- Map `/loop` to an exposed scheduler only for user-requested recurring work. A normal agent turn does not persist after exit. Use the host's skill authoring tools for skill creation.
- Orchestrate is a `poteto-mode` playbook, not a standalone pstack skill.

## Playbooks and principles

Playbooks are step lists inside `/poteto-mode`, not skills, so they have no slash command. Inside `/poteto-mode`, describing the task picks one, and these phrases name one directly:

- "babysit this pr" or "check on pr 123" runs Babysit. It drives the PR to merge-ready and stops there. It doesn't merge unless the user asks to merge, land, or ship.
- "land the stack" runs Shipping.
- "take over this branch" runs Session pickup.
- "pause safely" runs Pause safely.
- "full autopilot on this queue" runs Autopilot-full. "stack them, don't ship" runs Autopilot-stack.
- "run the eval playbook" runs Eval.

In T3, a request to watch or babysit a PR uses its available watcher and ends the turn so T3 can wake the thread. Follow RUNTIME.md rather than installing a polling loop. The Playbooks section of [`poteto-mode`](../poteto-mode/SKILL.md) lists every playbook and when it applies. [Guide page 6](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/06-verify-and-ship.md) covers opening, babysitting, and landing a PR.

pstack has no standalone planning skill. Use the current host's planning capabilities. For work that spans phases or stacked PRs, asking `/poteto-mode` for a plan runs the [Multi-phase plan playbook](../poteto-mode/playbooks/multi-phase-plan.md), which writes the plan and doesn't implement it. For a design question, the Prototype playbook or `/architect` settles it in code first.

Principles are one-rule skills that `/poteto-mode` reads and cites in its replies. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Read private principle files from `~/.agents/pstack/skills/` when needed. They are not public slash commands in this installation. [Guide page 8](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/08-principles.md) lists them.

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| The mode stopped applying after a few turns | Reinvoke `poteto-mode` and restate the goal. Its session instruction persists until the user opts out, but no runtime hook enforces it. |
| A question got treated as the next step of the last task | Say "new task", or say the turn doesn't need the mode. |
| A new model choice had no effect | Check the active host profile in MODELS.json. Workflows read it on invocation. New skill discovery may need a fresh session. |
| Runs cost more than expected | See the cost paragraph under Get set up. |
| A skill did not load on its own | Check its invocation policy. Explicit-only skills need a named invocation. Start a fresh session if newly installed skills are missing. |
| Parallel agents overwrote each other | Assign separate files or worktrees when parallel work is requested. Do not assume workers have separate machines. |
| An overnight run moved but finished nothing | Define a check that can pass or fail and an exit condition. Persistent runs require a supported scheduler and an explicit recurring-work request. |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers. [Guide page 10](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/10-recipes-and-pitfalls.md) has more pitfalls and the recipes worth copying.

## Make pstack my own

- [`/automate-me`](../automate-me/SKILL.md) drafts a personal mode skill from the user's own history, to use alongside `/poteto-mode`.
- [`/reflect`](../reflect/SKILL.md) after a session turns its lessons into skill edits the user approves.
- `/poteto-mode write a skill for <workflow>` runs the authoring playbook. The eval playbook tests a skill change blind.
- Keep skill fixes within the requested scope. Create a PR only when the user requests one.

[Guide page 9](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/09-make-it-yours.md) covers each of these.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
