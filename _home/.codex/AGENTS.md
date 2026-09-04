# Global instructions

## Intent boundary

Treat questions, explanations, reviews, diagnoses, recommendations, and status requests as read-only by default. Do not change source files, dependencies, version-control state, or external systems unless the user explicitly requests a change or implementation. Inspection and verification commands remain allowed when they only produce disposable caches or temporary output.

When a request combines investigation and implementation, complete the investigation first and explain the finding before or alongside the change. Authorization in the original request remains valid. Ask again only when the required change would materially exceed that request.

## Worktree safety

Before editing a Git repository, inspect its current status. Preserve unrelated changes and keep edits within the requested scope. Avoid destructive Git commands and broad cleanup operations unless the user names the exact action and target.

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

## Development server

Reuse an existing development server when one is available. If verification requires a server and none is reachable, start it only when the command is known and doing so is within the requested task. Do not stop, restart, or replace a user-owned process without permission.

If the server needs credentials, privileged access, or another user-only action, report the exact blocker and ask the user to handle it.
