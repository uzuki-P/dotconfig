# Cockpit through Caddy

Cockpit is exposed through a tailnet-only Caddy endpoint:

```text
https://cockpit.<COCKPIT_BASE_DOMAIN>
```

The tracked socket override binds Cockpit to `127.0.0.1:9090`, so port 9090 is
only reachable by Caddy on the same host.

## Install

From this directory, inspect the available commands and install the host files:

```bash
cp .env.example .env
# Set COCKPIT_BASE_DOMAIN in .env.
just
just install
```

The equivalent file-install commands are:

```bash
sudo dnf install cockpit-podman
just render
sudo install -D -m 0644 cockpit.conf /etc/cockpit/cockpit.conf
sudo install -D -m 0644 listen.conf /etc/systemd/system/cockpit.socket.d/listen.conf
sudo systemctl daemon-reload
sudo systemctl restart cockpit.socket
```

Then validate and reload the existing Caddy container:

```bash
just caddy-reload
```

Open `https://cockpit.<COCKPIT_BASE_DOMAIN>` and confirm login and the Podman
page. Only after that succeeds, remove direct access to port 9090:

```bash
just close-direct-firewall
```
