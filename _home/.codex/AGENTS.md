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

## Capital CRM backend

When working in the `capital-crm` repository or any of its worktrees, "BE" and "backend" refer to `/home/uzuki_p/projects/crmapi/`. Inspect that repository when frontend work depends on backend behavior. Change it only when the user explicitly requests backend changes.

## Development server

Reuse an existing development server when one is available. If verification requires a server and none is reachable, start it only when the command is known and doing so is within the requested task. Do not stop, restart, or replace a user-owned process without permission.

If the server needs credentials, privileged access, or another user-only action, report the exact blocker and ask the user to handle it.

## Skill replacements

Poteto's `interrogate` replaces the previous `code-review`, and `architect` replaces `codebase-design`. The current `tdd`, `teach`, and `unslop` are Poteto's versions. When older workflows reference the retired names, use these replacements within the user's requested scope.

For these skills and `how`, `why`, or `arena`, read `~/.agents/pstack/RUNTIME.md` before executing the workflow. The installation and Vercel removal are recorded in `~/dotconfig/docs/pstack-skills.md`.
