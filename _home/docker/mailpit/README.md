# Mailpit

Local SMTP catcher for development services. SMTP listens only on
`127.0.0.1:1025`, and the captured-message web UI is available at
`http://127.0.0.1:8025` or the private Caddy endpoint at
`https://mailpit.<CADDY_TS_BASE_DOMAIN>`.

Mailpit runs as a rootless Podman Quadlet managed by the user systemd instance.
Run `just setup` to install the Quadlet files and start it, `just status` to
inspect it, and `just stop` to stop it without deleting the `mailpit-data`
volume. Run `just` for the full command list.

The network Quadlet creates the externally named `mailpit` Podman network.
Penpot's backend joins that network and submits mail to `mailpit:1025`, with
authentication and TLS disabled. The volume Quadlet retains the existing
`mailpit-data` named volume, so captured messages survive the migration.

## Migrating from Compose

After updating this directory, remove only the old Compose-managed container;
leave its network and volume in place:

```bash
podman stop mailpit
podman rm mailpit
just setup
```

The Quadlets adopt the existing `mailpit` network and `mailpit-data` volume by
name. To start Mailpit automatically when the machine boots without an
interactive login, enable lingering once with `loginctl enable-linger`.
