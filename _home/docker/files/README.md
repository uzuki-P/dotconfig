# Private artifact sharing

This directory deploys [Gokapi](https://github.com/Forceu/Gokapi) as a rootless
Podman user service for files produced by local AI agents. Gokapi listens only
at `http://127.0.0.1:53842`; the machine's existing dev-router publishes the
stable private `files` HTTPS hostname through its tailnet-only Caddy listener.

This deliberately adapts the generic `tailscale serve` design to this host.
Do not create a second TLS listener: the existing dev-router is the source of
truth for persistent private subdomains and applies changes through Caddy's
loopback admin API.

## Layout

| Path | Purpose |
| --- | --- |
| `deploy/gokapi.container` | Rootless Podman Quadlet, pinned to Gokapi v2.2.4 |
| `data/` | Uploaded objects and Gokapi data (ignored except `.gitkeep`) |
| `config/` | Generated configuration/database (ignored except `.gitkeep`) |
| `custom/` | Admin UI tweaks loaded through Gokapi's supported customization hook |
| `secrets/api-key` | Local API key used by `bin/share` (ignored) |
| `bin/share` | Upload and deletion helper |

The repository path `_home/docker/files` is installed by this dotfiles repo as
`~/docker/files`. Run service commands from `~/docker/files` after Stow/setup.

## Prerequisites

- Rootless Podman with Quadlet support
- `systemd --user`, `curl`, `jq`, `just`, and `dev-route`
- The existing private dev-router and Caddy service

No rootful Podman command is used for Gokapi. Container root, if shown by
`podman top`, is namespaced to the unprivileged host user; it is not host root.

## Install and first start

Validate and install the Quadlet:

```bash
cd ~/docker/files
just validate
just install
just start
just status
```

The install recipe creates user-owned `data/`, `config/`, and `secrets/`
directories with mode `0700`, copies the Quadlet to
`~/.config/containers/systemd/gokapi.container`, and reloads the user systemd
manager. The `[Install]` section makes it part of the user's default target.
To keep user services running after logout, this machine may need the one-time
host setting `loginctl enable-linger "$USER"`; that is intentionally not run by
the recipes.

Create the requested persistent route after the loopback listener is up:

```bash
cd ~/docker/files
just route
dev-route resolve files
```

`just route` is equivalent to `cd ~/docker/dev-router && just specific files
53842`. It should print the exact private HTTPS URL accepted by Caddy. The URL
is reachable only by devices allowed onto this tailnet; this is not Funnel and
does not expose Gokapi publicly. The local host is also allowed through
loopback for local automation and testing.

The root of that URL is the upload entry point. Caddy redirects `/` to
Gokapi's authenticated `/admin` page, which asks for the `uzuki_p` Gokapi
password before showing the file-select and drag-and-drop upload interface.
After an upload, Gokapi displays the download link and, where supported, the
direct hotlink. Existing `/d` and `/h` links continue to be served by Gokapi.
For files with a hotlink, the admin table shows `Hotlink` before `URL`, and
clicking the file ID opens the hotlink. The original share and email actions
are replaced with `Show QR` after `URL`. Download, edit, and delete remain in
the second button group. Files without a hotlink keep Gokapi's normal
download-page link.

Open the printed URL on a tailnet device and complete `/setup`. Configure:

- the externally visible URL as the exact `https://files.…` route;
- local storage;
- normal Gokapi authentication;
- **end-to-end encryption disabled**.

E2E encryption must remain disabled for previewable direct hotlinks. Server-side
local encryption can still support hotlinks, but E2E/client-side decryption
cannot produce a raw image URL suitable for chat rendering. Gokapi v2.2.4 also
blocks SVG hotlinks for security; share SVG files as ordinary download links.

After setup, create an API key in Gokapi's API menu with only `Upload`, `List
Uploads`, and `Delete Uploads` permissions. `List Uploads` is useful for
inspection; `Upload` and `Delete Uploads` are required by the helper's matching
commands. Copy the key immediately.

## Configure the helper

```bash
cd ~/docker/files
cp .env.example .env
mkdir -p secrets
chmod 700 secrets
printf '%s' 'PASTE_API_KEY_HERE' > secrets/api-key
chmod 600 secrets/api-key
```

Edit `.env` and replace the placeholder with the exact URL printed by `just
route`. `.env`, `secrets/`, generated config, and uploaded data are ignored by
Git. Never place API keys, passwords, real tailnet domains, or generated state
in tracked files.

Alternatively, set `GOKAPI_API_KEY` and `GOKAPI_PUBLIC_URL` in the calling
process. The key environment variable takes precedence over the secret file.

## Share and delete artifacts

The default is seven-day expiry and unlimited downloads (`0` in Gokapi):

```bash
bin/share /path/to/image.png
just share /path/to/report.pdf
bin/share upload /path/to/file --days 3 --downloads 10
bin/share delete FILE_ID_FROM_UPLOAD_JSON
```

An upload prints the complete JSON response first. It rewrites the returned
URLs to the configured stable private origin, then prints Markdown. Images use
Gokapi's direct `/h/<hotlink-id>` raw URL; other files use the download page.
Deletion prints a small JSON confirmation. The API key needs the corresponding
Gokapi permission or the helper exits with the HTTP error and response body.

The helper uploads through loopback by default, while the URL it prints uses
private HTTPS. This keeps agent-to-service traffic local and avoids relying on
hairpin access through the reverse proxy.

## Routine operation

```bash
just status
just logs
just stop
just start
dev-route list-named
dev-route resolve files
```

The application health/setup page can also be checked locally without a key:

```bash
curl --fail --show-error --head http://127.0.0.1:53842/
```

## Updating

The image is intentionally pinned to `docker.io/f0rc3/gokapi:v2.2.4`, a release
that includes important security fixes. Do not switch it to `latest`.

Before an update, read every intervening Gokapi release note and take a backup.
Then change the version in both `deploy/gokapi.container` and the `update`
recipe, run validation, reinstall the Quadlet, pull, and restart:

```bash
just validate
just install
podman pull docker.io/f0rc3/gokapi:vNEW_VERSION
systemctl --user restart gokapi.service
systemctl --user --no-pager status gokapi.service
```

Do not downgrade a migrated Gokapi database unless the release notes explicitly
say it is supported.

## Backup and restore

Both `config/` and `data/` are required for a complete backup. Stop the service
to obtain a consistent snapshot:

```bash
cd ~/docker/files
just stop
mkdir -p backups
tar --create --gzip \
  --file "backups/gokapi-$(date +%Y%m%d-%H%M%S).tar.gz" \
  config data
just start
```

Store the archive somewhere protected; configuration may contain password
hashes and encryption material. The archive is ignored by Git.

Restore only into an empty, stopped deployment after verifying the archive:

```bash
cd ~/docker/files
just stop
tar --list --file /safe/path/gokapi-backup.tar.gz
mv config "config.before-restore-$(date +%Y%m%d-%H%M%S)"
mv data "data.before-restore-$(date +%Y%m%d-%H%M%S)"
tar --extract --gzip --file /safe/path/gokapi-backup.tar.gz
chmod -R u+rwX,go-rwx config data
just start
just status
```

Keep the moved directories until the restored service and several artifacts
have been verified. Restore with a Gokapi version compatible with the backed-up
database.

## Security model

- Tailnet membership and Tailscale ACLs are the network boundary. The dev-router
  Caddy listeners are bound only to host loopback and the configured Tailscale
  address, while Gokapi is bound only to host loopback.
- Gokapi login and upload API keys are an additional application boundary. Use
  a dedicated least-privilege key for agents and revoke it if exposed.
- Download and hotlink URLs are bearer links. Anyone who can reach the private
  hostname and obtains a returned URL can use it until expiry/deletion; do not
  paste links into audiences outside the intended trust boundary.
- Unlimited downloads are required for reliable image rendering because chat
  clients can fetch or refetch previews. The seven-day expiry remains the
  default containment mechanism.
- `NoNewPrivileges` and an empty Linux capability set reduce container process
  privileges. Rootless Podman prevents container UID 0 from becoming host root.

## Troubleshooting

### Quadlet or rootless Podman permissions

```bash
systemctl --user daemon-reload
systemctl --user status gokapi.service
journalctl --user-unit gokapi.service --lines=100
podman unshare id
stat -c '%U:%G %a %n' data config
```

Run all Gokapi Podman and systemd commands as the normal user, never with
`sudo`. If stale files were created by another ownership mapping, stop the
service and use `podman unshare chown -R 0:0 data config`; for this Quadlet,
container root maps to the invoking unprivileged user. Do not recursively chown
unknown paths.

### SELinux bind mounts

The Quadlet uses `:Z` so Podman gives the two private bind mounts an exclusive
container label. Check denials with `ausearch -m AVC -ts recent` and inspect
labels with `ls -Zd data config`. Do not disable SELinux. If the paths were
copied from another system, reinstall/start the unit so Podman can relabel
them, or use `restorecon` only after confirming the expected host policy.

### Port or route failures

```bash
ss -ltn '( sport = :53842 )'
curl --fail --show-error http://127.0.0.1:53842/
dev-route list-named
dev-route resolve files
dev-route validate
```

Only `127.0.0.1:53842` should listen for Gokapi. If the route registry is valid
but Caddy restarted without its generated fragment, `dev-route apply`
reconciles persistent routes. This host does not use `tailscale serve` for
these named services; inspect the dev-router/Caddy status instead. Do not use
Funnel.

### Hotlinks do not preview

- Confirm setup has E2E encryption disabled and the JSON contains a non-empty
  `FileInfo.HotlinkId`.
- Confirm the content type starts with `image/`. SVG is intentionally not
  hotlinkable in Gokapi v2.2.4.
- Paste the `/h/…` URL, not only the `/d?id=…` download-page URL.
- A cloud-hosted chat renderer is not a device on this tailnet, so it cannot
  fetch the private URL. The link can still be opened by you from another
  tailnet-connected machine; an inline preview inside the cloud chat is not a
  reliable verification method.
- Unlimited downloads avoid preview fetches consuming a finite quota, but the
  bearer URL still expires after seven days by default.

## Secret-free verification and post-setup checks

These do not require an API key:

```bash
just validate
bash -n bin/share
bin/share help
grep '^PublishPort=127.0.0.1:53842:53842$' deploy/gokapi.container
grep '^Image=docker.io/f0rc3/gokapi:v2.2.4$' deploy/gokapi.container
```

After inserting the real `.env` URL and API key:

```bash
just start
just route
dev-route resolve files
bin/share /path/to/test.png
```
