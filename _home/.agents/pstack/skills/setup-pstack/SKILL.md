---
name: setup-pstack
description: Configure pstack delegate and review models for Codex, Claude Code, OpenCode, or T3 Code. Use for setup-pstack, configuring pstack models, or changing its reasoning budget.
metadata:
  opencode/autoinvoke: 'true'
  opencode/slash: 'true'
---

# Set up pstack

Read `~/.agents/pstack/RUNTIME.md` first. Configure `~/.agents/pstack/MODELS.json`, which every installed pstack workflow reads. Do not write Cursor rules or change the host's global model settings.

1. Detect the active host and its available delegation models using the runtime guide. Prefer the t3 profile when its orchestration tools are exposed. Otherwise choose codex, claude, or opencode. If explicit selections cannot be verified, offer inheritance. Do not ask for API keys or run model calls to discover names.
2. Read the existing JSON. Preserve other profiles and current role overrides. If the file is malformed or has an unsupported version, report the issue before replacing it. Initialize a missing profile with inherited roles.
3. Explain that reasoning budget controls internal model reasoning, affects latency and usage, and does not control reply length. Offer inherit, small, medium, large, and unlimited. They mean current settings, medium reasoning, high reasoning, xhigh reasoning, and the highest supported level. Prefer a structured question when the host supports it. Inherited roles retain the session's settings regardless of the budget label.
4. Show the role table and ask for preferences only where needed. Start new roles on inherit-parent. Preserve existing selections unless the user changes them. Panel lists control independent seat counts. Show whether the host can actually run different models. Present only confirmed model choices, plus inherit-parent and auto. Honor model and budget preferences already provided in the conversation.
5. Validate the full profile before writing. Every real model must be confirmed in the active catalog and supported by the delegation mechanism. For T3, store both providerInstanceId and model. Store effort separately in options only when the delegation tool accepts that setting. Keep inheritance aliases as strings. Use the nearest supported reasoning level at or below the requested level. If none fits, explain the limitation and obtain a choice. A budget label alone cannot force a tool to support a setting.
6. Update only the active profile in version 1 JSON. Re-read it and check its structure and selections. A rerun with unchanged preferences must preserve the same values. Tell the user the file path, active profile, and any inherited-model limitations. Future workflow invocations read the file. A new session may be needed for newly installed skills or commands.
7. Check whether the current project has a verify skill or existing harness. If neither exists and the project is an app, offer once to use create-verification-skill. Only generate it when requested. Do not create an app harness for a dotfiles installation. Point to poteto-mode for the first real task.

The scalar roles are `feature, refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `judgment and prose`, `hardest tasks`, `how explorer`, `how explainer`, `why investigators`, `why synthesizer`, `reflect tooling`, and `reflect judgment, divergent, synthesizer`.

The list roles are `architect runners` and `interrogate reviewers`. Default lists contain three inherit-parent entries.

Example profile entries:

```json
{
  "budget": "inherit",
  "roles": {
    "bug-fix": "inherit-parent",
    "interrogate reviewers": ["inherit-parent", "inherit-parent", "inherit-parent"]
  }
}
```

For explicit T3 selections use objects shaped like `{"providerInstanceId": "<confirmed provider>", "model": "<confirmed model>"}`. Add options only from the actual tool contract. Never paste model names or reasoning suffixes from the upstream Cursor examples.
