---
name: domain-modeling
description: Keep a project's domain language and design decisions in CONTEXT.md and docs/adr. Use when a domain term is new, vague, or used two ways, when code, API, UI, and docs name one concept differently, when a hard-to-reverse design decision settles, or when asked to create or update CONTEXT.md, CONTEXT-MAP.md, or an ADR.
---

# Domain modeling

Give each domain concept one name, and record the decisions a future reader would question. The glossary is `CONTEXT.md`. Decisions are ADRs in `docs/adr/`. Read both before working in an area. Update them as soon as a term or decision settles.

## Find the files

- A root `CONTEXT-MAP.md` lists several contexts, each with its own `CONTEXT.md` and optional `docs/adr/`. Work in the context the topic belongs to. Ask only when two fit.
- Otherwise use the root `CONTEXT.md` and `docs/adr/`.
- Paths named in the project's `AGENTS.md` or `docs/agents/domain.md` win.
- Create a file only when you have a term or a decision to write.

## Sharpen the language

Raise these as they come up in the conversation, not as a checklist.

- **Conflict.** The user or the code uses a term differently from the glossary. Quote the entry and ask which meaning holds.
- **Overloaded word.** Propose one canonical term. "Account" could mean the User or the Customer.
- **Scenario.** Probe a boundary with a concrete case. "A Lead converts, then the Customer is deleted. What happens to the Lead?"
- **Code check.** When someone states how something works, read the code. Report a contradiction with its file and line, and ask which side is right.
- **Drift.** Code, API, UI copy, or tickets name one concept differently. Record the canonical term and the other names.

Write each resolved term into `CONTEXT.md` right away.

## Glossary entries

Keep the file's existing layout. Three are common: `### Term` headings, `**Term**:` with an `_Avoid_:` line, and a table with an "Aliases to avoid" column. A new file uses the table.

```md
# <Project> glossary

<One or two sentences on what the product is and what it deliberately is not.>

## <Cluster>

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Stage** | The workflow step a Lead or Customer is in. The API calls it `pipeline`. | pipeline, step |
```

- Define what the term is in one to three sentences. Include its allowed states or invariants when they define it.
- Name the code or API identifier when it differs from the term. Leave out file paths, libraries, and how values are computed.
- Choose one term per concept. List the rest as aliases to avoid.
- Include only terms specific to this domain.
- Group terms under headings once clusters appear. Edit or remove a stale entry instead of adding a contradicting one.

## Decision records

Write an ADR only when all three hold:

1. It is costly to reverse.
2. A future reader would wonder why, or would "fix" it.
3. Real alternatives existed and were rejected for stated reasons.

Typical cases are architecture shape, boundaries between contexts or between frontend and backend, technology with lock-in, deliberate deviations from the obvious path, and constraints the code cannot show, such as compliance, a partner contract, or a staging database with real data.

Follow the folder's existing style. Name files `NNNN-slug.md`, one above the highest number present. A new ADR uses this form.

```md
# <The decision, stated as a sentence>

Accepted on YYYY-MM-DD.

## Context
<The forces at play and the alternatives rejected.>

## Decision
<What we do. Number the rules when there are several.>

## Consequences
<What readers and maintainers can now rely on, and what it costs.>
```

A small decision can be a title and one paragraph. Never rewrite an accepted decision. Append a dated note, or write a new ADR and add `Superseded by NNNN.` under the old one's title.

When planned work contradicts an ADR, say so before acting and name the ADR. Ask whether to reopen it.

## Carry terms into code

Use glossary terms in new types, modules, functions, tests, and branch names. When a term has a fixed set of states or a lifecycle, encode it as one structure per `~/.agents/pstack/skills/principle-model-the-domain/SKILL.md`. Flag code names that disagree with the glossary. Rename them only when the task covers it.

## Set up a project

When asked to start domain docs:

1. Draft `CONTEXT.md` from the core types, API fields, and UI labels. Keep the terms a newcomer would misread and those that two layers name differently. Mark inferred definitions and have the user confirm them.
2. If `AGENTS.md` lacks it, add one line. It says to read `CONTEXT.md` and the relevant ADRs before working in an area, and to use the glossary's terms.
3. Write ADRs only for decisions the user confirms.
