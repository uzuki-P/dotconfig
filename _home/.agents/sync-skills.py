#!/usr/bin/env python3
"""Link home user skills to dotconfig without downloading or restoring skills."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "_home/.agents/skills"
HOME = Path.home()
TARGETS = (
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".zcode/skills",
    ".hermes/skills",
    ".openwiki/skills",
    ".config/goose/skills",
    ".config/opencode/skills",
)
RESERVED = {".codex/skills": {".system"}, ".claude/skills": {"synced", ".trash"}}
REMOVED = {"modern-web-guidance", "chrome-extensions"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without changing files")
    args = parser.parse_args()
    guard = subprocess.run([sys.executable, str(REPO / "_home/.agents/validate-pstack.py")])
    if guard.returncode:
        return guard.returncode
    skills = {p.name: p for p in SOURCE.iterdir() if (p / "SKILL.md").is_file()}
    if not skills or REMOVED & set(skills):
        parser.error("Source is empty or contains a deliberately removed skill")
    invalid = [p.name for p in SOURCE.iterdir() if p.name not in skills]
    if invalid:
        parser.error(f"Invalid source entries: {', '.join(sorted(invalid))}")

    changes = []
    for relative in TARGETS:
        directory = HOME / relative
        if directory.resolve() == SOURCE.resolve():
            continue
        if directory.is_symlink():
            parser.error(f"Unexpected directory link: {directory}")
        for existing in directory.iterdir() if directory.exists() else ():
            if existing.name in RESERVED.get(relative, set()):
                continue
            if not existing.is_symlink():
                parser.error(f"Move this independent skill into dotconfig first: {existing}")
            if existing.name not in skills:
                # Remove only links owned by the shared user skill installation.
                target = Path(os.path.abspath(existing.parent / os.readlink(existing)))
                roots = (HOME / ".agents/skills", SOURCE, REPO / "_home" / relative)
                if not any(target.is_relative_to(root) for root in roots):
                    parser.error(f"Unrecognized skill link: {existing}")
                changes.append((existing, None))
        for name, source in sorted(skills.items()):
            link = directory / name
            if not link.is_symlink() or link.resolve() != source.resolve():
                changes.append((link, source))

    lock = HOME / ".agents/.skill-lock.json"
    data = json.loads(lock.read_text()) if lock.exists() else None
    stale = set(data.get("skills", {})) - set(skills) if data else set()
    if args.check:
        for link, source in changes:
            print(f"{'Link' if source else 'Remove'} {link}")
        if stale:
            print(f"Remove stale lock entries: {', '.join(sorted(stale))}")
        print(f"Checked {len(skills)} skills across {len(TARGETS)} home directories")
        return int(bool(changes or stale))

    backup = HOME / ".local/share/agent-skill-backups" / f"{time.time_ns()}-home-sync"
    if changes or stale:
        backup.mkdir(parents=True)
        saved = {str(p.relative_to(HOME)): os.readlink(p) for p, _ in changes if p.is_symlink()}
        (backup / "links.json").write_text(json.dumps(saved, indent=2) + "\n")
        if stale:
            shutil.copy2(lock, backup / "skill-lock.json")
    for link, source in changes:
        if link.is_symlink():
            link.unlink()
        if source:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(os.path.relpath(source, link.parent))
    if stale:
        for name in stale:
            del data["skills"][name]
        lock.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Synced {len(skills)} skills across {len(TARGETS)} home directories, {len(changes)} link changes")
    if changes or stale:
        print(f"Recovery records: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
