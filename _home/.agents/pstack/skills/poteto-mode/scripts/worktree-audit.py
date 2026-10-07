#!/usr/bin/env python3
"""Audit local worktrees without fetching, changing files, or reading chat stores."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or "Git query failed")
    return result.stdout


def worktrees(repo):
    entries = []
    row = {}
    for field in git(repo, "worktree", "list", "--porcelain", "-z").decode().split("\0"):
        if not field:
            if row:
                entries.append(row)
                row = {}
            continue
        key, _, value = field.partition(" ")
        row[key] = value
    if row:
        entries.append(row)
    return entries


def paths(repo, *args):
    return [p.decode(errors="replace") for p in git(repo, "ls-files", *args, "-z").split(b"\0") if p]


def audit(repo, base=None, active=(), prs=()):
    entries = worktrees(repo)
    if not base:
        try:
            base = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").decode().strip()
        except ValueError:
            base = entries[0].get("branch", "").removeprefix("refs/heads/")
    try:
        base_sha = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
    except ValueError as e:
        raise ValueError("Choose an existing base with --base. " + str(e)) from e
    active = {str(Path(p).resolve()) for p in active}
    rows = []
    for index, entry in enumerate(entries):
        path = entry["worktree"]
        branch = entry.get("branch", "").removeprefix("refs/heads/")
        row = {"path": path, "branch": branch, "head": entry.get("HEAD", ""),
               "base": base, "base_sha": base_sha, "merged": "UNKNOWN", "remote": "UNKNOWN",
               "pr": "UNKNOWN", "active": "YES" if str(Path(path).resolve()) in active else "UNKNOWN",
               "tracked": [], "untracked": [], "ignored": [], "bucket": "review"}
        try:
            row["tracked"] = sorted(set(paths(path, "--modified") + paths(path, "--deleted") +
                                        [p.decode(errors="replace") for p in git(path, "diff", "--cached", "--name-only", "-z").split(b"\0") if p]))
            row["untracked"] = paths(path, "--others", "--exclude-standard")
            row["ignored"] = paths(path, "--others", "--ignored", "--exclude-standard", "--directory")
            result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", row["head"], base_sha], capture_output=True)
            if result.returncode not in [0, 1]:
                raise ValueError("Cannot establish commit reachability")
            row["merged"] = "YES" if result.returncode == 0 else "NO"
            try:
                upstream = git(path, "rev-parse", "--abbrev-ref", "@{upstream}").decode().strip()
                remote_sha = git(path, "rev-parse", "@{upstream}").decode().strip()
                row["remote"] = f"{upstream}:" + ("matches" if remote_sha == row["head"] else "differs")
            except ValueError:
                row["remote"] = "no-upstream"
            matches = [pr for pr in prs if pr["headRefName"] == branch]
            row["pr"] = ",".join(f"#{pr['number']}/{pr['state']}" for pr in matches) or "UNKNOWN"
            if index == 0:
                row["bucket"] = "hold-main"
            elif "locked" in entry:
                row["bucket"] = "hold-locked"
            elif row["active"] == "YES":
                row["bucket"] = "hold-active"
            elif row["tracked"] or row["untracked"] or row["ignored"]:
                row["bucket"] = "hold-files"
            elif any(pr["state"] == "OPEN" for pr in matches):
                row["bucket"] = "hold-open-pr"
            elif row["merged"] == "YES":
                row["bucket"] = "candidate-clean-merged"
            elif any(pr["state"] == "MERGED" for pr in matches):
                row["bucket"] = "review-squash-merge"
            else:
                row["bucket"] = "review-unmerged"
        except (ValueError, OSError) as e:
            row["bucket"] = "hold-unreadable"
            row["error"] = str(e)
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--base", help="Local base ref. No fetch occurs.")
    parser.add_argument("--active", action="append", default=[], help="Exact known active worktree, repeatable")
    parser.add_argument("--pr-data", type=Path, help="JSON array with number, state, and headRefName from the actual forge")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        prs = json.loads(args.pr_data.read_text()) if args.pr_data else []
        if not isinstance(prs, list) or any(not isinstance(p, dict) or not isinstance(p.get("number"), int)
            or p.get("state") not in ["OPEN", "CLOSED", "MERGED"] or not isinstance(p.get("headRefName"), str) for p in prs):
            raise ValueError("PR data must contain number, OPEN/CLOSED/MERGED state, and headRefName")
        rows = audit(Path(args.repo), args.base, args.active, prs)
    except (ValueError, OSError) as e:
        parser.error(str(e))
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        columns = ["bucket", "merged", "active", "remote", "pr", "tracked", "untracked", "ignored", "path"]
        print("\t".join(c.upper() for c in columns))
        for row in rows:
            print("\t".join(str(len(row[c])) if isinstance(row[c], list) else str(row[c]).replace("\t", "\\t").replace("\n", "\\n") for c in columns))
        print("Counts include ignored entries. Use --json to inspect exact names. Candidates need activity checks and target approval.", file=sys.stderr)


if __name__ == "__main__":
    main()
