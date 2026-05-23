# Developer README

## Who this is for

This document is for anyone who needs to modify, build, or deploy the FoodPantryListGenerator application. It assumes basic familiarity with Python and the command line but not necessarily familiarity with this specific codebase.

**If you are returning to this project after a long time away:** start with the [Project overview](#project-overview) and [Repository structure](#repository-structure) sections. The [Module reference](#module-reference) section explains what each file does and why.

---

## Contents

1. [Project overview](#project-overview)
2. [Why we use Python](#why-we-use-python)
3. [Repository structure](#repository-structure)
4. [Module reference](#module-reference)
5. [Data formats](#data-formats)
6. [Setting up a development environment](#setting-up-a-development-environment)
7. [Running the tests](#running-the-tests)
8. [Building the Windows executable](#building-the-windows-executable)
9. [Releasing a new version](#releasing-a-new-version)
10. [Deploying to the Surface Pro](#deploying-to-the-surface-pro)
11. [Branching and versioning conventions](#branching-and-versioning-conventions)
12. [Open issues and roadmap](#open-issues-and-roadmap)
13. [Production environment](#production-environment)

---

## Project overview

FoodPantryListGenerator is a console application that runs on a Microsoft Surface Pro at the St. Andrew's food pantry. A volunteer uses a Tera barcode scanner to scan each customer's ID card as they enter the shopping area. The program records each case number to a date-stamped CSV file. At the end of pantry, that file is copied to a thumb drive and merged with the Oasis pantry assistance report by staff.

The application is intentionally simple — no network connection, no database, no GUI. This is by design: the volunteer running this station is not required to be trained on the Oasis system, so the tool needs to be as low-friction as possible.

---

## Why we use Python

The original application (v1.0.0) was written in C and compiled with Visual Studio. It was rewritten in Python for v2.0.0 for the following reasons:

- **Maintainability.** C is more susceptible to certain categories of bugs — memory management, string handling, format specifiers — that are simply easier to avoid in Python.
- **Testability.** The original C code mixed I/O and logic in a single `main()` function with no separation, making automated testing impractical. Python's module system makes it straightforward to test logic independently.
- **Extensibility.** Upcoming features (reporting, import/export, barcode validation) are significantly more practical to implement in Python than in C.
- **Cross-platform development.** Developers can work on macOS, Windows, or Linux without needing Visual Studio or a Windows-specific toolchain.
- **No runtime dependency on the Surface Pro.** PyInstaller bundles the Python interpreter into a single `.exe`, so Python does not need to be installed on the Surface Pro.

---

## Repository structure

```
FoodPantryListGenerator/
├── FoodPantryListGenerator.py   Entry point. Acquires a single-instance lock,
│                                 then runs the scanning session. Run this file
│                                 (or the compiled .exe) to start a session.
│
├── food_pantry/                 Core package. All business logic lives here.
│                                 One module per concern — see Module reference
│                                 below for what each file does.
│
├── tests/                       pytest unit and integration tests.
│   └── fixtures/                Synthetic CSV datasets (no real pantry data).
│                                 See fixtures/README.md for the scenario key.
│
├── docs/                        Documentation.
│   ├── ChurchCert.cer           Public code-signing certificate. Safe to
│   │                             distribute — install on each church computer
│   │                             to trust signed releases. See InstallationGuide.md.
│   ├── InstallationGuide.md     One-time setup guide for a new computer
│   │                             (certificate install, folder, shortcut).
│   ├── VolunteerInstructions.md Step-by-step guide for pantry volunteers.
│   ├── DeveloperReadme.md       This file.
│   └── Scanner User Manual.pdf  User manual for the Tera D5100 scanner.
│
├── .github/
│   └── workflows/
│       ├── test.yml             Runs tests on every push and pull request
│       │                         (ubuntu, windows, macos / Python 3.12).
│       └── release.yml          Runs only on version tags (v*). Re-runs tests,
│                                 builds the .exe on Windows, and creates a
│                                 GitHub Release with the .exe attached.
│
├── pyproject.toml               Configures pytest test discovery.
├── requirements-dev.txt         Development dependencies (pytest, pyinstaller).
├── README.md                    Short overview for anyone landing on the repo.
└── .gitignore
```

> **Runtime files (not in the repo):** On first run the application creates `InvNmbrs.csv` in its working directory (`C:\DoubleCheck\` in production) if it does not already exist. The file is a skeleton with just the two header rows — the administrator fills in their contact details and adds case numbers to flag. See the [InvNmbrs.csv format](#invnmbrscsv) section for details. Additionally, whenever a flagged barcode or already-served re-scan is detected, the application creates (or appends to) `flagged_barcodes20YYMMDD.csv` in the same directory. See [Flagged barcode log](#flagged-barcode-log---flagged_barcodes20yymmddcsv) for the format. While the application is running it also holds a `FoodPantryListGenerator.lock` file in the working directory to prevent a second instance from starting; the lock file is removed on exit and cleaned up automatically if left behind by a crash.

---

## Module reference

### `FoodPantryListGenerator.py`

The entry point. Contains `main()`, which acquires a single-instance lock via `lock.py` before starting a session — if another instance is already running it prints a message and exits. The scanning work is done in `_run_session()`: prompts for input, calls `parse_barcode()`, checks for flagged case numbers via `invalid_numbers.py`, calls `append_record()` for clean scans, calls `append_flagged_record()` for both flagged scans and already-served re-scans, and exits on blank input. It also calls `ensure_invnmbrs_exists()` and `validate_and_clean_invnmbrs()` at startup to ensure the flagged-numbers file is present and well-formed. It contains no business logic beyond wiring these pieces together — if you find yourself adding logic here, it probably belongs in a module inside `food_pantry/` instead.

### `food_pantry/lock.py`

Enforces single-instance operation. Provides two public functions:

- `acquire_lock()` — writes the current process PID to `FoodPantryListGenerator.lock` in the working directory and returns `True`. Returns `False` if a live process already holds the lock. If the lock file exists but the PID inside it is no longer running (stale lock from a crash), it is overwritten automatically.
- `release_lock()` — removes the lock file. Safe to call even if the file is absent.

On Windows, PID existence is checked via `ctypes.OpenProcess` with `PROCESS_QUERY_LIMITED_INFORMATION`. On POSIX systems, `os.kill(pid, 0)` is used. This distinction exists because on Windows, `os.kill` with signal 0 calls `TerminateProcess` rather than performing a harmless existence check.

### `food_pantry/invalid_numbers.py`

Manages `InvNmbrs.csv` — the flagged case number list maintained by the Oasis Administrator. Provides four public functions:

- `ensure_invnmbrs_exists(path)` — creates a skeleton file (contact row + `Case #` header, no case numbers) if the file is absent. Called at startup. Returns `True` if it created the file, `False` if it already existed.
- `validate_and_clean_invnmbrs(path, error_log_path)` — scans rows 3+ on startup; removes any row that is not a valid `C`+digits case number, rewrites the file, and appends removed rows to `InvNmbrs_errors.log`.
- `read_invalid_numbers(path)` — returns the current set of flagged case numbers. Called on every scan so mid-session changes take effect immediately.
- `read_admin_contact(path)` — returns the formatted contact string from row 1 for display in the flag banner.

### `food_pantry/scanner.py`

Responsible for one thing: turning a raw string (from the scanner or typed manually) into a normalized case number like `C1052089`.

The scanner in use is a **Tera D5100 2D Wireless Barcode Scanner** ([product page](https://tera-digital.com/products/2d-barcode-scanner-d5100)). It connects to the Surface Pro via a USB dongle. The user manual is stored at `docs/Scanner User Manual.pdf` in this repository.

The scanner sends raw input in the format `{[C]01052089}`. This module strips the wrapper characters and leading zeros. If the input doesn't start with `{[C]`, it is treated as a manually typed case number and the `C` prefix is added.

If the scanner model ever changes, or the barcode format changes, **only this file needs to be updated.** Everything else in the application works with normalized case numbers.

### `food_pantry/csv_writer.py`

Manages both output CSV files.

For the **scanned barcodes file** (`scanned_barcodes20YYMMDD.csv`): builds the filename, counts existing rows on startup, formats timestamps, and appends records. The row format (6 fields: case number, 4 empty fields, timestamp) is intentional — the empty fields exist for alignment with the Oasis pantry assistance report merge. **Do not change this row format without confirming the merge process still works.**

For the **flagged barcode log** (`flagged_barcodes20YYMMDD.csv`): provides `build_flagged_filename()` and `append_flagged_record()`. The flagged log uses a simple two-column format (`case_number,timestamp`) — **no empty merge fields** — because this file is for the administrator's review only and is never merged into Oasis.

### `tests/test_scanner.py` and `tests/test_csv_writer.py`

Unit tests. Run them with `pytest` (see [Running the tests](#running-the-tests)). Each test is named to describe the scenario it covers — reading the test names gives you a plain-English summary of what the modules are expected to do.

---

## Data formats

This section describes the two CSV files involved in a pantry session. Understanding them is essential for working on any feature that reads, compares, or reports on pantry data (see [Issue #2](https://github.com/G-IV/FoodPantryListGenerator/issues/2)).

### Scanner output — `scanned_barcodes20YYMMDD.csv`

Produced by `FoodPantryListGenerator.exe` during a session. Each row represents one scan event, appended in the order scans occurred.

**No header row.**

| Position | Field | Type | Example |
|----------|-------|------|---------|
| 1 | Case number | String — `C` prefix + digits | `C1052089` |
| 2–5 | *(empty)* | Empty columns to match the Oasis case number export format | |
| 6 | Timestamp | `M/D/YYYY H:MM` (no leading zeros) | `4/25/2026 8:00` |

```
C1052089,,,,,4/25/2026 8:00
C1052090,,,,,4/25/2026 8:03
```

Key behaviours:

- Rows are in chronological order (order of scanning).
- No deduplication — the same case can appear more than once if the barcode was scanned multiple times.
- The file may already contain records from a prior session when the app starts; new scans are appended.
- The four empty fields exist to match the column layout of the Oasis case number data export. **Do not change the row format without confirming with staff that the import process still works.**

### Flagged barcode log — `flagged_barcodes20YYMMDD.csv`

Produced by `FoodPantryListGenerator.exe` during a session whenever a flagged barcode is scanned. The filename uses the same date-stamp convention as the scanned barcodes file.

**No header row.**

| Position | Field | Type | Example |
|----------|-------|------|---------|
| 1 | Case number | String — `C` prefix + digits | `C1052089` |
| 2 | Timestamp | `M/D/YYYY H:MM` (no leading zeros) | `5/5/2026 9:15` |

```
C1052089,5/5/2026 9:15
C1052090,5/5/2026 9:47
```

Key behaviours:

- The file is created on the first flagged scan of the session. If it already exists (from a previous session on the same calendar date, or from the current session), new rows are appended.
- Unlike the scanned barcodes file, this file has **no empty merge columns** — it is for the administrator's review only and is never imported into Oasis.
- Each row represents one scan event, in chronological order.
- **Flagged barcodes** (case numbers in `InvNmbrs.csv`) are written here instead of the main scanned barcodes file.
- **Already-served re-scans** — a barcode scanned earlier in the same session (but not as the immediately prior scan) — are also written to this file using the same two-column format.

---

### Oasis assistance report — `*assistance_report*.csv`

Exported from the Oasis case management system after a session. One row per assistance record logged by a volunteer agent.

**12-line header section** precedes the column headers (rows 1–12 are the Filters/Summary block produced by Oasis). The column header row is row 13.

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

Key behaviours:

- The same case can appear more than once if a volunteer entered it multiple times, or if the case was served across multiple time windows.
- Oasis timestamps are 5-minute batch windows — an `Assistance Date` of `9:35` means the record was entered between `9:30` and `9:35`. Exact timestamp matching across the two files is not meaningful.
- This file contains PII (names, household sizes, agent names). **Never commit a real Oasis report to the repository.** Real reports belong in `docs/prev_reports/`, which is gitignored.

### Ideal state

A clean session produces a **1-to-1 correspondence** between the two files:

- Every case in the scanner file appears exactly once in the Oasis report.
- Every case in the Oasis report appears exactly once in the scanner file.

In practice this is the common case, but it is never guaranteed.

### What can happen

| Scenario | Scanner | Oasis | Notes |
|----------|---------|-------|-------|
| Clean match | Once | Once | Ideal state — customer went through both stations exactly once |
| Entered multiple times in Oasis | Once | Multiple | Data-entry error, or customer passed through the Oasis station more than once |
| Scanned multiple times | Multiple | Once | Accidental re-scan, or customer passed through this station more than once |
| Multiple in both | Multiple | Multiple | Any combination of the above — occurred at both stations |
| Scanner only | Once or multiple | Absent | Customer bypassed the Oasis station; customers are expected to go through Oasis first |
| Oasis only | Absent | Once or multiple | Customer was not scanned at this station; unexpected — customers should be recorded at both |

Synthetic test fixtures covering all of these scenarios are in `tests/fixtures/`. See the [fixture README](../tests/fixtures/README.md) for the scenario-to-case-number mapping used in those files.

### InvNmbrs.csv

An optional file placed in `C:\DoubleCheck\` by the pantry administrator to block flagged case numbers from being logged. It is **not** committed to the repository — it is operational data that lives only on the production machine.

**On first run the application creates the file automatically** if it does not exist, writing a skeleton with just the two header rows and no flagged case numbers. The administrator can then open it in Notepad to add their contact details and any case numbers to flag.

**Format:**

| Row | Content | Example |
|-----|---------|---------|
| 1 | Administrator contact — `Name,Phone` | `Pantry Admin,(555) 867-5309` |
| 2 | Column header (ignored by the app) | `Case #` |
| 3+ | One flagged case number per row | `C1052089` |

```
Pantry Admin,(555) 867-5309
Case #
C1052089
C1052090
```

Key behaviours:

- **On first run**, if the file does not exist, the application creates a skeleton automatically and prints a one-time notice prompting the administrator to open the file and fill in their contact details on line 1.
- The file is re-read on every scan, so changes take effect immediately without restarting the application.
- When a flagged barcode is scanned, a red banner is printed, the scan is **not** written to the scanned barcodes CSV, and the case number + timestamp **are** written to the [flagged barcode log](#flagged-barcode-log---flagged_barcodes20yymmddcsv). Scanning continues immediately with no blocking prompt.
- Once the administrator removes a case number from the file, the next scan of that barcode is logged normally.
- Row 1 is used as the contact string in the banner. If row 1 is absent or blank, the banner still displays but omits the contact line.

**Format validation:**

At startup the application checks every case number row (row 3+). A valid row is a `C` followed by digits — e.g. `C1052089`. Any row that does not match this pattern is removed from the file and written to `InvNmbrs_errors.log` (in the same folder) so the data is not lost. Blank rows are dropped silently without logging. The first two header rows are never touched.

---

## Setting up a development environment

### Python version

This project targets **Python 3.12**. This is the version used in the GitHub Actions workflow and the version all developers should use locally. Using a different version risks subtle incompatibilities that only surface during the automated build or on another developer's machine.

Check your current version with:

```
python --version
```

If you see anything other than `3.12.x`, install 3.12 before continuing (see platform instructions below).

### Why use a virtual environment?

A virtual environment is an isolated Python installation scoped to this project. You should always use one. Here's why it matters:

- **Python version mismatches.** Your system may have Python 3.9 or 3.11 installed globally. Running `python` or `pip` without a virtual environment uses whatever version is on your system PATH, which may not be 3.12. A virtual environment lets you pin the exact version this project requires.
Dependency isolation. pip install without a virtual environment installs packages globally, which can conflict with other projects on your machine. A virtual environment keeps this project's dependencies separate.
- **Reproducibility.** Another developer cloning the repo and following these steps will end up with the same environment you have.

The `.venv/` directory is in `.gitignore` — virtual environments are machine-specific and should never be committed.

---

### macOS

```bash
# Install Python 3.12 via Homebrew if you don't have it
brew install python@3.12

# Confirm the version
python3.12 --version

# Clone the repo
git clone https://github.com/G-IV/FoodPantryListGenerator.git
cd FoodPantryListGenerator

# Create a virtual environment using Python 3.12 specifically
python3.12 -m venv .venv

# Activate the virtual environment
# You will need to do this each time you open a new terminal for this project
source .venv/bin/activate

# Confirm the active Python version (should show 3.12.x)
python --version

# Install development dependencies into the virtual environment
pip install -r requirements-dev.txt
```

Your shell prompt will show `(.venv)` when the virtual environment is active. To deactivate it: `deactivate`.

---

### Windows

Download and install Python 3.12 from https://www.python.org/downloads/. During installation, check **"Add Python to PATH"** and **"Add Python to environment variables"**.

```powershell
# Confirm the version
python --version

# Clone the repo
git clone https://github.com/G-IV/FoodPantryListGenerator.git
cd FoodPantryListGenerator

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# You will need to do this each time you open a new terminal for this project
.venv\Scripts\activate

# Confirm the active Python version (should show 3.12.x)
python --version

# Install development dependencies into the virtual environment
pip install -r requirements-dev.txt
```

Your shell prompt will show `(.venv)` when the virtual environment is active. To deactivate it: `deactivate`.

> **Windows note:** If you see a permissions error running `.venv\Scripts\activate`, run this first in PowerShell:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Running the application locally (without building the .exe)

With the virtual environment active:

```bash
python FoodPantryListGenerator.py
```

The output CSV will be written to whatever directory you run the command from.

---

## Running the tests

Make sure your virtual environment is active (`source .venv/bin/activate` on macOS, `.venv\Scripts\activate` on Windows), then from the repository root:

```bash
pytest
```

For verbose output that shows each test name and result:

```bash
pytest -v
```

Tests run on every push via GitHub Actions (see `.github/workflows/test.yml`). A pull request to `main` will not be considered ready to merge if tests are failing.

---

## Building the Windows executable

The `.exe` must be built on Windows. The GitHub Actions workflow does this automatically when a version tag is pushed (see [Releasing a new version](#releasing-a-new-version)), so you should rarely need to build manually.

If you do need to build manually (e.g. for testing the .exe locally before releasing):

1. On your Windows machine, install dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run PyInstaller from the repository root:
   ```
   pyinstaller --onefile --name FoodPantryListGenerator FoodPantryListGenerator.py
   ```

3. The executable is created at `dist\FoodPantryListGenerator.exe`.

**Note:** PyInstaller bundles the Python interpreter into the `.exe`. No Python installation is required on the target machine. The resulting file is approximately 5–10 MB.

**Antivirus note:** Windows Defender may flag a freshly-built PyInstaller executable as suspicious (this is a known false positive with PyInstaller binaries). If this happens on the Surface Pro, add `C:\DoubleCheck\` to Windows Defender's exclusions list. This is a one-time step.

---

## Releasing a new version

1. Make sure all your changes are merged into `main` and tests are passing.

2. Update `__version__` in `food_pantry/__init__.py` to the new version number.

3. Commit that change:
   ```bash
   git commit -am "chore: bump version to v2.1.0"
   git push origin main
   ```

4. Tag the release and push the tag:
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

5. GitHub Actions picks up the tag, runs all tests, builds `FoodPantryListGenerator.exe` on a Windows runner, and creates a GitHub Release with the `.exe` attached automatically.

6. Go to the [Releases page](https://github.com/G-IV/FoodPantryListGenerator/releases) to confirm the release was created and the `.exe` is attached.

---

## Deploying to the Surface Pro

For a **first-time setup** on a new computer (certificate installation, folder creation, shortcut creation), see [InstallationGuide.md](InstallationGuide.md).

For a **version update** on a computer that is already set up:

1. On the Surface Pro, open a browser and go to the [Releases page](https://github.com/G-IV/FoodPantryListGenerator/releases).
2. Download `FoodPantryListGenerator.exe` from the latest release.
3. Copy it to `C:\DoubleCheck\`, replacing the previous version.
4. The desktop shortcut does not need to be updated — it already points to `C:\DoubleCheck\FoodPantryListGenerator.exe`.

**Desktop shortcut settings (for reference):**
- Target: `C:\DoubleCheck\FoodPantryListGenerator.exe`
- Start in: `C:\DoubleCheck\`
- Name: `FoodPantry ListGenerator`

The "Start in" field is what causes the output CSV to be saved to `C:\DoubleCheck\` rather than wherever the shortcut itself lives.

---

## Branching and versioning conventions

This project uses [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

| Change type | Version bump | Example |
|-------------|-------------|---------|
| Breaking change or full rewrite | MAJOR | `v1.0.0` → `v2.0.0` |
| New feature, backward compatible | MINOR | `v2.0.0` → `v2.1.0` |
| Bug fix | PATCH | `v2.1.0` → `v2.1.1` |

**Branch naming:**

| Type | Pattern | Example |
|------|---------|---------|
| New feature | `feat/<description>` | `feat/invalid-barcode-detection` |
| Bug fix | `fix/<description>` | `fix/timestamp-format` |
| Documentation only | `docs/<description>` | `docs/volunteer-instructions` |

**Workflow:**
1. Create a branch from `main`.
2. Make changes, write/update tests.
3. Open a pull request to `main`.
4. Tests must pass before merging.
5. After merging, tag `main` with the new version to trigger a release build.

---

## Open issues and roadmap

See the [GitHub Issues](https://github.com/G-IV/FoodPantryListGenerator/issues) page for the current backlog. Key upcoming work:

- **[#2 Invalid barcode detection](https://github.com/G-IV/FoodPantryListGenerator/issues/2)** — Detect case numbers that are no longer active in the Oasis system. The solution must work offline (no Oasis connection) since this station is intentionally staffed by non-Oasis-trained volunteers.

---

## Production environment

| Item | Detail |
|------|--------|
| Device | Microsoft Surface Pro |
| OS | Windows 11 Pro |
| CPU | Intel Core i5-1035G1 @ 1.10 GHz |
| RAM | 8 GB |
| Storage | 238 GB |
| Scanner | [Tera D5100 2D Wireless Barcode Scanner](https://tera-digital.com/products/2d-barcode-scanner-d5100) (connects via USB dongle; user manual in `docs/`) |
| Install location | `C:\DoubleCheck\` |
| Output files | `C:\DoubleCheck\scanned_barcodes20YYMMDD.csv` (all clean scans), `C:\DoubleCheck\flagged_barcodes20YYMMDD.csv` (flagged scans and already-served re-scans — created only when at least one such scan occurs) |
| Flagged numbers file | `C:\DoubleCheck\InvNmbrs.csv` (auto-created on first run; managed by the pantry administrator) |
| Lock file | `C:\DoubleCheck\FoodPantryListGenerator.lock` (created at startup, removed on exit; stale locks are cleaned up automatically) |
| Backup device | A second Surface Pro (labeled "M") with the same software installed |
