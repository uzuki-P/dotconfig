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
- For build recipes that produce an APK, AppImage, or EXE, stage a copy in `_apk/` named `<app>-<version>_<dd-mmm_hh-mm>.<extension>`. Use a lowercase month abbreviation and the format's usual extension casing, such as `.apk`, `.AppImage`, or `.exe`. Keep the untimestamped build output in the project's build directory. Use the staged file when reporting or sharing the build.

## APK and desktop release conventions

Apply these defaults when creating a new app's release workflow or when asked to add or revise build recipes. Preserve an existing workflow unless its replacement is requested. Read the target project's justfile and Gradle configuration first. Read `~/dotconfig/_template/build/README.md` and the relevant recipe or helper. Templates require adaptation to the target's task names, package IDs, signing configuration, version source, and artifact paths.

### Android

- Use the `build-apk` example in `~/dotconfig/_template/build/justfile.example` and its `scripts/stage-artifact` helper as the starting point.
- Make `build-apk` build the production release APK, stage the timestamped copy in `_apk/`, then upload that exact copy with `~/docker/files/bin/share`. Read the `share-file` skill for the helper's behavior. Do not read or embed its credentials in a recipe.
- Derive the version and artifact path from the target project's configuration. Keep its existing signing setup. If release signing needs user-provided configuration, report the exact missing input instead of silently producing a debug APK.
- Add `build-apk-dev` only when the project has a separate dev flavor and the requested workflow needs it. Keep its package ID and artifact name distinct from production.

### Linux desktop

- Use `~/dotconfig/_template/build/justfile.example` and the staging and installation helpers under its `scripts/` directory as the starting point. Read only the relevant packaging and installation code.
- Make `build-appimage` build the AppImage and stage the timestamped copy in `_apk/`. Do not upload it by default unless requested or already part of the project's convention.
- Make `install` ensure the AppImage exists, copy it to `~/apps/<app>.AppImage`, and register the desktop entry and icon so launchers can find it by name. Adapt installation paths and desktop metadata to the target app.
- Make `update` perform the full build, staging, and installation flow. Order these operations explicitly and avoid duplicate builds when the packaging tasks already share dependencies.
- Retain other platform recipes. Add EXE or other packaging only for requested targets supported by the project.

Creating recipes does not require running release builds, uploads, or installation to validate them. Execute those operations when requested as part of the task or through a requested recipe.

## Verification

Run `just --list` and `just --dry-run dev` when `dev` exists. Completion means Just parses the file, lists the new recipes, and expands `dev` to the command established by the project.

For added or changed release recipes, also run `just --dry-run <recipe>` for each relevant recipe. Inspect task names, artifact paths, version extraction, filename formatting, dependency order, and upload or install targets. Dry runs verify recipe expansion, not artifact creation. When a real build is requested, verify the staged file and report the upload or installation result only if that operation succeeds.
