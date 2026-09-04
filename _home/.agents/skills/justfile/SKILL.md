---
name: justfile
description: Create or update a justfile when scaffolding a new project with a runnable development mode, setting up project developer commands, or explicitly asked to add or edit Just recipes. Do not invoke for ordinary code changes.
---

# Justfile

Create a small project task runner without changing unrelated developer workflows.

## Scope

- For a new project with a runnable local development mode, create a `justfile` in the project root.
- For an existing project, edit its `justfile` only when the user asks for Just changes or developer-workflow setup.
- Treat `package.json`, lockfiles, project documentation, and existing task-runner files as the source of truth for commands.

## Rules

- Preserve existing recipes, the current default recipe, naming, imports, settings, and formatting conventions.
- In a new `justfile`, put a `default` recipe first and make it run `just --list`.
- Add a `dev` recipe when the project has a known development command.
- Give each new recipe a concise one-line doc comment. Do not rewrite old recipes merely to add comments.
- Use the package manager selected by the project's lockfile or configuration.
- If the required command cannot be determined from the project, ask before inventing it.
- Do not start the development server merely to test the recipe.

## Verification

Run `just --list` and `just --dry-run dev` when `dev` exists. Completion means Just parses the file, lists the new recipes, and expands `dev` to the command established by the project.
