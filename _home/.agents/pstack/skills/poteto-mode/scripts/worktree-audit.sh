#!/usr/bin/env bash
# Keep the existing entrypoint while using portable, read-only Git inspection.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/worktree-audit.py" "$@"
