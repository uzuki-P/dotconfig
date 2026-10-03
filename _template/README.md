# Reusable app modules

These are source modules to adapt into a project. They are not complete runnable starters. Keep the target project's dependency versions, package names, storage migration rules, and existing build tasks unless the task calls for changes.

| Directory | Contents |
| --- | --- |
| `compose/common/` | Settings model, Expressive theme, and appearance controls |
| `compose/android/` | DataStore persistence, wallpaper colors, system bars, and haptics |
| `compose/desktop/` | Java Preferences persistence and live system-theme detection |
| `build/` | Just recipe example, artifact staging, and AppImage installation |

## Integration

Copy only the needed modules and rename `example.app` to the target package. In an Android-only app, common and Android files can share its main source set. In a multiplatform app, common files belong in commonMain, Android files in androidMain, and desktop files in the JVM desktop source set.

The Compose modules use Material 3 Expressive, MaterialKolor, and coroutines. Android persistence also needs DataStore Preferences, and system bars need AndroidX Core. Desktop theme detection uses Skiko. Resolve compatible dependencies through the target's build configuration. These modules do not pin dependency versions.

Load settings before rendering the app, collect changes into Compose state, and persist control callbacks through the appropriate store. Wrap the existing navigation tree in the theme without rebuilding or replacing it when settings change. Pass the platform's system-dark value and optional wallpaper color scheme to `ExpressiveAppTheme`. Android uses `isSystemInDarkTheme`; desktop uses `rememberSystemThemeIsDark`.

Use `AppearanceSettings` with wallpaper and vibration controls enabled only on supported Android devices. Its callback emits a settings copy. Connect `onVibrationPreview` to the Android haptics adapter. Desktop can share theme and seed-color settings without displaying unsupported controls.

The build example requires adaptation to the app's actual Gradle tasks, version source, and artifacts. Read `build/README.md` before using it.

## Public content rules

Keep credentials, signing material, local device paths, private endpoints, user data, exports, and generated builds outside this directory. Use runtime configuration or an ignored local file for values a target app needs. Public examples use `example.app` and generic app metadata. Do not copy whole application folders into templates.

The local ignore rules prevent common private and generated files from being added by accident. They do not replace reviewing new content for secrets. Review only template and task-related changes, without printing credentials from unrelated files.

When updating a module, verify it in an isolated integration project with compatible dependencies. Record what was exercised. A syntax check or recipe dry run does not establish that a Compose app builds or that a real device vibrates.
