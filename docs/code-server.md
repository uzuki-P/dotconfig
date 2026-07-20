# code-server over Tailscale

This setup exposes [code-server](https://coder.com/docs/code-server/latest) —
VS Code in the browser — on a loopback port fronted by Caddy on the Tailscale
interface. It gives a remote VS Code session with full access to the server's
files, integrated terminal, and extension marketplace. Open the editor at
`https://code.<CADDY_TS_BASE_DOMAIN>/`.

code-server runs as a system template unit (`code-server@<user>.service`)
installed by the official installer. The template instance
`code-server@$USER.service` runs as your user and reads its configuration from
`~/.config/code-server/config.yaml`. The live config is a local untracked file
copied from `code-server/config.yaml.example` (see Install).

Access is controlled by the tailnet ACLs or grants and by Caddy binding only to
the Tailscale IP. There is deliberately no code-server password in the default
configuration: traffic is already HTTPS-terminated by Caddy and gated by the
tailnet, and `auth: password` over a non-TLS listener would not protect
credentials. Set `auth: password` in `config.yaml` (see caveat below) if you
want a second factor on top of the tailnet ACL.

## Files

- `code-server/config.yaml.example` — configuration template, stowed to
  `~/.config/code-server/config.yaml.example`. Copy it to the live path before
  first start (see Install).
- Caddy route: `import service code 127.0.0.1:4444` in
  `_home/docker/caddy/Caddyfile`.

Data locations (code-server defaults, per-user under the template instance):

- `~/.config/code-server/config.yaml` — live config (untracked, local).
- `~/.local/share/code-server/` — user data, workspaces, caches.
- `~/.local/share/code-server/extensions/` — installed extensions.

## Install

The live `config.yaml` must exist BEFORE the code-server service starts for the
first time, because the installer auto-runs `systemctl enable --now
code-server@$USER` at the end of install. If the config is missing at that
moment, code-server writes a default (`bind-addr: 127.0.0.1:8080`, `auth:
password`, randomly generated plaintext password) at the path and starts
listening on 8080 — which does not match the Caddy upstream.

From the dotconfig repository, put the template in place first:

```sh
stow .
mkdir -p ~/.config/code-server
cp ~/.config/code-server/config.yaml.example ~/.config/code-server/config.yaml
```

Then install code-server. The default method drops the binary at
`/usr/bin/code-server`, installs the system template unit, and enables +
starts the per-user instance:

```bash
curl -fsSL https://code-server.dev/install.sh | sh
```

Check the service and logs with systemd:

```sh
systemctl status code-server@$USER
journalctl -u code-server@$USER -f
```

Because this is a system service, it starts at boot without `loginctl
enable-linger` — no lingering setup is needed, unlike the `ttyd` user service.

To confirm code-server picked up the copied config:

```sh
ss -tlnp | grep 4444   # should show 127.0.0.1:4444
```

## Extensions

code-server uses the [Open VSX Registry](https://open-vsx.org) by default, not
the Microsoft marketplace. Most popular extensions are published there; search
from the editor's extension panel as usual.

To point code-server at the Microsoft marketplace instead, you need to override
the `product.json` it ships with (typically at
`/usr/lib/code-server/product.json`). Edit it as root and add:

```json
"extensionsGallery": {
  "serviceUrl": "https://marketplace.visualstudio.com/_apis/public/gallery",
  "itemUrl": "https://marketplace.visualstudio.com/items"
}
```

Note that doing so is outside the terms of service for the Microsoft marketplace
when used by non-VS-Code clients; prefer Open VSX unless a specific extension
is missing. The override will be lost on package upgrade — re-apply after
updating code-server.

## Override defaults

Edit the live `~/.config/code-server/config.yaml` (a local, untracked file)
and restart the service:

```sh
sudo systemctl restart code-server@$USER
```

Useful fields:

- `bind-addr:` — host:port to listen on. Keep `127.0.0.1` so Caddy (on the
  Tailscale IP) is the only entry point.
- `auth:` — `none` (default, tailnet ACL is the gate) or `password`.
- `disable-telemetry:` / `disable-update-check:` — privacy knobs.

To pass additional CLI flags not exposed by the YAML (e.g. a custom
`--extensions-dir`), drop in a system unit override:

```sh
sudo systemctl edit code-server@$USER
```

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/code-server --extensions-dir /path/to/extensions
```

Then `sudo systemctl daemon-reload && sudo systemctl restart code-server@$USER`.

## Caveat on `auth: password`

When `auth: password`, code-server generates a random password and writes its
bcrypt hash into `~/.config/code-server/config.yaml` on first start. The live
config is intentionally a local untracked file, so this won't dirty the repo —
just keep the file out of source control.

## Security notes

- Keep `bind-addr` on `127.0.0.1`; do not change it to a public or wildcard
  address. Caddy (on the Tailscale IP) is the only intended entry point.
- Use Tailscale ACLs or grants to restrict which tailnet identities can reach
  Caddy on this device.
- A connected client receives shell access as the local user through the
  integrated terminal, equivalent to the `ttyd` setup.
- If the host is shared, prefer `auth: password` as a second factor (see the
  caveat above).
