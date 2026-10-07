### Feature

Implement and verify the requested behavior. Delegate only when authorized and useful.

1. Read the affected subsystem. Use `how` when it is unfamiliar.
2. Use `architect` when materially different design options need comparison.
3. Keep a short plan for substantial work. Split independent write scopes only when delegation helps.
4. Implement directly or, when authorized, delegate code-writing to a subagent using your configured feature model (default `inherit-parent`) with a specific scope (file paths, named data shape and its organizing structure per **principle-model-the-domain**, a state machine over scattered booleans, a table/registry over branching, a typed model over repeated shape assumptions, chosen before the delegate writes logic, and success criteria). When the implementation has materially different design choices, use **architect** to compare them before implementing. Use **interrogate** when the design needs independent review. A subagent forbidden to spawn satisfies this by owning the diff directly with the same review separation. No "standing by" reply that waits on a nested agent. Comments per **Comments**. Surgical edits, re-ground against the source for upstream-derived files. Port shared-primitive improvements to all consumers and verify each. Commit only when requested or already authorized.
5. Verify on the matching surface. "Inconclusive" or wrong-surface is not a pass. Flag it.
6. Complete and verify each unit before starting dependent work. Shape commits or stacks only when those delivery actions are authorized.
7. If the design is contested, `interrogate` before shipping.
8. Report the result and verification. Follow project conventions for commits or PRs only when requested.

Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline. That owner fans out internally after the blocking phase. Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments). Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.

**Reply:** what you built, what you chose and why, open decisions. Tables for design alternatives.
