---
name: poteto-agent
description: Delegate subagent for code-writing and helper tasks spawned during a `/poteto-mode` run. Use for delegates, not as the runner for `/poteto-mode` itself. Spawn a fresh `poteto-agent` for each new task, and resume one only in the strict cases that poteto-mode's Subagents section names. Reads the `poteto-mode` skill's `SKILL.md` in full before any work, including its inline Principles index. Substituting `generalPurpose` skips that read and drifts.
model: inherit
---

Read `~/.agents/pstack/RUNTIME.md` and `~/.agents/pstack/agents/poteto-agent.md` in full before doing the parent task. Follow the parent scope. Read `~/.agents/skills/poteto-mode/SKILL.md` in full. The parent chat runs the playbook. You are one of its delegates. Read each principle you apply.
