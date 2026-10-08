---
name: app-icon
description: Explicitly invoked workflow to create or replace an app, favicon, extension, or project icon and save a small root-level JPG for T3 Code.
disable-model-invocation: true
---

# App icon

Create an icon that communicates the app's main function and remains readable at small sizes. Also provide a small JPG in the project root for the user's T3 Code project icon.

Run this workflow only when the user invokes `$app-icon`, `/app-icon`, or explicitly asks to use the `app-icon` skill. Do not select it automatically for a new app or a generic icon request.

## Determine the icon's purpose

Read the project's instructions, README or domain documentation, and relevant app entry points. Identify its main function and existing visual identity before choosing a symbol. Inspect existing icons and their packaging or manifest references. Preserve an established identity unless the user asks to replace it.

Keep the scope tied to the request. A project-folder icon needs the root JPG. An app-icon replacement also needs the relevant packaged assets. An icon task does not authorize a UI redesign or a platform migration.

## Create and integrate

- Choose a simple silhouette and a palette appropriate to the app's function and theme. Avoid tiny details or text that disappears at launcher size.
- For a new raster illustration or a requested image edit, use the available image-generation tool and its skill instructions. If that capability is unavailable, report the blocker rather than silently changing the requested output to a placeholder. Edit an existing SVG or other native source directly when that is the appropriate task.
- Keep the reusable source or high-resolution master in the project's existing asset layout. Copy generated project assets into the repository before finishing.
- Derive the platform assets from the selected design. Follow the target's existing configuration for Android launcher and adaptive icons, web favicons, extension sizes, or desktop package icons. Preserve transparency where those formats need it.
- Also save a real RGB JPEG in the project root. Follow an existing root icon filename when present. Otherwise use `app-icon.jpg`, with 512 by 512 pixels as a default for a small project thumbnail. Honor a user-specified filename or size. This default is not a T3 Code format requirement.
- Flatten transparency onto an intentional background for the JPG. Do not rename a PNG to `.jpg`. Keep transparent platform assets separate from the JPEG thumbnail.
- When replacing a desktop tray icon, use a suitable simplified symbol and check visibility against both light and dark panels. A detailed launcher illustration may need a separate tray version.
- Update relevant asset references and packaging inputs. Do not install the app or change T3 Code's project configuration unless that is part of the request.

## Verify and report

Open the final root JPG and relevant platform assets. Inspect the design at small launcher or tray sizes as well as full size. Verify the JPEG's actual format, dimensions, and location, and check that manifests or packaging reference files that exist. Use the project's relevant asset or packaging checks when needed.

Report the root JPG path and the app assets updated. Distinguish files created from assets verified in a running app. Use the `share-file` skill only when an upload or private file URL is requested.
