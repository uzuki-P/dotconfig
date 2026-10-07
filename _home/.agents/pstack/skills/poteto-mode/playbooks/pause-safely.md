### Pause safely

Use when the user asks to pause. Context or usage limits require a handoff even when the user wants continued work.

1. Finish the current atomic operation and start no new work. Inspect owned delegate status and preserve useful reports before cancelling any owned tasks that must stop.
2. Preserve uncommitted edits in their existing checkout. Commit or push only when already authorized. Never include unrelated changes in a checkpoint commit.
3. Use the handoff skill to record the goal, checkout, branch, observed commit, uncommitted changes, completed checks, remaining work, and next action. Reuse the same durable handoff across sessions.
4. State what remains on disk and the handoff path. A handoff records state but cannot recover files after someone deletes the checkout.
