# Show the available repository commands.
default:
  @just --list

# Validate the tracked tmux configuration in an isolated server.
validate-tmux:
  @socket="/tmp/dotconfig-tmux-validate-$$.sock"; \
    tmux -S "$socket" -f "{{justfile_directory()}}/tmux/tmux.conf" new-session -d; \
    status=$?; \
    tmux -S "$socket" kill-server 2>/dev/null || true; \
    exit $status
