---
name: t3-shadcn-bootstrap
description: Scaffold a new React Router or TanStack Start shadcn app with the saved T3 Chat design preset and Effect runtime dependency.
disable-model-invocation: true
---

# T3 shadcn bootstrap

Use this skill only when the user explicitly invokes `$t3-shadcn-bootstrap`. It handles a new app scaffold and its initial UI setup. It is not a default instruction for unrelated frontend work.

## Defaults

- Preset: `b3ZNi3IlE8`.
- Template: `react-router`. Use `start` when the user chooses TanStack Start. The shadcn CLI calls this template `start`.
- Base: `base`, so generated components use Base UI primitives like T3 Code.
- Pointer buttons: enabled with `--pointer`.
- Theme: `t3-chat` / T3 Chat, the pink light/dark palette in [references/t3-chat-theme.md](references/t3-chat-theme.md). This is the default among T3 Code's six named themes.
- Icons: keep the preset's Phosphor icon library. Do not migrate icons as part of this skill.
- Runtime packages: `effect` is required as a direct dependency. Add Zod only when the user explicitly requests it.
- Effect source reference: when Effect API examples or deeper verification are needed, consult the local [sandbox Effect clone](</home/uzuki_p/projects/_sandbox/_github/effect/package.json>) without modifying it.
- Do not edit `AGENTS.md` or `CLAUDE.md`.

## Workflow

1. Confirm the target directory and project name. Preserve an existing non-empty project unless the user explicitly requests an in-place setup.

2. Resolve the preset before scaffolding:

   ```bash
   bun x --bun shadcn@latest preset decode b3ZNi3IlE8 --json
   ```

   Expect `mira`, `mauve`, `pink`, `phosphor`, Noto Sans, Geist headings, and a small radius. If the decoded values differ, report the difference before continuing.

3. Scaffold with the selected template:

   ```bash
   bun x --bun shadcn@latest init \
     --preset b3ZNi3IlE8 \
     --template react-router \
     --base base \
     --pointer \
     --name <project-name>
   ```

   Replace `react-router` with `start` for TanStack Start. Keep the preset and base flags the same.

4. Install the required Effect runtime package, then refresh dependencies. Detect the package manager from `package.json` or its lockfile. Add `effect` if it is absent: use `bun add effect`, `pnpm add effect`, or `npm install effect`. After that, run the package manager's install/update flow: for Bun, `bun install` followed by `bun update`; for pnpm, `pnpm install` followed by `pnpm update`; for npm, `npm install` followed by `npm update`. Review the resulting `package.json` and lockfile, then report direct dependency changes.

5. Select and apply the theme. The default is T3 Chat (`t3-chat`): read [references/t3-chat-theme.md](references/t3-chat-theme.md), keep its override in a separate stylesheet loaded after the generated global CSS, and map the T3 roles to shadcn variables. Preserve the distinction between `canvas`, `surface`, `surfaceRaised`, `accentSurface`, and `sidebar`.

   If the user chooses another T3 Code theme, use the six-theme catalog and switching procedure in the reference. Keep the selected Base UI component library, style, fonts, and Phosphor icons unchanged unless the user asks to change them. Apply only the color tokens so existing component code is not rewritten.

6. Check the generated setup:

   ```bash
   bun x --bun shadcn@latest info
   ```

   Confirm that `components.json` uses the selected template's generated configuration, Base UI, and Phosphor. Keep application-specific brand icons separate from the generated UI icons.

7. If the project has a runnable development server, ensure its root has a `justfile`. Preserve existing recipes. For a new project, add a `default` recipe that runs `just --list` and a documented `dev` recipe that runs the project's normal development command.

8. Run the scaffold's available typecheck, lint, and build checks. Check both light and dark tokens for the selected T3 Code theme on representative Button, Card, Input, Dialog, and Sidebar components. Stop if the project does not expose the command needed for a check, and report it.

Completion means the project is scaffolded with the selected template, `effect` is a direct dependency, the dependency refresh is reflected in its manifest and lockfile, the selected T3 Code theme is loaded after the generated CSS, the generated configuration is verified, and the available checks pass.
