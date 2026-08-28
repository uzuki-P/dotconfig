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

1. Read [references/document-design.md](references/document-design.md) completely before authoring. Treat its primitives as a vocabulary, not a fixed layout.
2. Finish the underlying answer first. Research or inspect sources when the request requires current, precise, or attributed information. Keep estimates visibly separate from sourced facts.
3. Create a temporary working directory with `mktemp -d`. Set `PUBLISH_HTML_SKILL_DIR` to the directory containing this `SKILL.md`.
4. Create a draft from the shared shell:

   ```bash
   python3 "$PUBLISH_HTML_SKILL_DIR/scripts/html_preview.py" new \
     --title "Document title" \
     --kicker "Document type or date" \
     --output "$PUBLISH_HTML_WORK_DIR/document.html"
   ```

5. Replace `<!-- DOCUMENT_CONTENT -->` in the draft with the complete document body. Use `apply_patch` for the edit. Compose each section according to its information: prose, table, code, chart, Mermaid, callout, metrics, or a restrained combination.
6. Validate the completed file:

   ```bash
   python3 "$PUBLISH_HTML_SKILL_DIR/scripts/html_preview.py" validate \
     "$PUBLISH_HTML_WORK_DIR/document.html"
   ```

   Fix every reported issue. The step is complete when validation prints `valid` and no template marker remains.
7. Publish atomically:

   ```bash
   python3 "$PUBLISH_HTML_SKILL_DIR/scripts/html_preview.py" publish \
     "$PUBLISH_HTML_WORK_DIR/document.html" \
     --slug "short-topic"
   ```

8. Verify the returned URL with a read-only HTTP request. Use browser automation only when the active environment permits it and the user has granted any required permission.
9. Return a concise chat message containing the exact private HTTPS URL and a one-line description. State that the URL is available only to devices with tailnet access.

## Lifecycle

- List published documents with `html_preview.py list`, and archived ones with
  `html_preview.py list --archived`.
- Hide a document from the catalog without deleting it with
  `html_preview.py archive <document-id>`; restore it later with
  `html_preview.py unarchive <document-id>`.
- Remove a document permanently with `html_preview.py remove <document-id>`. It
  works on active and archived documents. Only remove when the user explicitly
  requests removal or cleanup.
- The catalog page has archive and delete buttons per document, plus a restore
  list for archived documents. They call `html_preview.py serve` through Caddy
  at `/api/*`; the `deploy` recipe in `~/docker/html-preview` applies any
  changes to that stack.

## Completion

Finish only when the HTML validates, the published URL returns successfully, and the chat response contains that exact URL.
