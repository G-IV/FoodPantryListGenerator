---
mode: ask
model: GPT-5
description: "Set up and run the Food Pantry manual test sandbox"
tools: ["codebase", "editFiles", "runCommands", "search", "githubRepo", "extensions", "runTests", "usages"]
---

Use the skill `food-pantry-manual-test-sandbox` to create and run a manual test sandbox for FoodPantryListGenerator.

User scenario to validate: ${input:Describe the behavior, branch, or scenario to verify}

Requirements:
- Use `dev/output/manual-test-sandbox/` as the default isolated working directory.
- Stage `tests/fixtures/InvNmbrs.csv` into the sandbox when flagged scenarios are part of the run.
- Open and follow `tests/manual_tests/checklist.html` and `tests/manual_tests/test_barcodes.html`.
- Launch from the sandbox working directory.
- Summarize checklist sections exercised and pass/fail outcomes.
