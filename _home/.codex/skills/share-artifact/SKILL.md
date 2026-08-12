---
name: share-artifact
description: Upload local images, reports, archives, and other agent-produced artifacts to this machine's private Gokapi service and return stable tailnet HTTPS links. Use when the user asks to share, publish, upload, or provide a private URL for a file, or when an artifact must be shown as a Markdown image through the files service. Also use to delete a previously shared item by its Gokapi file ID.
---

# Share Artifact

Use the installed helper at `~/docker/files/bin/share`. It owns authentication,
expiry defaults, URL construction, error handling, and image-hotlink selection.
Keep the API key inside `~/docker/files/secrets/api-key`; invoke the helper
without reading, copying, logging, or printing that file.

## Upload

1. Resolve the artifact to a readable local regular file. Preserve its useful
   filename and extension because Gokapi uses them for content type and links.
2. Run:

   ```bash
   ~/docker/files/bin/share /absolute/path/to/artifact
   ```

   The default is seven-day expiry with unlimited downloads. Pass
   `--days N` or `--downloads N` only when the requester specifies a different
   lifetime or limit.
3. Check for a successful JSON object and retain its `FileInfo.Id`. Use the
   Markdown line printed after the JSON as the share result:
   - images with a hotlink ID produce `![name](https://files.../h/...)`;
   - other files produce `[name](https://files.../d?id=...)`.
4. Return the clickable private URL or Markdown plus the file ID needed for
   deletion. State that the link is reachable only from permitted tailnet
   devices when that access boundary matters to the request.

Completion criterion: the helper exits successfully, its JSON reports
`Result: OK`, and the returned URL uses the private `https://files.` origin.

## Delete

Delete only the item the user identifies or explicitly asks to clean up:

```bash
~/docker/files/bin/share delete FILE_ID
```

Completion criterion: the helper prints `Result: OK` with the requested
`DeletedId`. Deletion is permanent.

## Diagnose

Keep diagnosis local and avoid browser automation:

```bash
systemctl --user is-active gokapi.service
ss -ltn '( sport = :53842 )'
dev-route resolve files
curl --fail --show-error --head http://127.0.0.1:53842/
```

If the service is inactive during an explicit upload request, start it with
`systemctl --user start gokapi.service` and retry once. Report helper errors
without exposing request headers or credentials.

The public service is private tailnet infrastructure. A cloud-hosted chat
renderer may not fetch its image hotlinks even though the user can open them
from a tailnet-connected device. Treat a successful helper response as the
upload result; do not replace the private link with a public hosting service.
