---
name: setup-matt-pocock-skills
description: "Configure a repo for local Markdown issue tracking, optional triage states, and domain documentation. Run before using engineering skills that need this repo configuration."
disable-model-invocation: true
---

# Setup Matt Pocock's skills

Configure repository-local Markdown issues and the documentation consumed by the engineering skills. Tracker operations use local files regardless of the repository's Git host. Do not offer remote trackers or use issue-tracker APIs, MCPs, `gh`, or `glab` for this setup.

## Skill dependencies

This setup does not invoke another skill and has no mandatory skill dependency.

- Check whether `triage` is installed to decide whether to generate its state mapping.
- `domain-modeling` consumes the domain documentation conventions. It is not required to run setup.

## 1. Explore

Read the existing repository conventions before choosing paths:

- `AGENTS.md` and `CLAUDE.md`, resolving symlinks, and any existing `## Agent skills` block.
- `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and `docs/agents/triage-labels.md` if present.
- `.scratch/` and any other documented local issue directory.
- `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant ADR directories.
- Whether `triage` is installed.
- Workspace configuration and package directories to distinguish a single-context project from a genuine multi-context repository.

Use `.scratch/<feature-slug>/` by default. Preserve an existing documented tracker directory when it is inside the repository. If existing configuration describes a remote tracker, draft its replacement with the local Markdown convention. Existing remote issues remain outside this setup's scope.

## 2. Prepare the configuration

The tracker choice is fixed to local Markdown. Do not ask the user to choose a provider.

Prepare `docs/agents/issue-tracker.md` from [issue-tracker-local.md](issue-tracker-local.md), adapting the directory paths to the repository's local convention.

If `triage` is installed, prepare `docs/agents/triage-labels.md` from [triage-labels.md](triage-labels.md). Preserve an existing state mapping; otherwise use the default canonical states. Ask only if an existing mapping is ambiguous or the user requests different state names. Without `triage`, omit the triage subsection and new mapping file; preserve any existing file.

Prepare `docs/agents/domain.md` from [domain.md](domain.md). Default to one root `CONTEXT.md` and `docs/adr/`. Preserve an existing multi-context layout; propose one only when repository structure supports it. Missing domain documents are created later as actual concepts and decisions are resolved.

## 3. Show the draft

Present the local tracker path, the generated configuration files, and the `## Agent skills` block. Apply them within the user's authorized setup scope. Resolve any material layout ambiguity with the user before writing the affected configuration.

## 4. Write

Edit the existing repository instruction file. Prefer `CLAUDE.md` when present, otherwise `AGENTS.md`. Resolve a symlink to its source so both harnesses continue sharing the same instructions. If neither exists, ask which instruction file to create.

Update an existing `## Agent skills` block in place and preserve unrelated instructions. Use this structure:

```markdown
## Agent skills

### Issue tracker

Issues live as local Markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage states

Issue state is recorded in local Markdown fields. See `docs/agents/triage-labels.md`.

### Domain docs

Domain terms and decisions use `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
```

Adapt the paths and domain layout to the chosen local conventions. Include the triage subsection only when `triage` is installed. If a previous generated block links to remote-tracker configuration, replace that tracker subsection with the local convention.

Write the prepared configuration files. Keep any existing issue or spec files intact; setup configures their location and conventions rather than creating project work or migrating issue contents.

## 5. Verify and report

Check that the instruction block points to the files actually written and that the tracker configuration describes local file operations. When triage is enabled, verify its state mapping matches the fields documented in the tracker configuration.

Report the configured local directory and changed files. Name only installed consumers of the generated configuration, such as `triage` and `domain-modeling`. Later edits can be made directly in `docs/agents/*.md`.
