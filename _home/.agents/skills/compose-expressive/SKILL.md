---
name: compose-expressive
description: Build or redesign personal Kotlin Compose apps with Material 3 Expressive, using maintained modules in dotconfig for Android and desktop theme and settings behavior. Use for new Compose UI, settings work, or requested design migrations, not unrelated fixes or automatic rewrites of other stacks.
---

# Compose expressive

Use Material 3 Expressive as the default design direction for the user's personal Compose apps unless the task specifies another direction. Adapt the template patterns to the target's purpose and supported platforms.

## Read the relevant template

Inspect the target project's instructions, UI structure, settings persistence, and dependency configuration first. Read `~/dotconfig/_template/README.md` and only the relevant modules below. These are reusable source examples to adapt, not complete starters or dependencies on another personal project.

| Template | Use it for |
| --- | --- |
| `~/dotconfig/_template/compose/common/` | Settings model, Material 3 Expressive theme, seed colors, and appearance controls |
| `~/dotconfig/_template/compose/android/` | DataStore persistence, wallpaper colors, system bars, and vibration |
| `~/dotconfig/_template/compose/desktop/` | Settings persistence and live system-theme detection |

Replace the example package and adapt the modules to the target's existing storage and UI. Templates do not pin versions. Check compatibility with the target's dependencies before using APIs. Treat templates as read-only during app work unless template changes are requested. If they are unavailable, state the gap and use the target's existing patterns where possible.

## Theme and settings behavior

- For new apps or requested settings redesigns, provide persisted System, Light, and Dark choices. Make changes update the UI without losing navigation, draft input, or other screen state.
- On Android, provide default, wallpaper, and custom seed-color choices where supported. Provide a fallback for unsupported wallpaper colors. Keep system-bar icon contrast consistent with the app's selected theme.
- On desktop, inspect the desktop template implementation for detecting system-theme changes while the app is open. Adapt it to the target's runtime rather than assuming a startup-only theme query follows later changes.
- For Android vibration settings, provide Off, Light, Default, Strong, and Custom choices, including a preview and persisted custom duration. Use the Android template's duration bounds and implementation as the starting point. Make relevant haptic actions respect the selected setting.
- Expose vibration controls only on platforms with a working implementation. For shared Compose code, keep Android APIs in the Android implementation and use platform-specific behavior where needed.
- Reuse the settings grouping and interaction patterns, not unrelated app settings such as spending backups or prayer notifications.

## Expressive UI

Use the target's supported Material 3 Expressive APIs for its theme, motion, typography, shapes, and interactive components. Check its dependencies before adopting a template API. Change dependencies only as needed for the requested work and preserve supported platforms.

Keep the target app's own content and palette. Use theme colors throughout screens, dialogs, navigation, and transitions. Check press states, selected states, text contrast, tap targets, clipping, and alignment. Respect reduced-motion settings where supported. Match layout and input behavior to each target, including desktop keyboard navigation and window resizing.

A reference does not authorize a full rewrite. Apply the patterns to the screens or settings in scope. For a plan-only request, describe the concrete implementation and verification without changing the app.

## Verification and related workflows

Use the target project's existing Just recipes and required checks. For changed theme or settings behavior, check persistence after restart, all theme modes, live system-theme changes, and navigation or input preservation. For vibration work, check Off, presets, and custom preview on an Android device or emulator when available. State when actual hardware vibration could not be verified.

Inspect relevant screens in light and dark modes on the requested platforms. Check navigation transitions for background flashes and verify desktop tray contrast when tray assets change. Report any platform that could not be exercised.

Use `justfile` for requested developer-workflow setup. Run `app-icon` only when the user explicitly invokes that skill. This skill does not itself add build recipes, generate icons, upload artifacts, or install an app.
