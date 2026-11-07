---
name: sync-jira
description: For the Capital CRM project (capital-crm, crmapi and onecore-crm-mobile). Compare what the team shipped on develop and master with the SCRUM Jira board, propose tickets to create or update, and apply them with acli after the user approves. Use when the user asks to sync, update, add or check Jira tickets for the team's work. Works only on Pajar's PC.
---

# Sync Jira

This skill is for the Capital CRM project: the `capital-crm` frontend, the `crmapi` backend and the `onecore-crm-mobile` app. Do not use it for other Jira projects.

Project `SCRUM`, board 1. The Jira site, the Bitbucket workspace, and the team live in `~/.config/crm-preview/jira.env`, outside this public repository. Never copy names, emails, or account IDs from it into this skill or any other committed file.

Run the git commands in the repository you are reading. The script works from any directory. Start every sync by printing the team:

```bash
J=~/.agents/skills/sync-jira/scripts/jira.py
python3 $J team
```

`team` prints each person's nick (`me` is the user), Jira name, usual area, and git author names, plus a ready `--author` filter for `git log`. A plan's `assignee` is one of those nicks.

`acli jira auth status` must say Authenticated. The script also needs these keys in `jira.env`:

```bash
JIRA_EMAIL=...            # API access
JIRA_API_TOKEN=...
JIRA_CLOUD_ID=...
JIRA_SITE=example.atlassian.net
BITBUCKET_WORKSPACE=...   # builds the PR links
JIRA_PERSON_ME=<account id>|<Jira name>|<git author>,<git author>|<usual areas>
JIRA_PERSON_<NICK>=...    # one line per teammate
```

If acli is not authenticated or a key is missing, stop and tell the user.

## Areas: title prefix

The area depends on which repository the work is in, not on who did it. The usual area from `team` is only a hint.

| Area | Repository | Title prefix |
| --- | --- | --- |
| FE | `capital-crm` (often a worktree under `~/.t3/worktrees/capital-crm/`) | `[FE]` |
| BE | `~/projects/crmapi` | `[BE]` |
| Mobile | `~/projects/_sandbox/onecore-crm-mobile` | `[Mobile]` |

The prefix goes on the parent task only; subtasks have none. `apply` adds it from the plan's `area`. Do not add labels. When the work spans two areas, make one parent per area.

## 1. Read the branches

Read **develop and master** unless the user names other branches. Start from the active sprint's start date, or from the last ticketed work if that is earlier. Run the same commands in crmapi or the mobile repo when the user asks about BE or Mobile work.

```bash
git fetch -q origin
git log origin/master origin/develop --since=<date> --no-merges --date=short \
  --format='%h %ad %an | %s' <author filter from `team`>
git log origin/master origin/develop --merges --since=<date> --date=short --format='%h %ad | %s'
git log --no-merges --format='  %h %an | %s' <merge>^1..<merge>^2
```

Use the merge commits to map each commit to its PR, and note whether the commit has reached master or is only on develop. Ignore `Merged in develop` and `Merged in master` sync merges. If the user asks about unmerged work, list the person's feature branches with `git log --all ^origin/develop ^origin/master --author=...`.

## 2. Read Jira

```bash
python3 $J state            # active sprint, plus everyone's tickets in an open sprint or updated in 21 days
python3 $J state --days 45
acli jira workitem view SCRUM-1234 --fields summary,description,status,parent --json
```

`state` prints each ticket's status, parent and sprint. A ticket for current work that shows `BACKLOG` or `closed Sprint N` is missing from the active sprint.

## 3. Propose, then wait

Show a list per person and **submit nothing until the user agrees**. For each person, list:

- Work with no ticket: its PRs and commits, and whether they are on master or only on develop.
- Tickets to move into the active sprint.
- Status changes, with evidence. A ticket whose fix is only on a feature branch keeps its status.
- Comments, such as "Fixed in PR #1599, now on master" on QA tickets in Recheck.
- When nothing needs to change for someone, say so and why.

Ticket shape:

- One parent **Task** per feature or PR, titled `[<area>] <outcome>`. Its description is one or two sentences plus `Shipped in PR #N. Each part is a subtask.`
- Each distinct change is a **Subtask**, never a bullet in the parent's description. Small unrelated fixes go under a dated parent `[FE] Small fixes <Mon D> - <Mon D>`, with one subtask per fix.
- A subtask title states the user-visible outcome in plain English. Its description gives the effect and ends with `PR #N`. Read the commit body (`git show -s <sha>`) before you describe a change. Do not guess.
- Status: the user's (`me`) merged work is `Done`. For teammates, use the status of their recent shipped tickets (`Recheck` while QA checks, `Done` after), and ask when that is unclear.
- New tickets go into the **active sprint**. Put them in the backlog only when the user asks.

## 4. Apply

Write the approved list to a plan file in the scratchpad, dry-run it, then apply it:

```json
{
  "create": [
    {
      "area": "FE",
      "summary": "Self-service registration go-live",
      "assignee": "me",
      "status": "Done",
      "description": "Self-service sign-up ready for go-live. Shipped in PR #1600. Each part is a subtask.",
      "subtasks": [
        { "summary": "Gate self-registration with the register feature flag", "description": "Registration follows the register flag from crmapi. PR #1605." }
      ]
    }
  ],
  "sprint_moves": ["SCRUM-2700"],
  "transitions": [{ "key": "SCRUM-2671", "status": "Recheck" }],
  "comments": [{ "key": "SCRUM-2693", "body": "Fixed in PR #1599 (https://bitbucket.org/<workspace>/capital-crm-client/pull-requests/1599), now on master." }]
}
```

```bash
python3 $J apply plan.json         # validate and dry run
python3 $J apply plan.json --yes   # after approval
```

The dry run checks the whole plan first: every task and subtask needs a `summary` and `description`, assignees and areas must be known, referenced keys must exist, and subtasks cannot be sprint moves. An invalid plan changes nothing.

`apply` is safe to re-run. It reuses a task with the same title, a subtask with the same title under that parent, skips a transition when the ticket already has that status, and skips a comment the ticket already has. If a run stops halfway, fix the cause and run the same plan again.

- `area` is `FE` (the default), `BE` or `Mobile`. `assignee` is a nick from `team`.
- A subtask inherits its parent's status and assignee unless it sets its own.
- `"backlog": true` keeps a task out of the sprint. A top-level `"sprint": <id>` targets a sprint other than the active one.
- `PR #N` in a description becomes a link to the PR in the task's area: capital-crm for FE, crmapi for BE, onecore-crm-mobile for Mobile. Comments are plain text, so write the full PR URL there.

Afterwards run `python3 $J state --days 3` and report the new keys with their status and sprint.

## Known acli limits

- `acli jira workitem search` refuses the `parent` and `customfield_10020` (sprint) fields, so `state` reads them through the REST API.
- `acli jira workitem edit` cannot set a sprint. `apply` moves tickets with REST `PUT /issue/<key>` and `customfield_10020`. The token gets 401 on the agile `/sprint/<id>/issue` endpoint.
- `acli jira workitem create --from-json` takes the sprint in `additionalAttributes.customfield_10020`. Subtasks follow their parent's sprint, so move the parent instead.
- The source lives in `~/dotconfig/_home/.agents/skills/sync-jira`. Edit it there and run `just sync-skills` in dotconfig.
