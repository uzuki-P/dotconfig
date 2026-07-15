# ttyd over Tailscale

This setup exposes a writable Fish login shell through ttyd on the Tailscale
interface. Open the web terminal and run `herdr` inside that shell. ttyd does
not launch Herdr directly.

Access is controlled by the tailnet ACLs or grants. There is deliberately no
ttyd username/password: Basic authentication over plain HTTP would not encrypt
the credentials or terminal traffic.

## Files

- `~/script/ttyd-run` is the foreground ttyd launcher used by systemd.
- `~/script/ttyd-serve` provides `start`, `stop`, `restart`, `status`, and
  `logs` commands.
- `~/.config/systemd/user/ttyd.service` supervises the launcher.

The unit removes Herdr's pane environment variables only from ttyd and its
children. It does not modify the environment of an existing shell or local
Herdr process. This makes it safe to manage ttyd from inside Herdr: the Fish
shell opened in the browser is treated as an outer terminal, so running
`herdr` there does not trigger the nested-launch guard.

## Install

From the dotconfig repository:

```sh
stow .
stow _home --target="$HOME"
systemctl --user daemon-reload
systemctl --user enable --now ttyd.service
```

Check the service and logs with either systemd or the wrapper:

```sh
ttyd-serve status
ttyd-serve logs
journalctl --user -u ttyd.service -f
```

The default URL is `http://<tailscale-ip>:7681/`. The defaults in
`~/script/ttyd-run` can be overridden for the service with a systemd drop-in:

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
systemctl --user restart ttyd.service
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
