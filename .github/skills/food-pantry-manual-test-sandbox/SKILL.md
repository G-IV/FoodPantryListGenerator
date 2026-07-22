---
name: food-pantry-manual-test-sandbox
description: 'Create a manual testing sandbox for FoodPantryListGenerator. Use when preparing an isolated local run, staging the InvNmbrs.csv fixture, opening the manual checklist and barcode sheet, and verifying startup, clean scans, flagged scans, manual entry, and exit behavior.'
argument-hint: 'Describe the behavior, branch, or scenario you want to verify'
user-invocable: true
---

# Food Pantry Manual Test Sandbox

Use this skill when you need a repeatable manual-testing workflow for FoodPantryListGenerator without mixing test output into the repo root or a production `C:\DoubleCheck\` folder.

## What This Skill Produces

- An isolated working directory under `dev/output/manual-test-sandbox/`
- A staged `InvNmbrs.csv` fixture so flagged-barcode scenarios are predictable
- The manual test artifacts needed for scanning and verification:
  - `tests/manual_tests/checklist.html`
  - `tests/manual_tests/test_barcodes.html`
- A running local app session that writes its output files into the sandbox directory
- A concise pass/fail summary tied to the checklist sections that were exercised

## When to Use

Use this skill for prompts such as:

- "Set up a manual test sandbox for the scanner flow"
- "Run the barcode checklist against my branch"
- "Prepare a safe local sandbox for flagged barcode testing"
- "Verify manual entry and exit behavior with the test barcode sheet"

## Core Constraints

- Do not use or overwrite a real production `C:\DoubleCheck\` folder unless the user explicitly asks for a Surface Pro run.
- Keep runtime artifacts in `dev/output/manual-test-sandbox/` so `scanned_barcodes*.csv`, `flagged_barcodes*.csv`, `already_served*.csv`, `InvNmbrs_errors.log`, and `FoodPantryListGenerator.lock` stay isolated.
- Treat `tests/manual_tests/checklist.html` as the source of truth for the manual pass/fail checks.
- Treat `tests/manual_tests/test_barcodes.html` as the source of truth for the scan inputs.
- The application writes to the current working directory, so the working directory chosen for launch is part of the test setup.

## Procedure

1. Confirm scope.
   - Ask what behavior or branch the user wants to validate.
   - Always continue through launch and at least the checklist sections needed to validate the requested behavior.

2. Prepare the sandbox directory.
   - Use `dev/output/manual-test-sandbox/` as the default working directory.
   - Remove or archive old sandbox output only after checking with the user if preserving prior evidence matters.
   - Unless the user asks to preserve prior evidence, delete any existing `flagged_barcodes*.csv` file(s) in the sandbox **before launching the app** so flagged-log assertions start from a clean state.
   - Unless the user asks to preserve prior evidence, also delete prior scripted-output artifacts `manual_retest_output.txt` and `section35_retest_output.txt` before launch.
   - After cleanup and before launch, verify no `flagged_barcodes*.csv` file exists in the sandbox.
   - Ensure the directory exists before launching the app.

3. Stage deterministic fixture files.
   - Copy `tests/fixtures/InvNmbrs.csv` into the sandbox as `InvNmbrs.csv`.
   - If the scenario involves custom flagged messaging, also stage `tests/fixtures/flagged_message.txt` when present; otherwise rely on the built-in default banner text.

4. Open the manual test assets.
   - Open `tests/manual_tests/checklist.html` so the validation criteria stay visible.
   - Open `tests/manual_tests/test_barcodes.html` so the barcode sheet is available for scanning or visual reference.
   - If browser tools are available, prefer opening the files directly; otherwise tell the user exactly which files to open.

5. Launch the app from the sandbox.
   - Start the program with the sandbox as the current working directory.
   - For local development, prefer running `python ../../FoodPantryListGenerator.py` from inside `dev/output/manual-test-sandbox/`.
   - If the repo has a different validated launch command for the current environment, use that instead.

6. Choose checklist coverage based on the requested behavior.
   - Startup/output behavior: run checklist section 1 and section 5.
   - Clean scan persistence: run section 2.
   - Flagged-number blocking or logging: run section 3.
   - Manual entry or scanner parsing: run section 4 plus at least one clean scan from section 2.
   - Broad regression sweep: run sections 1 through 5 in order.

7. Validate outputs against the checklist.
   - Clean scans must append to `scanned_barcodes20YYMMDD.csv` in the sandbox.
   - Flagged scans must not appear in the scanned-barcodes file.
   - `flagged_barcodes20YYMMDD.csv` must not exist before launch in a clean run; it should be created only when the first flagged scan occurs.
   - Flagged scans must append to `flagged_barcodes20YYMMDD.csv` using exactly two columns: case number and timestamp.
   - Startup output must show the output filename, current record count, release URL, and scan prompt.
   - Manual entry must accept both numeric-only input and `C`-prefixed input.
   - Exiting on blank input must print the final saved filename and close cleanly.

8. Summarize results.
   - Report which checklist sections were exercised.
   - Report each observed pass/fail outcome.
   - Call out any files created in the sandbox and any mismatches between observed behavior and checklist expectations.
   - If behavior changed intentionally, recommend whether `tests/manual_tests/checklist.html`, `tests/manual_tests/test_barcodes.html`, or `docs/ChangeChecklist.md` should also be updated.

## Decision Points

### If the user wants to test flagged-barcode behavior

- Prioritize checklist section 3.
- Verify both on-screen banner behavior and `flagged_barcodes*.csv` contents.
- If results are inconsistent, inspect whether the sandbox `InvNmbrs.csv` was staged correctly and whether the launch directory was correct.

### If the user wants to test scanner parsing or manual entry

- Prioritize checklist section 4.
- Include one barcode scan from the sheet and one typed value to distinguish scanner-format handling from manual normalization.

### If the user is validating a branch that changed docs or manual-test assets

- Compare the exercised behavior to `tests/manual_tests/checklist.html` and `tests/manual_tests/test_barcodes.html`.
- Flag stale test assets explicitly instead of silently updating them.

## Completion Criteria

- Sandbox directory exists and is usable as the app working directory.
- `InvNmbrs.csv` fixture is staged when flagged scenarios are part of the run.
- `tests/manual_tests/checklist.html` and `tests/manual_tests/test_barcodes.html` were opened or clearly handed off to the user.
- The app was launched from the intended working directory.
- Results were summarized in terms of checklist expectations, not just raw terminal output.

## Related Repo Files

- `FoodPantryListGenerator.py`
- `docs/DeveloperReadme.md`
- `docs/ChangeChecklist.md`
- `tests/fixtures/InvNmbrs.csv`
- `tests/manual_tests/checklist.html`
- `tests/manual_tests/test_barcodes.html`