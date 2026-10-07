### Orchestrate

Use for a requested program that needs several owners or sessions. Complete smaller tasks directly. Read RUNTIME.md and MODELS.json before selecting delegates or tools.

1. Define the goal, scope, acceptance checks, and delivery actions the user authorized. A request to implement does not by itself request PR publication or merging.
2. Use the handoff skill for durable state. Keep a unit list with owner, allowed paths, dependencies, current status, evidence, and remaining work. Store briefs beside the handoff unless the project specifies another location.
3. Delegate only when the user or applicable instructions authorize it. Discover the host's actual child-task capabilities and concurrency limits. Do not require cloud placement or nested delegation. Use sequential work when those capabilities are absent. Select models from the active profile and preserve parent inheritance.
4. Give each worker a concrete goal, exclusive write scope, context, acceptance checks, verification commands, and required report. Read-only reviewers report findings without changing files or external systems. Include standing instructions in each brief.
5. Run independent work concurrently when supported. Resolve dependencies before starting dependent units. Keep one writer per worktree and avoid two workers editing the same files. Do not automatically launch a fixed number of workers or retry on guessed models.
6. Inspect completion evidence and reconcile every owned task. Use task status tools to check liveness. Do not restart an idle agent merely to check on it. Retry a failed unit at most twice before reporting the blocker and adjusting the plan.
7. Verify behavior with project commands and available browser or terminal tools. Scale review to the risk. An independent same-model attempt remains independent review, but it is not cross-model evidence. Record missing capabilities and failed checks.
8. For authorized PR work, follow project conventions and the actual forge. Register relevant PRs with the runtime. Preserve stack bases and exclusive ownership during rebases. Use the runtime watcher for requested monitoring. Schedule recurring work only when requested and supported.
9. Recheck the requested result, report verification and remaining blockers, and update the handoff. Do not claim persistence after the current turn unless a supported scheduler or watcher owns it.

Keep unrelated discoveries in the local report. Messages to others, ticket changes, evaluation jobs, deployment, deletion, and merges require their own authorization. Apply authorization already given without asking again.
