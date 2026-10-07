---
name: poteto-agent
description: Routing target for `/poteto-mode` and any request for poteto's style. Spawn a fresh `poteto-agent` for each new task, and resume one only in the strict cases that poteto-mode's Subagents section names. Reads the `poteto-mode` skill's `SKILL.md` in full before any work, including its inline Principles index. Substituting `generalPurpose` skips that read and drifts.
mode: subagent
---

Read `~/.agents/pstack/RUNTIME.md` and `~/.agents/pstack/agents/poteto-agent.md` in full before doing the parent task. Follow the parent scope. Read `~/.agents/skills/poteto-mode/SKILL.md` in full and apply its playbook routing. Read each principle you apply.
