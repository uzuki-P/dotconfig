# Private upload notifications

This companion to `../files` runs ntfy v2.28.0 as a rootless Quadlet. It binds
only to `127.0.0.1:53843`. The existing dev-router supplies the private HTTPS
`ntfy` route. No Firebase or public listener is required.

## Set up the server

Run these commands from `~/docker/ntfy` after Stow has linked this directory.
Copy `.env.example` to `.env` and set the real private HTTPS URL there.

```bash
chmod 600 .env
just validate
just install
just start
just route
just bootstrap-auth
```

`bootstrap-auth` generates passwords and tokens into local `secrets/` files
with mode 0600. It copies the publisher token to the files service and enables
its endpoint file. It prints no credentials and preserves existing credentials
on subsequent runs. The android account can read device topics. The publisher
account can write them. Anonymous access is denied. Use `secrets/android-password`
for the phone's ntfy account. `user-add`, `configure-access`, and `token-add` are
available for manual setup instead.

## Connect a phone

Install ntfy on Android. Add the private HTTPS server and the android account
under its account settings, then choose that server for UnifiedPush. In Gokapi,
choose Notifications, Instant. Copy the registered device endpoint into
`~/docker/files/secrets/ntfy-endpoints`, one HTTPS URL per line, mode 0600.
Set `NTFY_ENDPOINTS_FILE` in the files service's `.env` to that file.

UnifiedPush creates a device-specific `up...` topic. The publisher must send to
that endpoint to reach Gokapi. A regular `gokapi-uploads` subscription in ntfy
can also show the messages, but it does not deliver them to Gokapi. Optional
`NTFY_URL` publishes to that regular topic as well.

If an endpoint changes, replace its old line. Treat the endpoint list as private.
The upload helper sends a small JSON payload after Gokapi accepts each file.
Gokapi fetches the corresponding metadata from its configured server before
showing a notification. Uploads from the phone do not publish to ntfy.

Gokapi falls back to WorkManager polling if no distributor is registered.
Polling starts with a baseline and does not notify about every existing file.
Android schedules subsequent checks at intervals of at least 15 minutes.

## Validate

`just validate` checks the deployment configuration. The files service's
`bin/test-notify-upload.py` tests optional publishing, endpoint delivery, and
failed publishing with a local mock HTTP server and fake credentials.
