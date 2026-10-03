# Verification record

Checked on 2026-10-03 in isolated integration projects. The template directory contains no generated builds or integration-project configuration.

## Compose compilation

- Common and desktop modules compiled with Kotlin 2.4.20, Compose Multiplatform 1.11.0, Material 3 1.9.0-alpha04, MaterialKolor 2.1.0, and coroutines 1.11.0.
- Common and Android modules compiled with Android Gradle Plugin 9.4.1, Kotlin 2.4.20, compile SDK 37, minimum SDK 26, Compose BOM 2026.09.00, Material 3 1.5.0-alpha29, MaterialKolor 2.1.0, DataStore 1.1.7, and Core KTX 1.17.0.

These combinations record successful checks. They are not mandatory versions for target apps. The Android Material 3 version reports a deprecation for the value-based Slider overload. Adapt it to the target's supported API when integrating. This overload currently compiles on both checked platforms.

No UI was launched. Settings persistence, live system-theme switching, and physical vibration still require verification in a target app.

## Build helpers and configuration

Shell syntax checks and Just parsing and dry runs passed. Fixture checks covered staging APK, AppImage, and EXE files, filename format, source preservation, invalid identifiers, paths with spaces, and AppImage replacement while an old file remained open. The generated desktop entry passed `desktop-file-validate`.

No production build, upload, or installation was performed. The AppImage fixture used a temporary installation directory.

Skill metadata, explicit-only app-icon policy, shared skill links, and whitespace checks passed. An isolated Stow simulation proposed no template links. Template content review found no credentials, private keys, signing files, private data, or personal absolute paths. Ignore rules exclude common private and generated files, but future additions still need review.
