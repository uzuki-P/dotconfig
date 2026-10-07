---
name: handoff
description: Create, update, or resume task handoffs when asked, at major milestones in substantial work, before planned breaks, or when usage or context limits approach.
---

# Task handoffs

Preserve enough verified task state for another thread to continue the work. Routine handoffs do not require quota data.

## When to write

Create or update a handoff when asked, at a major milestone in substantial work, and before a planned break. A milestone is a completed phase with useful results to preserve, such as finishing an investigation, implementing a change, or completing verification. Brief questions and small edits do not need milestone handoffs unless asked or a limit warning appears.

An explicit impending usage or context limit warning requires an immediate handoff before further substantive work. Do not ask permission to write it. If work continues, update the same file at subsequent milestones and before ending the turn.

## Location and reuse

Store handoffs outside repositories at `~/projects/_md/YYYY-MM-DD_HHMMSS-project-task/handoff.md`. Use local time for the folder's creation timestamp and short project and task names. Create the task folder when needed. Reuse it across threads and worktrees, including after a branch or working directory changes. Add other Markdown files only when the task needs them.

Use the task path already established in the conversation or an explicitly supplied handoff. If no path is supplied, inspect matching task folders. Ask when the intended task is ambiguous. Do not assume the newest folder is the right task.

## What to record

Inspect the current checkout before recording Git state. Record unknown or unavailable values as such rather than guessing. For tasks without a repository, mark Git fields as not applicable.

Include:

- The goal, creation and last-updated times with timezone, and task status.
- The repository, main checkout, exact working directory, branch, and last observed commit.
- Uncommitted changes, with task changes distinguished from unrelated changes. A handoff does not preserve uncommitted files after their worktree disappears.
- A checklist of completed and remaining work, key decisions, verification results, and unresolved problems.
- The next concrete action and any user action needed to unblock it.

Keep the file concise and current. Replace stale task state rather than copying conversation logs or creating a dated file for every session. Preserve decisions and verification evidence that still matter. Tell the user the handoff path when creating it or handing work back for later continuation.

## Additional quota triggers

When the runtime exposes a reliable read-only quota tool or explicit quota data, check the active provider and account at the start of substantive work, at major milestones, and before long operations. Discover the actual tool. Provider availability, model availability, and concurrent agent counts do not measure remaining quota.

If an applicable quota window has 15% or less remaining, write the handoff before further substantive work. This is 85% or more used when the provider reports `usedPercent`. Record the provider, applicable window, remaining percentage, observation time, and reset time when available. Tell the user which quota triggered the handoff.

Treat account quota and context capacity separately. Explicit runtime data reporting 15% or less context capacity remaining also triggers a handoff. Never estimate either percentage from message counts or token guesses.

If usage data is unavailable, stale, or ambiguous, state that limitation once and continue with normal milestone handoffs. Missing quota data must never delay them. A limit warning requires a handoff even without a percentage.

## Resume

Read the selected handoff before continuing. Verify its working directory, branch, commit, and uncommitted state against the current checkout. Resolve differences before relying on recorded state, preserve unrelated changes, and update stale facts in the same handoff. Continue from the next concrete action within the user's authorized scope.
