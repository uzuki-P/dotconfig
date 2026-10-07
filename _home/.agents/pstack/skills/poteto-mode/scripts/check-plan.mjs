#!/usr/bin/env node
import fs from "node:fs";
const file = process.argv[2];
if (!file) { console.error("Usage: node check-plan.mjs <plan.md>"); process.exit(2); }
const text = fs.readFileSync(file, "utf8").replace(/^```[^\n]*\n[\s\S]*?^```\s*$/gm, "");
const errors = [];
if (!/^# .+/m.test(text)) errors.push("Missing plan title");
for (const title of ["Scope", "Units", "Open questions"]) {
  if (!new RegExp(`^## ${title}\\s*$`, "m").test(text)) errors.push(`Missing ${title} section`);
}
const units = text.split(/^## Units\s*$/m)[1]?.split(/^## /m)[0] ?? "";
const blocks = units.split(/^### /m).slice(1);
if (!blocks.length) errors.push("No units");
for (const unit of blocks) {
  const name = unit.split("\n")[0];
  for (const field of ["Depends on", "Files", "Outcome", "Verify"]) {
    if (!new RegExp(`^- ${field}:\\s*\\S`, "m").test(unit)) errors.push(`${name}: missing ${field}`);
  }
}
if (/<[^>]+>/.test(text)) errors.push("Unfilled placeholder");
for (const error of errors) console.error(`${file}: ${error}`);
console.log(`${blocks.length} units, ${errors.length} problems`);
process.exit(errors.length ? 1 : 0);
