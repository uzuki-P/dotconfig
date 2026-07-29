# dotconfig

Personal Fedora dotfiles managed with [GNU Stow](https://www.gnu.org/software/stow/).
The repository contains the configuration currently used for Fish, Neovim,
tmux, terminal emulators, editors, launchers, and several optional local
services. It is not intended to be a universal Fedora installer: review the
files and enable only the tools you use.

## What gets installed

The repository has two Stow targets:

| Source | Target | Purpose |
| --- | --- | --- |
| Top-level directories such as `fish/`, `nvim/`, `tmux/`, and `zed/` | `~/.config/` | Application configuration |
| `_home/` | `~/` | Home-directory files, scripts, and service directories |

`setup.sh` applies both targets. The `_home/docker/`, `_home/cockpit/`, and
`_home/ttyd/` directories contain optional services with their own READMEs and
`justfile`s; the main setup only creates links and does not start them.

## Recommended order on a clean Fedora Workstation

The order matters because `fish/config.fish` initializes Starship, mise,
zoxide, and Carapace, while `fish/conf.d/rustup.fish` loads Rustup's Fish
environment. Install those commands before using this Fish configuration.

### 1. Update Fedora and install the base packages

Run this from the default Bash shell:

```bash
sudo dnf upgrade --refresh
sudo dnf install \
  fish git stow curl gcc make dnf-plugins-core \
  neovim tmux zoxide starship \
  ripgrep fd-find unzip just eza xclip
```

Why `sudo` is used here: DNF writes RPM packages and metadata to system-owned
locations. Apart from enabling/installing the COPR packages below, the
remaining setup is per-user and should not be run with `sudo`.

This setup also uses these third-party Fedora COPR repositories:

```bash
sudo dnf copr enable lihaohong/yazi
sudo dnf copr enable scottames/ghostty
sudo dnf copr enable zeno/scrcpy
sudo dnf install yazi ghostty scrcpy
```

Enabling a COPR writes repository definitions under the system-owned
`/etc/yum.repos.d/`, so these commands also require `sudo`. COPR projects are
community-maintained rather than official Fedora repositories; review their
project pages before enabling them on another machine. The old
`phracek/PyCharm` COPR is present but disabled on the current machine, so it is
intentionally not part of the clean-install steps.

Useful but optional packages depend on which configurations you plan to use:
`alacritty`, `btop`, `i3`, `i3blocks`, `rofi`, `solaar`, and `podman`.
Applications such as Herdr, lazygit, Superfile, Vicinae, code-server, and Zed
may require their upstream installation method when they are not available
from your enabled Fedora repositories.

This guide assumes regular package-based Fedora Workstation. Fedora
Silverblue/Kinoite uses `rpm-ostree`/Toolbox instead of the DNF host workflow.

### 2. Clone the repository

```bash
git clone --recurse-submodules https://github.com/uzuki-P/dotconfig.git ~/dotconfig
cd ~/dotconfig
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

### 3. Install the Fish startup tools

Install these before opening Fish:

1. [Rustup](https://rustup.rs/) — required by
   `fish/conf.d/rustup.fish`.
2. [mise](https://mise.jdx.dev/getting-started.html) — required by
   `mise activate fish`.
3. [Carapace](https://carapace-sh.github.io/carapace-bin/install.html) —
   required by `carapace _carapace`.

Rustup's standard installer can be run from Bash:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Use the official mise and Carapace instructions for their current Fedora
installation methods. Confirm all startup commands exist before applying the
Fish configuration:

```bash
command -v fish starship mise zoxide carapace
test -f "$HOME/.cargo/env.fish"
```

If you intentionally do not want one of these tools, comment out its matching
initialization line in `fish/config.fish`. For Rustup, comment out:

```fish
source ~/.config/fish/conf.d/rustup.fish
```

Do that before starting Fish; otherwise a clean install will print an error for
the missing command or file.

### 4. Check for Stow conflicts

Do not use `stow --adopt` followed by `git reset --hard`. `--adopt` moves
existing files into this repository, and a hard reset can then permanently
discard them.

Preview both operations first:

```bash
cd ~/dotconfig
stow --no --verbose .
stow --no --verbose _home --target="$HOME"
```

If Stow reports a conflict, compare the existing target with the tracked file,
then move the existing file to a backup directory. For example:

```bash
mkdir -p ~/dotconfig-backup
mv ~/.config/fish/config.fish ~/dotconfig-backup/config.fish
```

Repeat the dry run until the output is clean.

### 5. Apply the links

```bash
cd ~/dotconfig
./setup.sh
```

The equivalent manual commands are:

```bash
stow .
stow _home --target="$HOME"
```

Run `just` in the repository root to list repository-level maintenance
commands.

### 6. Verify Fish

Start a temporary Fish session first:

```bash
fish
```

Check that a prompt appears without startup errors, exercise the commands you
normally use, then return to Bash:

```bash
exit
```

Keeping Bash as the login shell and starting Fish manually is the safest
default. It leaves a known-good shell available if a Fish startup file becomes
invalid, repeatedly starts another Fish process, or otherwise enters a startup
loop.

Making Fish the login shell is entirely optional. Only do it after several
successful test sessions:

```bash
chsh -s "$(command -v fish)"
```

Log out and back in for that change to take effect. If Fish later fails during
startup, open a TTY or another terminal using Bash and restore Bash as the
login shell:

```bash
bash --noprofile --norc
chsh -s /bin/bash
```

Avoid placing unconditional `fish`, `exec fish`, or `source
~/.config/fish/config.fish` commands in Fish startup files. Those can restart
or recursively source the shell configuration. Fish automatically loads files
under `~/.config/fish/conf.d/`. This repository also sources its three `conf.d`
files explicitly from `config.fish`, which can make them run twice but does not
recursively source `config.fish`; do not add further manual sources or any
self-source.

## Fish configuration after a clean install

The baseline configuration does **not** require uncommenting any optional PATH
line. Install the startup tools in step 3 and leave optional lines commented
until their corresponding SDK or version manager is installed.

The relevant files are:

- `fish/config.fish` — prompt/tool initialization and shell functions.
- `fish/conf.d/abbr.fish` — interactive abbreviations.
- `fish/conf.d/paths.fish` — PATH entries and development environment
  variables.
- `fish/conf.d/rustup.fish` — Rustup environment.

After installing an optional tool, uncomment only the matching lines:

| Tool/workflow | Lines to enable |
| --- | --- |
| FNM-managed Node.js | `fnm env --use-on-cd --shell fish \| source` in `fish/config.fish` |
| Puro-managed Flutter | `~/.puro/bin`, `~/.puro/shared/pub_cache/bin`, `~/.puro/envs/default/flutter/bin`, `PURO_ROOT`, and `PUB_CACHE` in `fish/conf.d/paths.fish` |
| Manually installed Flutter SDK | `~/sdk/flutter/bin`; do not also enable the Puro Flutter path |
| Shorebird | `~/.shorebird/bin` |
| Dart global executables without Puro | `~/.pub-cache/bin` |
| Composer global executables | `~/.config/composer/vendor/bin` |
| Maestro | `~/.maestro/bin` |
| A manually unpacked scrcpy | `~/apps/scrcpy` |
| OpenCode | `~/.opencode/bin` |
| Boot.dev's Go installation | `~/.local/opt/go/bin` |
| A fixed Java installation | the one `JAVA_HOME` line matching the installed JDK; never enable two |

Notes:

- Do not uncomment `~/.local/share/mise/shims` when
  `mise activate fish | source` is enabled; activation already manages mise's
  shell integration.
- The repository currently enables Bun's and FNM's install directories in
  `PATH`, but that is harmless when those directories do not exist. The FNM
  initialization itself remains optional.
- `PNPM_HOME` in `fish/config.fish` is machine-specific. On a machine whose
  username differs from the repository owner's, replace its absolute path with
  your own home path before using pnpm.
- Android paths are enabled by default and expect the SDK at
  `~/Android/Sdk`. Install Android Studio/command-line tools there, or adjust
  `ANDROID_HOME`, `ANDROID_SDK`, and `ANDROID_SDK_ROOT`.
- The `SSH_AUTH_SOCK` setting expects a user SSH agent at
  `$XDG_RUNTIME_DIR/ssh-agent.socket`. Comment it out if your desktop/session
  manages SSH authentication differently.

## Optional development tooling

### Flutter with Puro

Install [Puro](https://puro.dev/) first, then create/select the environment you
want using its current documentation. Once the environment exists, enable the
Puro lines listed in the Fish table above and restart Fish:

```fish
exec fish
```

### Java

Install the JDK version required by the project you are working on, then select
it with Fedora's alternatives system if applicable:

```bash
sudo alternatives --config java
```

Only set `JAVA_HOME` in `fish/conf.d/paths.fish` when a tool specifically needs
it, and make sure the path matches the installed JDK.

### Yazi sudo plugin

The repository includes the `sudo.yazi` plugin files. To refresh it from
upstream when needed:

```bash
ya pack -a TD-Sky/sudo
```

## Repository-specific documentation

- `nvim/README.md` — Neovim configuration notes.
- `docs/code-server.md` — code-server setup and recovery.
- `docs/herdr/README.md` — pinned Herdr reference.
- `_home/docker/*/README.md` — local Podman Compose stacks.
- `_home/cockpit/README.md` — Cockpit configuration.
- `_home/ttyd/README.md` — ttyd user service.

Each optional service directory has a `justfile`; run `just` inside that
directory to list its commands before applying changes.

## Vial keyboard access

Use `_home/script/register-vial-hid.sh` for the tracked udev-rule workflow.
Review the script before running it: it uses `sudo` because udev rules are
installed under the system-owned `/etc/udev/rules.d/` directory.
