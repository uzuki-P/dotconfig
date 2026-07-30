# Show the available repository commands.
default:
  @just --list

# Install Vim and Which Key in the desktop VS Code-compatible editor.
install-vscode-vim-which-key:
  @editor=""; \
    for candidate in code codium code-oss; do \
      if command -v "$candidate" >/dev/null 2>&1; then editor="$candidate"; break; fi; \
    done; \
    if [ -z "$editor" ]; then \
      echo "No desktop VS Code CLI found (tried: code, codium, code-oss)." >&2; \
      exit 1; \
    fi; \
    "$editor" --install-extension vscodevim.vim; \
    "$editor" --install-extension VSpaceCode.whichkey

# Install Vim and Which Key in code-server.
install-code-server-vim-which-key:
  code-server --install-extension vscodevim.vim
  code-server --install-extension VSpaceCode.whichkey

# Validate the tracked tmux configuration in an isolated server.
validate-tmux:
  @socket="/tmp/dotconfig-tmux-validate-$$.sock"; \
    tmux -S "$socket" -f "{{justfile_directory()}}/tmux/tmux.conf" new-session -d; \
    status=$?; \
    tmux -S "$socket" kill-server 2>/dev/null || true; \
    exit $status
