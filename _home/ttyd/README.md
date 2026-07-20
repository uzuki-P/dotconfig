# ttyd over Tailscale

This setup exposes a writable Fish login shell through ttyd on the Tailscale
interface. Open the web terminal and run `herdr` inside that shell. ttyd does
not launch Herdr directly.

Access is controlled by the tailnet ACLs or grants. There is deliberately no
ttyd username/password: Basic authentication over plain HTTP would not encrypt
the credentials or terminal traffic.

## Files

- `~/ttyd/ttyd-run` is the foreground ttyd launcher used by systemd.
- `~/ttyd/ttyd-build-index` builds the custom ttyd 1.7.7 browser client into
  `~/.local/share/ttyd/index.html`. It follows the browser's system theme using
  Catppuccin Mocha in dark mode and Latte in light mode, with a Material Pink
  500 cursor. The launcher uses xterm.js's Canvas renderer to avoid WebGL glyph
  atlas corruption in terminal UIs with dense tab decorations. The build also
  pulls in `@xterm/addon-clipboard`, so programs that emit the OSC 52 escape
  sequence (tmux with `set-clipboard on`, neovim with `clipboard=unnamedplus`
  routed through OSC 52, etc.) write into the browser's clipboard and reach the
  client machine. ttyd 1.7.7 does not ship this addon; the build script patches
  it in alongside the theme.
- `~/ttyd/ttyd.service` is the tracked unit; installation links it to
  `~/.config/systemd/user/ttyd.service`.
- `~/ttyd/justfile` provides the build and service-management commands.

The unit removes Herdr's pane environment variables only from ttyd and its
children. It does not modify the environment of an existing shell or local
Herdr process. This makes it safe to manage ttyd from inside Herdr: the Fish
shell opened in the browser is treated as an outer terminal, so running
`herdr` there does not trigger the nested-launch guard.

## Install

From the dotconfig repository, expose `_home` and install the unit:

```sh
stow _home --target="$HOME"
cd ~/ttyd
just ttyd-install
```

Build the custom browser client before starting or restarting ttyd:

```bash
cd ~/ttyd
just ttyd-build
```

Check the service and logs with systemd:

```sh
just ttyd-status
just ttyd-logs
```

The default URL is `http://<tailscale-ip>:7681/`. The defaults in
`~/ttyd/ttyd-run` can be overridden for the service with a systemd drop-in:

```sh
systemctl --user edit ttyd.service
```

For example:

```ini
[Service]
Environment=TTYD_PORT=8765
Environment=TTYD_MAX_CLIENTS=2
```

Then apply the change:

```sh
systemctl --user daemon-reload
cd ~/ttyd
just ttyd-restart
```

## Run across logout and reboot

A user service normally runs only while the user manager is active. To start
the user manager at boot and keep it alive after logout, enable lingering:

```sh
loginctl enable-linger "$USER"
```

Disable it later with `loginctl disable-linger "$USER"` if boot-time service
startup is no longer wanted.

## Security notes

- Keep the service bound to `tailscale0`; do not change the interface to a
  public or wildcard address.
- Use Tailscale ACLs or grants to restrict which tailnet identities can reach
  TCP port 7681 on this device.
- A connected client receives shell access as the local user.
- The default maximum client count is one. Override `TTYD_MAX_CLIENTS` only
  when concurrent browser connections are intentional.
