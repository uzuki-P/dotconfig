#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from functools import cache
from pathlib import Path

PROJECT = "SCRUM"
BOARD = 1
SPRINT_FIELD = "customfield_10020"
# Credentials, the Jira site, the Bitbucket workspace, and the team live in this local
# file, never in the repository:
#   JIRA_EMAIL, JIRA_API_TOKEN, JIRA_CLOUD_ID   API access
#   JIRA_SITE                                   e.g. example.atlassian.net
#   BITBUCKET_WORKSPACE                         workspace that holds the repos below
#   JIRA_PERSON_<NICK>=<account id>|<Jira display name>|<git author>,<git author>|<usual areas>
# A plan's `assignee` is the lowercase <NICK>; the person whose nick is ME is the user.
TOKEN_FILE = Path.home() / ".config/crm-preview/jira.env"
TOKEN_KEYS = ("JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_CLOUD_ID", "JIRA_SITE", "BITBUCKET_WORKSPACE")
PERSON_PREFIX = "JIRA_PERSON_"

REPOS = {"FE": "capital-crm-client", "BE": "crmapi", "Mobile": "onecore-crm-mobile"}
AREAS = tuple(REPOS)
DEFAULT_STATUS = "To Do"


def acli(*args: str) -> str:
    result = subprocess.run(["acli", "jira", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"acli {' '.join(args)} failed:\n{result.stdout}{result.stderr}\nRe-run the same plan: finished steps are skipped.")
    return result.stdout


@cache
def token() -> dict[str, str]:
    if not TOKEN_FILE.is_file():
        sys.exit(f"Missing {TOKEN_FILE}. It needs {', '.join(TOKEN_KEYS)}.")
    lines = [line.split("=", 1) for line in TOKEN_FILE.read_text().splitlines() if "=" in line and not line.lstrip().startswith("#")]
    env = {k.strip().removeprefix("export "): v.strip().strip('"') for k, v in lines}
    missing = [k for k in TOKEN_KEYS if not env.get(k)]
    if not any(k.startswith(PERSON_PREFIX) for k in env):
        missing.append(f"{PERSON_PREFIX}<NICK> lines")
    if missing:
        sys.exit(f"{TOKEN_FILE} is missing {', '.join(missing)}.")
    return env


@cache
def people() -> dict[str, dict]:
    team = {}
    for key, value in token().items():
        if not key.startswith(PERSON_PREFIX):
            continue
        fields = [part.strip() for part in value.split("|")]
        if len(fields) < 3 or not fields[0] or not fields[1]:
            sys.exit(f"{TOKEN_FILE}: {key} must be <account id>|<Jira name>|<git authors>[|<areas>]")
        team[key[len(PERSON_PREFIX):].lower()] = {
            "account": fields[0],
            "jira": fields[1],
            "git": [a.strip() for a in fields[2].split(",") if a.strip()],
            "areas": fields[3] if len(fields) > 3 else "",
        }
    return team


def pr_url(area: str, number: str) -> str:
    return f"https://bitbucket.org/{token()['BITBUCKET_WORKSPACE']}/{REPOS[area]}/pull-requests/{number}"


def rest(method: str, path: str, body: dict | None = None) -> dict:
    env = token()
    auth = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_API_TOKEN']}".encode()).decode()
    request = urllib.request.Request(
        f"https://api.atlassian.com/ex/jira/{env['JIRA_CLOUD_ID']}/rest/api/3{path}",
        data=None if body is None else json.dumps(body).encode(),
        method=method,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return json.loads(raw) if raw else {"status": response.status}
    except urllib.error.HTTPError as error:
        sys.exit(f"{method} {path} failed with {error.code}:\n{error.read().decode(errors='replace')}")


def active_sprint() -> dict:
    data = json.loads(acli("board", "list-sprints", "--id", str(BOARD), "--state", "active", "--json"))
    sprints = data.get("sprints", data) if isinstance(data, dict) else data
    if not sprints:
        sys.exit("No active sprint on the SCRUM board. Ask the user which sprint to use.")
    return sprints[0]


def search(jql: str, fields: list[str]) -> list:
    issues, page_token = [], None
    while True:
        body = {"jql": jql, "fields": fields, "maxResults": 100}
        if page_token:
            body["nextPageToken"] = page_token
        page = rest("POST", "/search/jql", body)
        issues += page.get("issues", [])
        page_token = page.get("nextPageToken")
        if not page_token:
            return issues


def adf(text: str, area: str) -> dict:
    paragraphs = []
    for block in text.split("\n\n"):
        content = []
        for part in re.split(r"(PR #\d+)", block):
            match = re.fullmatch(r"PR #(\d+)", part)
            if match:
                content.append({"type": "text", "text": part, "marks": [{"type": "link", "attrs": {"href": pr_url(area, match.group(1))}}]})
            elif part:
                content.append({"type": "text", "text": part})
        paragraphs.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": paragraphs}


def adf_text(node: dict | list | None) -> str:
    if isinstance(node, list):
        return "".join(adf_text(child) for child in node)
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    if node.get("type") in ("inlineCard", "blockCard"):
        return node.get("attrs", {}).get("url", "")
    separator = "\n" if node.get("type") in ("paragraph", "heading") else ""
    return adf_text(node.get("content")) + separator


def titled(summary: str, area: str) -> str:
    return summary if summary.startswith(f"[{area}]") else f"[{area}] {summary}"


def same_text(a: str, b: str) -> bool:
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def validate(plan: dict) -> None:
    errors = []

    def need_text(item: dict, field: str, where: str) -> None:
        if not isinstance(item.get(field), str) or not item[field].strip():
            errors.append(f"{where}: missing {field}")

    def need_person(item: dict, field: str, where: str, required: bool) -> None:
        if field in item or required:
            if item.get(field) not in people():
                errors.append(f"{where}: {field} {item.get(field)!r} is not one of {', '.join(people())}")

    for i, task in enumerate(plan.get("create", [])):
        where = f"create[{i}] {task.get('summary', '')!r}"
        need_text(task, "summary", where)
        need_text(task, "description", where)
        need_person(task, "assignee", where, True)
        if task.get("area", "FE") not in AREAS:
            errors.append(f"{where}: area {task.get('area')!r} is not one of {', '.join(AREAS)}")
        if task.get("type", "Task") == "Subtask":
            errors.append(f"{where}: put subtasks under a parent's subtasks list")
        for j, sub in enumerate(task.get("subtasks", [])):
            sub_where = f"{where} subtasks[{j}] {sub.get('summary', '')!r}"
            need_text(sub, "summary", sub_where)
            need_text(sub, "description", sub_where)
            need_person(sub, "assignee", sub_where, False)
    for i, item in enumerate(plan.get("transitions", [])):
        need_text(item, "key", f"transitions[{i}]")
        need_text(item, "status", f"transitions[{i}]")
    for i, item in enumerate(plan.get("comments", [])):
        need_text(item, "key", f"comments[{i}]")
        need_text(item, "body", f"comments[{i}]")

    keys = set(plan.get("sprint_moves", [])) | {item.get("key") for item in plan.get("transitions", []) + plan.get("comments", [])}
    keys.discard(None)
    if keys:
        found = {i["key"]: i["fields"] for i in search(f"key in ({', '.join(sorted(keys))})", ["issuetype", "parent"])}
        errors += [f"{key}: no such ticket" for key in sorted(keys - set(found))]
        for key in plan.get("sprint_moves", []):
            fields = found.get(key)
            if fields and fields["issuetype"].get("subtask"):
                parent = (fields.get("parent") or {}).get("key", "its parent")
                errors.append(f"sprint_moves {key}: a subtask follows its parent's sprint; move {parent} instead")
    if errors:
        sys.exit("Plan is invalid, nothing was changed:\n  " + "\n  ".join(errors))


def jql_words(text: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def existing_task(summary: str, kind: str) -> dict | None:
    words = jql_words(summary)
    if not words:
        return None
    jql = f'project = {PROJECT} AND issuetype = "{kind}" AND summary ~ "{words}" ORDER BY created DESC'
    return next((i for i in search(jql, ["summary", "status"]) if same_text(i["fields"]["summary"], summary)), None)


def existing_subtasks(parent: str) -> list:
    return search(f"parent = {parent}", ["summary", "status"])


def statuses_of(keys: list[str]) -> dict[str, str]:
    if not keys:
        return {}
    return {i["key"]: i["fields"]["status"]["name"] for i in search(f"key in ({', '.join(keys)})", ["status"])}


def has_comment(key: str, body: str) -> bool:
    start = 0
    while True:
        page = rest("GET", f"/issue/{key}/comment?startAt={start}&maxResults=100")
        if any(same_text(adf_text(c.get("body")), body) for c in page.get("comments", [])):
            return True
        start += len(page.get("comments", []))
        if start >= page.get("total", 0) or not page.get("comments"):
            return False


def create(summary: str, kind: str, assignee: str, description: str, area: str, parent: str | None, sprint_id: int | None) -> str:
    body = {
        "projectKey": PROJECT,
        "type": kind,
        "summary": summary,
        "assignee": people()[assignee]["account"],
        "description": adf(description, area),
    }
    if parent:
        body["parentIssueId"] = parent
    elif sprint_id:
        body["additionalAttributes"] = {SPRINT_FIELD: sprint_id}
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    try:
        with handle:
            json.dump(body, handle)
        return json.loads(acli("workitem", "create", "--from-json", handle.name, "--json"))["key"]
    finally:
        os.unlink(handle.name)


def run(plan: dict, sprint: dict, write: bool) -> None:
    def say(action: str) -> None:
        indent = action[: len(action) - len(action.lstrip())]
        print(action if write else f"{indent}would {action.lstrip()}")

    wanted: dict[str, str] = {}
    for task in plan.get("create", []):
        area = task.get("area", "FE")
        kind = task.get("type", "Task")
        status = task.get("status", DEFAULT_STATUS)
        summary = titled(task["summary"], area)
        sprint_id = None if task.get("backlog") else sprint["id"]
        target = "backlog" if sprint_id is None else sprint["name"]
        found = existing_task(summary, kind)
        if found:
            key = found["key"]
            print(f"exists {key} {summary}")
        elif write:
            key = create(summary, kind, task["assignee"], task["description"], area, None, sprint_id)
            print(f"created {key} -> {target}, {status}: {summary}")
        else:
            key = None
            say(f"create {kind} [{task['assignee']}] -> {target}, {status}: {summary}")
        subs = existing_subtasks(key) if key else []
        for sub in task.get("subtasks", []):
            sub_status = sub.get("status", status)
            match = next((s for s in subs if same_text(s["fields"]["summary"], sub["summary"])), None)
            if match:
                sub_key = match["key"]
                print(f"  exists {sub_key} {sub['summary']}")
            elif write:
                sub_key = create(sub["summary"], "Subtask", sub.get("assignee", task["assignee"]), sub["description"], area, key, None)
                print(f"  created {sub_key} {sub_status}: {sub['summary']}")
            else:
                sub_key = None
                say(f"  create Subtask [{sub.get('assignee', task['assignee'])}] {sub_status}: {sub['summary']}")
            if sub_key:
                wanted[sub_key] = sub_status
            elif sub_status != DEFAULT_STATUS:
                say(f"  transition the new subtask -> {sub_status}")
        if key:
            wanted[key] = status
        elif status != DEFAULT_STATUS:
            say(f"transition the new task -> {status}")
    for item in plan.get("transitions", []):
        wanted[item["key"]] = item["status"]

    current = statuses_of(sorted(wanted))
    by_status: dict[str, list[str]] = {}
    for key, status in wanted.items():
        if same_text(current.get(key, ""), status):
            print(f"{key} is already {current[key]}")
        else:
            by_status.setdefault(status, []).append(key)
    for status, keys in by_status.items():
        if write:
            print(acli("workitem", "transition", "--key", ",".join(keys), "--status", status, "--yes").strip())
        else:
            say(f"transition {', '.join(keys)} -> {status}")

    for key in plan.get("sprint_moves", []):
        if write:
            rest("PUT", f"/issue/{key}", {"fields": {SPRINT_FIELD: sprint["id"]}})
        say(f"move {key} -> {sprint['name']}")
    for item in plan.get("comments", []):
        if has_comment(item["key"], item["body"]):
            print(f"{item['key']} already has comment: {item['body']}")
        elif write:
            print(acli("workitem", "comment", "create", "--key", item["key"], "--body", item["body"]).strip())
        else:
            say(f"comment on {item['key']}: {item['body']}")


def cmd_state(args: argparse.Namespace) -> None:
    sprint = active_sprint()
    print(f"Active sprint: {sprint['name']} (id {sprint['id']}), {sprint.get('startDate', '')[:10]} to {sprint.get('endDate', '')[:10]}\n")
    names = ", ".join(f'"{p["jira"]}"' for p in people().values())
    jql = f"project = {PROJECT} AND assignee in ({names}) AND (sprint in openSprints() OR updated >= -{args.days}d) ORDER BY assignee, updated DESC"
    for item in search(jql, ["summary", "assignee", "status", "issuetype", "parent", SPRINT_FIELD]):
        f = item["fields"]
        sprints = f.get(SPRINT_FIELD) or []
        active = [s["name"] for s in sprints if s.get("state") == "active"]
        parent = (f.get("parent") or {}).get("key") or "-"
        where = active[0] if active else (f"closed {sprints[-1]['name']}" if sprints else "BACKLOG")
        print(f"{f['assignee']['displayName'][:14]:14} | {item['key']:10} | {f['issuetype']['name']:7} | {f['status']['name']:14} | parent {parent:10} | {where:22} | {f['summary'][:90]}")


def cmd_team(args: argparse.Namespace) -> None:
    env = token()
    print(f"Jira site {env['JIRA_SITE']}, project {PROJECT}, board {BOARD}.")
    print(f"PR links: https://bitbucket.org/{env['BITBUCKET_WORKSPACE']}/<repo>/pull-requests/<N>\n")
    print(f"{'nick':8} | {'Jira name':28} | {'usual area':12} | git authors")
    for nick, person in people().items():
        print(f"{nick:8} | {person['jira']:28} | {person['areas']:12} | {', '.join(person['git'])}")
    authors = " ".join(f"--author='{a}'" for p in people().values() for a in p["git"])
    print(f"\ngit log author filter: {authors}")


def cmd_apply(args: argparse.Namespace) -> None:
    plan = json.loads(Path(args.plan).read_text())
    validate(plan)
    sprint = {"id": plan["sprint"], "name": f"sprint {plan['sprint']}"} if plan.get("sprint") else active_sprint()
    run(plan, sprint, args.yes)
    if not args.yes:
        print("\nDry run. Re-run with --yes after the user approves.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    team = sub.add_parser("team")
    team.set_defaults(func=cmd_team)
    state = sub.add_parser("state")
    state.add_argument("--days", type=int, default=21)
    state.set_defaults(func=cmd_state)
    apply = sub.add_parser("apply")
    apply.add_argument("plan")
    apply.add_argument("--yes", action="store_true")
    apply.set_defaults(func=cmd_apply)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
