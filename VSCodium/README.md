# Vim and Which Key

Install `vscodevim.vim` and `VSpaceCode.whichkey`. The tracked user settings and keybindings are linked into `~/.config/VSCodium/User/`.

Press Space in Vim Normal or Visual mode to open the menu. Press another Space to find a file. Which Key also opens from an empty editor area. The explorer keeps its separate `Space e` sidebar toggle. Insert mode, search inputs, and terminals do not trigger the Space menu.

The menu owns the editor's Space shortcuts. Do not add competing `space ...` chords to `keybindings.json` or multi-key Space remaps to Vim settings.

| Shortcut | Action |
| --- | --- |
| `Space Space`, `Space f f` | Find a file |
| `Space f p` | Open a recent project |
| `Space /`, `Space f g`, `Space s g` | Search the project |
| `Space s b` | Search the current file |
| `Space s w` | Search the project with the current selection or word |
| `Space .`, `Space c a` | Code actions |
| `Space c r`, `Space c f` | Rename a symbol, format the file |
| `Space e` | Reveal the active file in the explorer |
| `Space b d`, `Space b o` | Close the active editor, close other editors |
| `Space g s` | Focus source control |
| `Space g h d` | Open the file diff |
| `Space g w t` | Open an existing Git worktree |
| `Space g f h` | Focus the file-history timeline |
| `Space g o` | Open the current file without its diff |
| `Space g g` | Start lazygit in a new integrated terminal |
| `Space m p`, `Space m P` | Markdown preview, preview beside the editor |
| `Space r t` | Choose a task |
| `Space t i` | Open the inlay-hint setting |
| `Space u w` | Toggle word wrap |
| `Space x x` | Show problems |

Normal mode also has `gd`, `gD`, `gi`, `gI`, `gt`, `gT`, and `gr` for definition, implementation, type definition, and references. Uppercase `D`, `I`, and `T` open beside the editor. `ss` lists file symbols, and `sS` lists workspace symbols. Vim Sneak is enabled for `s` and `S`. In Visual mode, `gc` toggles line comments. `gf` uses VSCodium's open-link action, which needs a recognized link or file path.

The existing pane movement, editor switching, diagnostics, Git hunk navigation, and explorer shortcuts remain. `Ctrl+Shift+G` focuses source control. In the source-control file list, `o` opens the selected file without its diff.

VSCodium does not provide exact equivalents for Zed's selected-hunk diff toggle, excerpt navigation, nearest-task discovery, or inlay-hint toggle. The menu uses the actions listed above. `Space a c` is omitted because no AI extension is installed. Zed's operator shortcuts `cr` and `ca` are omitted to preserve Vim's change operator. Use `Space c r` and `Space c a` instead.

The setup backup is outside this repository at `~/.local/state/dotconfig/backups/2026-10-03_164822-vscodium-which-key/`. Run its `restore.sh` to restore both original configuration files, including changes that existed before this setup. This replaces subsequent edits to those two files.
