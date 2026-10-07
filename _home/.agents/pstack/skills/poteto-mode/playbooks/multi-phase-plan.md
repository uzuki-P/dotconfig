### Multi-phase plan

Use when the user requests a plan for work with dependencies or several independently verifiable units. Planning ends with a reviewable plan. Execute it when the user authorizes implementation.

1. Read project instructions, relevant justfile recipes, and the affected code. Use the installed prototype skill only for questions that need an experiment.
2. Write the goal, scope, dependencies, and acceptance checks. Separate unresolved product decisions from questions the checkout or an experiment can answer.
3. Use one section per unit. Name its allowed files, expected behavior, verification commands, evidence, and completion condition. PRs are delivery units only when requested or established by project conventions.
4. Choose checks that prove the behavior. For UI changes, name the interaction and available browser or simulator. For performance work, define comparable measurements and a failure threshold. Explain checks that do not apply or remain blocked. Do not require ten workers, cloud VMs, screenshots for CLI-only tasks, or a perf benchmark for every change.
5. Name any authorized reviewers and use the active model profile. Size the panel to the uncertainty and runtime capacity. An inherited panel does not imply different model families.
6. State which external actions are already authorized and which need a decision. Do not require commits, ready PRs, merges, recurring tasks, or external messages as part of every plan.
7. Apply technical-writing and unslop. Run `node ~/.agents/pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` and fix missing fields.
8. Return the plan path, dependencies, unresolved decisions, and validation result. Save a handoff when the work spans sessions.

Use this structure and fill each field with concrete commands or evidence.

```markdown
# <Goal>

## Scope
<Requested outcome, affected paths, exclusions, and authorized delivery actions.>

## Units

### <Unit name>
- Depends on: <Other units, or none.>
- Files: <Allowed paths.>
- Outcome: <Observable result.>
- Verify: <Command or interaction, pass condition, and evidence to retain.>

## Open questions
<Unresolved decisions or none.>
```
