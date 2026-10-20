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

- Use the `stage-apk` and `build-apk` examples in `~/dotconfig/_template/build/justfile.example` and its `scripts/stage-artifact` helper as the starting point.
- Make `stage-apk` build the production release APK and stage the timestamped copy in `_apk/`. Make `build-apk` depend on `stage-apk`, then upload that exact copy with `~/docker/files/bin/share`. Read the `share-file` skill for the helper's behavior. Do not read or embed its credentials in a recipe.
- Derive the version and artifact path from the target project's configuration. Keep its existing signing setup. The user's apps read an optional git-ignored `keystore.properties` at the repo root and otherwise sign release builds with `~/.android/debug.keystore`, which is the user's intended signing key for sideloaded apps. For any other signing setup that needs user-provided configuration, report the exact missing input.
- Add `build-apk-dev` only when the project has a separate dev flavor and the requested workflow needs it. Keep its package ID and artifact name distinct from production.

### Linux desktop

- Use `~/dotconfig/_template/build/justfile.example` and the staging and installation helpers under its `scripts/` directory as the starting point. Read only the relevant packaging and installation code.
- Make `build-appimage` build the AppImage and stage the timestamped copy in `_apk/`. Do not upload it by default unless requested or already part of the project's convention.
- Make `install` ensure the AppImage exists, copy it to `~/apps/<app>.AppImage`, and register the desktop entry and icon so launchers can find it by name. Adapt installation paths and desktop metadata to the target app.
- Make `update` perform the full build, staging, and installation flow. Order these operations explicitly and avoid duplicate builds when the packaging tasks already share dependencies.
- Retain other platform recipes. Add EXE or other packaging only for requested targets supported by the project.

### Windows desktop

- For a Compose Desktop app that targets `TargetFormat.Exe`, use the `build-exe` and `update-exe` examples in `~/dotconfig/_template/build/justfile.example` and its `scripts/update-installed-exe.ps1` helper. metrolist-desktop and gokapi-android under `~/projects/_sandbox/` are working references.
- Add `set windows-shell` for Windows PowerShell and mark both recipes `[windows]` with a PowerShell `[script]` attribute, so Linux recipes keep `sh`.
- Make `build-exe` run `createDistributable` and `packageExe` together, stage the installer in `_apk/` with the naming rule above, and print the staged path as its last line.
- Make `update-exe` call `build-exe`, find the newest staged installer for the version in `_apk/`, then pass that installer, the Compose `packageName`, the `createDistributable` output folder, and the version to `update-installed-exe.ps1`. The helper swaps files in place when the app is installed and runs the installer once when it is not.
- Never pipe or capture the output of a command that runs Gradle, such as `just build-exe | Tee-Object` or `$(just build-exe)`. The Gradle and Kotlin daemons inherit the pipe and keep it open, so the recipe hangs after the build succeeds. Let the build write to the console and locate its artifact on disk. Capturing a helper that does not start Gradle, such as `stage-artifact`, is fine.
- Check that the Gradle `windows {}` block sets a fixed `upgradeUuid` and that the version increases on every build within Windows Installer's `major.minor.build` limits. Report a missing one instead of inventing it silently.

### Builds on GitHub Actions

GitHub Actions builds the Windows EXE, because this Linux machine cannot, and the release APK. A local poller fetches both. For EXE builds, lyrics-float, metrolist-desktop, gokapi-android, and pray-time under `~/projects/_sandbox/` are working references. For APK builds, spendr-kt and gokapi-android are.

- Add the EXE workflow only for a project with a GitHub remote and working `build-exe` and `update-exe` recipes. AppImage builds stay local.
- Copy `~/dotconfig/_template/build/github/workflows/windows-exe.yml` to the target's `.github/workflows/` and rename its artifact to `<app>-exe`. Keep its `just build-exe` step, full-history checkout, Asia/Jakarta timezone step, 7-day retention, push trigger with `paths-ignore` for docs, manual dispatch, and `concurrency` cancellation.
- Copy `~/dotconfig/_template/build/scripts/ci-exe` unchanged and add the `[linux]` `ci-exe` recipe from `justfile.example`. The script refuses an unpushed HEAD, waits for the push's run or dispatches one, then calls `ci-fetch --run`.
- Add the APK workflow only for an Android project with a GitHub remote and a working `stage-apk` recipe. Copy `~/dotconfig/_template/build/github/workflows/android-apk.yml` and rename its artifact to `<app>-apk`, copy `scripts/ci-apk` unchanged, and add the `[linux]` `ci-apk` recipe. Set the four `ANDROID_*` signing secrets from `~/.android/debug.keystore` as the template README describes. Without them, the workflow fails rather than signing with the runner's own key.
- Add the project's path to `~/dotconfig/_home/.config/ci-fetch/repos`. `ci-fetch.timer` then downloads each successful build of either workflow into `_apk/`, shares it through Gokapi, deletes the GitHub artifact, and sends a desktop notification. Confirm the timer is enabled with `systemctl --user is-active ci-fetch.timer`.
- A private repo spends included Actions minutes on every non-docs push. Tell the user before adding the workflow to one.

Creating recipes does not require running release builds, uploads, or installation to validate them. Execute those operations when requested as part of the task or through a requested recipe.

## Verification

Run `just --list` and `just --dry-run dev` when `dev` exists. Completion means Just parses the file, lists the new recipes, and expands `dev` to the command established by the project.

For added or changed release recipes, also run `just --dry-run <recipe>` for each relevant recipe. Inspect task names, artifact paths, version extraction, filename formatting, dependency order, and upload or install targets. Dry runs verify recipe expansion, not artifact creation. When a real build is requested, verify the staged file and report the upload or installation result only if that operation succeeds.
