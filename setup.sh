#!/bin/sh

stow .
stow _home --target=$HOME
python3 "$(dirname "$0")/_home/.agents/sync-skills.py"
