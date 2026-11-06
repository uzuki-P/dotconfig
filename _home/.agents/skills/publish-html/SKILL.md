---
name: publish-html
description: Create and privately publish a rich HTML document response.
disable-model-invocation: true
---

# Publish HTML

Turn the answer into a private, durable HTML document and return its preview URL.

## Workflow

Publication authorization: invoking `$publish-html` authorizes publishing the
completed document to the private tailnet preview service at
`https://html-preview.ts.uzuki-p.my.id`. Treat that invocation as approval for
the publication destination and proceed directly after validation. The URL is
reachable only from devices with tailnet access. If the runtime itself blocks
the operation or requires a platform-level approval, report that boundary and
follow it; skill instructions cannot override runtime safety controls.

1. **Answer first.** Read [references/document-design.md](references/document-design.md)
   completely, then finish the underlying answer. Research or inspect sources when
   the request needs current, precise, or attributed information. Keep estimates
   visibly separate from sourced facts.
2. **Create the draft.** Make a working directory with `mktemp -d` and set
   `PUBLISH_HTML_SKILL_DIR` to the directory containing this `SKILL.md`:

   ```bash
   H="$PUBLISH_HTML_SKILL_DIR/scripts/html_preview.py"
   python3 "$H" new \
     --title "Document title" \
     --kicker "Document type or date" \
     --summary "One or two sentences on what the reader learns." \
     --output "$PUBLISH_HTML_WORK_DIR/document.html"
   ```

   The summary becomes the meta description and the catalog blurb, so write it
   for someone scanning a list.
3. **Fill the sections.** Replace `<!-- DOCUMENT_CONTENT -->` with the document
   body using `apply_patch`. Compose each section from the vocabulary in the
   design reference: prose, table, code, chart, Mermaid, callout, metrics, or a
   restrained combination.
4. **Publish.** `publish` validates the structure, prints lint warnings, and
   publishes atomically:

   ```bash
   python3 "$H" publish "$PUBLISH_HTML_WORK_DIR/document.html" --slug "short-topic"
   ```

   Fix every error and every `warning:` line, then publish again. To correct a
   document that is already published, keep its URL with
   `--update <document-id>` instead of `--slug`.
5. **Verify and reply.** Check the returned URL with a read-only HTTP request.
   Use browser automation only when the environment permits it and the user has
   granted any required permission. Reply with the exact private HTTPS URL and a
   one-line description, and state that only devices with tailnet access can
   open it.

`validate <file>` runs the same checks without publishing when you want them
earlier.

## Lifecycle

- List published documents with `html_preview.py list`, and archived ones with
  `html_preview.py list --archived`.
- Hide a document from the catalog without deleting it with
  `html_preview.py archive <document-id>`; restore it later with
  `html_preview.py unarchive <document-id>`.
- Remove a document permanently with `html_preview.py remove <document-id>`. It
  works on active and archived documents. Only remove when the user explicitly
  requests removal or cleanup.
- The catalog page lists every document with its summary, grouped by month, with
  search (`/`), sort, a rows or tiles layout, and an Archive tab. Archive shows
  an undo toast; delete asks for a second click. The buttons call
  `html_preview.py serve` through Caddy at `/api/*`; the `deploy` recipe in
  `~/docker/html-preview` applies changes to that stack.
- Catalog thumbnails are headless-Chrome screenshots (`thumb.png` and
  `thumb-dark.png` in each document folder). `publish` takes one for the
  document, `sync` fills in missing ones, and `html_preview.py thumbnails
  [<document-id>...]` retakes them. The catalog's refresh buttons (one per
  document, one in the header for all) call `/api/thumbnails`. Set
  `HTML_PREVIEW_BROWSER` if Chrome is not on `PATH`.
- After changing anything under `assets/`, bump `ASSET_VERSION` in
  `html_preview.py` and run `just prepare` in `~/docker/html-preview`. It copies
  the assets, points every published document at the new version, and rebuilds
  the catalog.

## Completion

Finish only when `publish` succeeds with no unresolved warnings, the published URL returns successfully, and the chat response contains that exact URL.
