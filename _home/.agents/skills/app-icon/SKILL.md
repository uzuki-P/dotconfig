---
name: app-icon
description: Explicitly invoked workflow to create or replace an app, favicon, extension, or project icon and save a small root-level favicon.png that T3 Code detects as the project icon.
disable-model-invocation: true
---

# App icon

Create an icon that communicates the app's main function and remains readable at small sizes. Also save a small `favicon.png` in the project root, which T3 Code finds without any configuration.

Run this workflow only when the user invokes `$app-icon`, `/app-icon`, or explicitly asks to use the `app-icon` skill. Do not select it automatically for a new app or a generic icon request.

## Determine the icon's purpose

Read the project's instructions, README or domain documentation, and relevant app entry points. Identify its main function and existing visual identity before choosing a symbol. Inspect existing icons and their packaging or manifest references. Preserve an established identity unless the user asks to replace it.

Keep the scope tied to the request. A project-folder icon needs only the root `favicon.png`. An app-icon replacement also needs the relevant packaged assets. An icon task does not authorize a UI redesign or a platform migration.

## Create and integrate

- Choose a simple silhouette and a palette appropriate to the app's function and theme. Avoid tiny details or text that disappears at launcher size.
- For a new raster illustration or a requested image edit, use the available image-generation tool and its skill instructions. If that capability is unavailable, report the blocker rather than silently changing the requested output to a placeholder. Edit an existing SVG or other native source directly when that is the appropriate task.
- Keep the reusable source or high-resolution master in the project's existing asset layout. Copy generated project assets into the repository before finishing.
- Derive the platform assets from the selected design. Follow the target's existing configuration for Android launcher and adaptive icons, web favicons, extension sizes, or desktop package icons. Preserve transparency where those formats need it.
- Also save a real PNG named `favicon.png` in the project root, 512 by 512 pixels unless the user names another size. T3 Code checks a fixed list of icon paths and never looks for `.jpg` names, so do not use `app-icon.jpg` or any other JPEG name. Encode the file as PNG. Do not rename a JPEG to `.png`.
- Flatten the root `favicon.png` onto an intentional background so it reads in T3 Code's light and dark sidebars. Keep transparent platform assets separate from it.
- T3 Code checks the root `favicon.svg` and `favicon.ico` before `favicon.png`. If either exists, it will show that file instead. Report this and leave those files alone unless the user asks to replace them.
- Before overwriting or deleting an existing file, open it, show the user what it is, and ask for confirmation. This covers an existing root `favicon.png`, a legacy root `app-icon.jpg` from earlier runs of this skill, and any platform icon the new design would replace. Do not overwrite or delete until the user confirms.
- When replacing a desktop tray icon, use a suitable simplified symbol and check visibility against both light and dark panels. A detailed launcher illustration may need a separate tray version.
- Update relevant asset references and packaging inputs. Do not install the app, create or edit `t3.json`, or change T3 Code's in-app project settings unless that is part of the request. A `t3.json` `iconPath` or a saved project icon in T3 Code takes precedence over `favicon.png`. If one exists, report it instead of changing it.

## Verify and report

Open the final root `favicon.png` and relevant platform assets. Inspect the design at small launcher or tray sizes as well as full size. Verify that `favicon.png` is a real PNG with the expected dimensions in the project root, and check that manifests or packaging reference files that exist. Use the project's relevant asset or packaging checks when needed.

Report the root `favicon.png` path, any file that takes precedence over it in T3 Code, the files replaced after confirmation, and the app assets updated. Distinguish files created from assets verified in a running app. Use the `share-file` skill only when an upload or private file URL is requested.
