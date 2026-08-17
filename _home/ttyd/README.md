# ttyd → Herdr over Caddy

This setup exposes Herdr through ttyd. ttyd listens on loopback only and
launches `herdr` directly, which starts or attaches to the persistent session;
reconnecting from the browser re-attaches to the same session. Panes still run
the default shell from Herdr's `config.toml` (`fish`).

The terminal is published to the tailnet as the named dev-router route
`herdr` (`dev-route set herdr 7681`), so it is reached at
`https://herdr.<CADDY_TS_BASE_DOMAIN>/` with TLS terminated by Caddy. Caddy
binds only loopback and the Tailscale address, and the tailnet ACLs or grants
restrict which devices may connect.

There is deliberately no ttyd username/password: Basic authentication would
add nothing over Caddy's TLS and tailnet-only binding.

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

The unit removes Herdr's pane environment variables before ttyd starts. The
Herdr process launched by ttyd is therefore treated as an outer launch, so it
does not trigger the nested-launch guard even when the service itself is
managed from inside a Herdr pane. It does not modify the environment of an
existing shell or local Herdr process.

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

The default URL is `https://herdr.<CADDY_TS_BASE_DOMAIN>/`, served by Caddy
from `127.0.0.1:7681`. ttyd is not reachable directly over the Tailscale
interface anymore. If the named route is ever missing, recreate it with
`dev-route set herdr 7681`. The defaults in `~/ttyd/ttyd-run` can be overridden
for the service with a systemd drop-in:

```sh
systemctl --user edit ttyd.service
```

For example:

```ini
[Service]
Environment=TTYD_MAX_CLIENTS=2
```

If you change `TTYD_PORT`, also repoint the named route with
`dev-route set herdr <new-port>`.

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

- Keep the service bound to `lo`; the terminal should only be reachable
  through Caddy's `herdr` route, never through a public or wildcard address.
- Use Tailscale ACLs or grants to restrict which tailnet identities can reach
  this device; Caddy's wildcard listener is the only entry point.
- A connected client receives Herdr, and through it shell access as the local
  user.
- The default maximum client count is one. Override `TTYD_MAX_CLIENTS` only
  when concurrent browser connections are intentional.
