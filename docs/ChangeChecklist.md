# Change Checklist

Use this checklist for every behavior change, bug fix, or feature.

## 1) Scope and Behavior
- [ ] Change matches issue scope and expected behavior
- [ ] Edge cases reviewed (duplicate scans, flagged scans, manual entry, missing files)
- [ ] User-facing messages verified against real runtime output

## 2) Automated Tests
- [ ] Unit/integration tests updated for changed behavior
- [ ] Regression test added for bug-fix path
- [ ] Relevant pytest targets run locally and passing

## 3) Manual Test Assets
- [ ] tests/manual_tests/checklist.html updated if flow changed
- [ ] tests/manual_tests/test_barcodes.html updated if scenarios changed
- [ ] Manual verification run completed for changed path(s)

## 4) Developer Documentation
- [ ] docs/DeveloperReadme.md updated when architecture/flow changed
- [ ] Setup/run/test instructions still accurate

## 5) Volunteer Documentation
- [ ] docs/VolunteerInstructions.md volunteer section updated if workflow changed
- [ ] Instructions match current scanner/manual-entry behavior

## 6) Oasis Administrator Documentation
- [ ] Admin section in docs/VolunteerInstructions.md reviewed
- [ ] InvNmbrs, flagged handling, and log review steps are accurate

## 7) PR Hygiene
- [ ] PR description includes behavior changes and validation done
- [ ] Follow-up issues created for deferred work
- [ ] Reviewer checklist comment added when needed
