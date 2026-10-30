---
name: principle-encode-lessons-in-structure
description: "Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction. Encode the rule as a lint, metadata flag, runtime check, or script instead of more text."
disable-model-invocation: true
---

Read `~/.agents/pstack/RUNTIME.md` and the active profile in `~/.agents/pstack/MODELS.json` before following this workflow. Their runtime mappings override the Cursor-specific tools, model defaults, paths, and permissions below.

# Encode Lessons in Structure

If the lesson needs judgment and cannot be encoded, make the instruction more prominent and add an example of the failure mode.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.
