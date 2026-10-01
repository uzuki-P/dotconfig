# Triage states

The skills use five canonical triage states. This file maps them to the strings recorded in each local Markdown issue's `Status:` field.

| Canonical state | Local Status value | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill says to apply a triage state or label, update the local issue's `Status:` field using the corresponding value from this table. Record the separate category in its `Category:` field as `bug` or `enhancement`.

Edit the right-hand column to match whatever vocabulary you actually use.
