# Mailpit

Local SMTP catcher for development services. SMTP listens only on
`127.0.0.1:1025`, and the captured-message web UI is available at
`http://127.0.0.1:8025` or the private Caddy endpoint at
`https://mailpit.<CADDY_TS_BASE_DOMAIN>`.

Run `just setup` to start it, `just status` to inspect it, and `just stop` to
stop it without deleting the `mailpit-data` volume. Run `just` for the full
command list.

The stack creates the `mailpit` Podman network. Penpot's backend joins that
network and submits mail to `mailpit:1025`, with authentication and TLS
disabled.
