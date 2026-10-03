# Global instructions

## Language

Always respond in English unless the user explicitly asks for another language.

## Worktree safety

Before editing a Git repository, inspect its current status. Preserve unrelated changes and keep edits within the requested scope. Avoid destructive Git commands and broad cleanup operations unless the user names the exact action and target.

## Project commands and conventions

Before choosing commands or proposing workflow changes, read the project's justfile if one exists. Check the repository root and the relevant subdirectory, and follow imports or modules used by the relevant recipes.

Treat recipe comments, command bodies, dependencies, and variables as evidence of the intended workflow. Read the relevant recipe before running it. Prefer existing recipes for development, testing, builds, and deployment unless the user explicitly requests another approach.

When the user's shorthand matches an existing recipe or documented convention, use that meaning. If several interpretations remain, inspect the relevant project files before asking for clarification.

## Folders the user often mentions

### Sandbox folder

`~/projects/_sandbox` holds test projects and some production projects. When the user says "put it on sandbox" or "create a project on sandbox", they mean this parent folder.

Create new work in a uniquely named child directory. Require an exact project target before changing existing work. Do not run recursive deletion, cleanup, or bulk modification against the sandbox root.

### Dotconfig folder

When the user says "dotconfig folder", they mean `~/dotconfig`, their personal dotfiles repository managed with GNU Stow.

### Github folder

`~/projects/_sandbox/_github` holds clones of public repositories for reference. When the user says "github folder", they mean this folder. Inspect these repositories for examples or package source, but do not edit, update, or clean them unless the user explicitly requests it.

### Temp folder

When the user says "temp folder", they mean `~/projects/_temp`, the scratch project for quick chats and throwaway work. Its own AGENTS.md defines the layout for new work there.

## Task handoffs

Store task handoffs outside repositories under `~/projects/_md/YYYY-MM-DD_HHMMSS-project-task/handoff.md`, using local time for the folder's creation timestamp. Create the task folder when needed, reuse it across threads and worktrees, and add other Markdown files only when the task needs them.

Record the goal, creation and last-updated times, task status, repository, main checkout, exact working directory, branch, last observed commit, and uncommitted changes. Include a checklist, key decisions, verification results, unresolved problems, and the next concrete action.

Update the handoff when asked, before a planned break, or at a major milestone. Keep it concise and current rather than copying conversation logs or creating a new dated file for every session.

When resuming, read the explicitly supplied handoff and verify its state against the current checkout before continuing. If no path is supplied, inspect matching task folders and ask when the intended task is ambiguous. Do not assume the newest folder is the right task. A handoff does not preserve uncommitted work after its worktree is removed.

## Capital CRM backend

When working in the `capital-crm` repository or any of its worktrees, "BE" and "backend" refer to `/home/uzuki_p/projects/crmapi/`. Inspect that repository when frontend work depends on backend behavior. Change it only when the user explicitly requests backend changes.

## Development server

Reuse an existing development server when one is available. If verification requires a server and none is reachable, start it only when the command is known and doing so is within the requested task. Do not stop, restart, or replace a user-owned process without permission.

If the server needs credentials, privileged access, or another user-only action, report the exact blocker and ask the user to handle it.

## Personal app conventions

When creating a new personal Kotlin Compose app or redesigning its UI, default to Material 3 Expressive unless I specify another direction. Use the `compose-expressive` skill. Read the maintained reusable modules under `~/dotconfig/_template/compose/` for Android and desktop themes, settings, motion, and supported vibration behavior. Keep changes within the requested scope.

The `app-icon` skill is explicit-only. Run it only when I invoke `$app-icon`, `/app-icon`, or explicitly name that skill. Its workflow bases the design on the app's function and saves a small JPG in the project root for T3 Code. Do not invoke it automatically for a new app or a generic icon request.

Use the `justfile` skill for new-project developer commands and requested workflow changes. It defines the production APK build-and-share convention and the AppImage build, staging, install, and update conventions. Use the maintained examples under `~/dotconfig/_template/build/`. Existing project recipes remain the source of truth.

Shared skill sources live under `~/dotconfig/_home/.agents/skills/` and are linked into the agents' home skill directories with dotconfig's `just sync-skills` recipe.

## Skill replacements

Poteto's `interrogate` replaces the previous `code-review`, and `architect` replaces `codebase-design`. The current `tdd`, `teach`, and `unslop` are Poteto's versions. When older workflows reference the retired names, use these replacements within the user's requested scope.

For these skills and `how`, `why`, or `arena`, read `~/.agents/pstack/RUNTIME.md` before executing the workflow. The installation and Vercel removal are recorded in `~/dotconfig/docs/pstack-skills.md`.
