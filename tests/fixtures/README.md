# Test Fixtures

This directory contains synthetic datasets used for developing and testing the
comparison feature (Issue #2). All names and case numbers are fabricated — no
real pantry data is stored here.

---

## File formats

### `sample_scanned_barcodes.csv` — scanner output

Produced by `FoodPantryListGenerator.exe` during a pantry session. Each row
represents one scan event, written in the order scans occurred.

**No header row.**

| Position | Field | Type | Example |
|----------|-------|------|---------|
| 1 | Case number | String — `C` prefix + digits | `C1100001` |
| 2–5 | *(empty)* | Reserved for Oasis mail-merge fields | |
| 6 | Timestamp | `M/D/YYYY H:MM` (no leading zeros) | `4/5/2025 8:00` |

```
C1100001,,,,,4/5/2025 8:00
C1100002,,,,,4/5/2025 8:03
```

- Rows are in chronological order (order of scanning).
- No deduplication — the same case can appear more than once if the barcode
  was scanned multiple times.
- The file may already contain records from a prior session when the app
  starts; new scans are appended.

---

### `sample_assistance_report.csv` — Oasis export

Exported from the Oasis case management system after a pantry session. One row
per assistance record logged by a volunteer agent.

**12-line header section** precedes the column headers (rows 1–12 are the
Filters/Summary block produced by Oasis). The column header row is row 13.

```
Filters:,,,,,,,
Include private records:,Yes,,,,,,
Date range:,"Apr 5, 2025 to Apr 5, 2025",,,,,,
Category:,Food Pantry: Pantry Assistance,,,,,,
,,,,,,,
Summary:,,,,,,,
Assistance count:,59,,,,,,
Case count:,50,,,,,,
Household count:,50,,,,,,
Member count:,188,,,,,,
,,,,,,,
Case #,First Name,Middle Name,Last Name,Suffix,Household Size,Assistance Date,Agent Name
```

| Column | Field | Notes |
|--------|-------|-------|
| 1 | Case # | Same `C`-prefix format as scanner output — directly comparable, no transformation needed |
| 2 | First Name | |
| 3 | Middle Name | May be empty |
| 4 | Last Name | |
| 5 | Suffix | May be empty |
| 6 | Household Size | Integer |
| 7 | Assistance Date | `M/D/YYYY H:MM` — represents the 5-minute batch window in which the agent entered the record, not the exact arrival time |
| 8 | Agent Name | Name of the volunteer who entered the record |

```
C1100001,Yaw,,Abubakar,,3,4/5/2025 8:00,Alice Barlow
```

- The same case can appear more than once if a volunteer entered it multiple
  times, or if the case was served across multiple time windows.
- Oasis timestamps are 5-minute batch windows — an `Assistance Date` of
  `9:35` means the record was entered between `9:30` and `9:35`.

---

## Ideal state

A clean session has a **1-to-1 correspondence** between the two files:

- Every case in the scanner file appears **exactly once** in the Oasis report.
- Every case in the Oasis report appears **exactly once** in the scanner file.
- The Oasis `Assistance Date` for each case falls within a few minutes of the
  corresponding scan timestamp.

In practice this is the common case, but it is never guaranteed.

---

## What can happen

The table below lists every known scenario and the case-number range reserved
for it in the fixture files.

| Scenario | Scanner | Oasis | Fixture range | Notes |
|----------|---------|-------|---------------|-------|
| Clean match | Once | Once | C1100001–C1100035 | Most common; 35 cases |
| Entered multiple times in Oasis | Once | Multiple | C1200001–C1200003 | Possible data-entry error |
| Scanned multiple times | Multiple | Once | C1300001–C1300003 | Accidental re-scan |
| Multiple in both | Multiple | Multiple | C1400001–C1400002 | Re-scanned and re-entered |
| Scanned only (single) | Once | Absent | C1500001–C1500003 | Volunteer forgot to log in Oasis |
| Oasis only (single) | Absent | Once | C1600001–C1600005 | Arrived before scanner was ready, or scan missed |
| Scanned only (multiple) | Multiple | Absent | C1700001–C1700002 | Re-scanned, never logged |
| Oasis only (multiple) | Absent | Multiple | C1800001–C1800002 | Logged multiple times, never scanned |

> Additional scenarios and what to do about each will be defined as Issue #2
> development progresses.
