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
5. [Setting up a development environment](#setting-up-a-development-environment)
6. [Running the tests](#running-the-tests)
7. [Building the Windows executable](#building-the-windows-executable)
8. [Releasing a new version](#releasing-a-new-version)
9. [Deploying to the Surface Pro](#deploying-to-the-surface-pro)
10. [Branching and versioning conventions](#branching-and-versioning-conventions)
11. [Open issues and roadmap](#open-issues-and-roadmap)
12. [Production environment](#production-environment)

---

## Project overview

FoodPantryListGenerator is a console application that runs on a Microsoft Surface Pro at the St. Andrew's food pantry. A volunteer uses a Tera barcode scanner to scan each customer's ID card as they enter the shopping area. The program records each case number to a date-stamped CSV file. At the end of pantry, that file is copied to a thumb drive and merged with the Oasis pantry assistance report by staff.

The application is intentionally simple — no network connection, no database, no GUI. This is by design: the volunteer running this station is not required to be trained on the Oasis system, so the tool needs to be as low-friction as possible.

---

## Why we use Python

The original application (v1.0.0) was written in C and compiled with Visual Studio. It was rewritten in Python for v2.0.0 for the following reasons:

- **Maintainability.** C requires careful manual memory management and string handling. The original code contained bugs (see below) that are easy to make in C but trivial to avoid in Python.
- **Testability.** The original C code mixed I/O and logic in a single `main()` function with no separation, making automated testing impractical. Python's module system makes it straightforward to test logic independently.
- **Extensibility.** Upcoming features (reporting, import/export, barcode validation) are significantly more practical to implement in Python than in C.
- **Cross-platform development.** Developers can work on macOS, Windows, or Linux without needing Visual Studio or a Windows-specific toolchain.
- **No runtime dependency on the Surface Pro.** PyInstaller bundles the Python interpreter into a single `.exe`, so Python does not need to be installed on the Surface Pro.

**Bugs fixed in the rewrite:**

| Bug | Original C behavior | Fixed behavior |
|-----|---------------------|----------------|
| Manual case number entry | The C parser always assumed scanner format (`{[C]NNNNN}`), so a manually typed number like `1052089` would be parsed incorrectly | `scanner.py` detects the input format and parses accordingly |
| Timestamp format | `"%d/%d/%d% d:%d"` — the `% d` format specifier added a stray space before the hour | `format_timestamp()` in `csv_writer.py` builds the string manually with no stray space |

---

## Repository structure

```
FoodPantryListGenerator/
├── FoodPantryListGenerator.py   Entry point. Thin wrapper around the main loop.
│                                 Run this file (or the compiled .exe) to start
│                                 a scanning session.
│
├── food_pantry/                 Core package. All business logic lives here.
│   ├── __init__.py              Package init; contains __version__.
│   ├── scanner.py               Parses raw barcode input into case numbers.
│   └── csv_writer.py            Manages the output CSV file.
│
├── tests/                       Unit tests. One file per module.
│   ├── __init__.py
│   ├── test_scanner.py          Tests for scanner.py
│   └── test_csv_writer.py       Tests for csv_writer.py
│
├── docs/                        Documentation.
│   ├── VolunteerInstructions.md Step-by-step guide for pantry volunteers.
│   └── DeveloperReadme.md       This file.
│
├── .github/
│   └── workflows/
│       └── build.yml            GitHub Actions: runs tests on every push,
│                                 builds the .exe when a version tag is pushed.
│
├── pyproject.toml               Configures pytest test discovery.
├── requirements-dev.txt         Development dependencies (pytest, pyinstaller).
├── README.md                    Short overview for anyone landing on the repo.
└── .gitignore
```

---

## Module reference

### `FoodPantryListGenerator.py`

The entry point. It handles the main scanning loop: prompts for input, calls `parse_barcode()`, calls `append_record()`, and exits on blank input. It contains no business logic — if you find yourself adding logic here, it probably belongs in a module inside `food_pantry/` instead.

### `food_pantry/scanner.py`

Responsible for one thing: turning a raw string (from the scanner or typed manually) into a normalized case number like `C1052089`.

The Tera scanner sends raw input in the format `{[C]01052089}`. This module strips the wrapper characters and leading zeros. If the input doesn't start with `{[C]`, it is treated as a manually typed case number and the `C` prefix is added.

If the scanner model ever changes, or the barcode format changes, **only this file needs to be updated.** Everything else in the application works with normalized case numbers.

### `food_pantry/csv_writer.py`

Manages the output CSV file: building the filename, counting existing rows on startup, formatting timestamps, and appending records. The output format (6 fields per row, 4 empty fields between case number and timestamp) is intentional — those empty fields exist for alignment with the Oasis pantry assistance report merge. **Do not change the row format without confirming the merge process still works.**

### `tests/test_scanner.py` and `tests/test_csv_writer.py`

Unit tests. Run them with `pytest` (see [Running the tests](#running-the-tests)). Each test is named to describe the scenario it covers — reading the test names gives you a plain-English summary of what the modules are expected to do.

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
- **Dependency isolation.** `pip install` without a virtual environment installs packages globally, which can conflict with other projects on your machine. A virtual environment keeps this project's dependencies (`pytest`, `pyinstaller`) separate.
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

Tests run on every push via GitHub Actions (see `.github/workflows/build.yml`). A pull request to `main` will not be considered ready to merge if tests are failing.

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

Once a release is published on GitHub:

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
| Scanner | Tera barcode scanner (connects via USB dongle) |
| Install location | `C:\DoubleCheck\` |
| Output files | `C:\DoubleCheck\scanned_barcodes20YYMMDD.csv` |
| Backup device | A second Surface Pro (labeled "M") with the same software installed |
