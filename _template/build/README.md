# Build modules

Adapt `justfile.example` into the target's existing justfile. Replace its generic app name, version source, Gradle tasks, and artifact paths with the target's actual configuration. Its literal version demonstrates the variable only. A real recipe must read the project's version source or call an existing staging task that already does so.

Copy the helpers into the target project's `scripts/` directory. The example invokes the shell helpers through Bash and the PowerShell helper through `powershell.exe`, so executable file permissions are optional.

- `build-apk` builds the production release APK, stages it, and uploads the staged copy using the user's installed share helper. Signing configuration stays in the target project and outside the public template.
- `build-appimage` builds and stages the AppImage without installing or uploading it.
- `install` installs the built AppImage under a stable name and registers its launcher icon and desktop entry.
- `update` builds, stages, then installs the staged AppImage. Installation copies through a temporary file and renames it so an existing AppImage's mounted file is not overwritten in place.
- `build-exe` runs only on Windows. It runs `createDistributable` and `packageExe`, stages the installer in `_apk/`, and prints the staged path last.
- `update-exe` runs only on Windows. It calls `build-exe` without piping or capturing its output, picks the newest staged installer for the version from `_apk/`, then `update-installed-exe.ps1` swaps the installed app's files in place. If the app is not installed yet, it runs the staged installer once. A pipe such as `build-exe | Tee-Object` hangs after the build: the Gradle and Kotlin daemons that Gradle starts inherit the pipe and keep it open until they exit.

`stage-artifact` takes an existing artifact, app identifier, version, and output directory. It emits the staged path on stdout. The output name is `<app>-<version>_<dd-mmm_hh-mm>.<extension>`, with an English lowercase month and `.apk`, `.AppImage`, or `.exe`. It keeps the source file.

`install-appimage` takes an existing AppImage, app identifier, display name, and a launcher PNG. Prepare a 512 by 512 PNG in the target's asset pipeline. The helper does not build or resize assets. Its default installation locations are `~/apps` and `${XDG_DATA_HOME:-$HOME/.local/share}`. `APPIMAGE_APPS_DIR` and `APPIMAGE_DATA_DIR` can override these for isolated verification.

`update-installed-exe.ps1` takes the Compose `packageName` and the `createDistributable` output folder. It finds the install through the uninstall entry whose `DisplayName` equals `packageName`, and replaces only `<packageName>.exe`, `app\`, and `runtime\`. It refuses a drive root or a folder without that layout. If the app is running from the install folder, it asks the user to close it instead of killing it. It renames the old items aside first and restores them if the copy fails. `-Version` updates `DisplayVersion` in the uninstall entry, and `-DryRun` prints the plan without changing anything. The target's Gradle `windows {}` block needs a fixed `upgradeUuid`. Its version must stay within Windows Installer's `major.minor.build` limits and increase on every build, for example `<versionBase>.<commit count>`.

Validate adapted recipes with `just --list` and dry runs. Run real builds, uploads, or installation only within the requested task. These modules contain no signing files, personal configuration, service credentials, or built artifacts.
