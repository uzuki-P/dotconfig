# Issue tracker: local Markdown

Issues and specs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file. When `triage-labels.md` is configured, use its state strings.
- Triage category is recorded as `Category: bug` or `Category: enhancement`.
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create or update the relevant local Markdown file under `.scratch/<feature-slug>/`, creating the directory if needed. Issue publication means a local file write; it does not post to a remote service.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Triage operations

List issues by reading files under `.scratch/<feature-slug>/issues/`. Read and update `Category:` and `Status:` fields for categorization and state changes. Append triage notes and replies under `## Comments` while preserving earlier entries.

Record a closed or rejected outcome in the local file instead of deleting its history. For a `wontfix` decision, set `Status: wontfix` and append the reason.
