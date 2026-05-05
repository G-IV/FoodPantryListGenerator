"""
invalid_numbers.py — Flagged case number management

Reads InvNmbrs.csv, which the pantry administrator maintains to flag case
numbers that should not receive assistance (e.g. duplicate visits, known
fraud, administrative holds).

The file is re-read on every scan so changes take effect immediately
without restarting the application.  The administrator can add or remove
a case number from InvNmbrs.csv while a session is in progress.

File format
-----------
Row 1: Administrator contact info — two comma-separated fields: Name,Phone
Row 2: Column header (ignored — typically "Case #")
Row 3+: One flagged case number per row (the C-prefixed normalized form,
        e.g. C1052089). Trailing commas and surrounding whitespace are
        tolerated.

If the file does not exist the application behaves exactly as it did
before this feature was added — reads return empty/None and all scans are
logged normally.

Where to put InvNmbrs.csv
--------------------------
In production, place the file in C:\\DoubleCheck\\ (the same folder as the
.exe). The application looks for it in the current working directory.
For local development, place it in the project root (same directory as
FoodPantryListGenerator.py).
"""

import os
from typing import Optional


_RED = "\033[1;97;41m"
_RESET = "\033[0m"


def read_invalid_numbers(path: str) -> set:
    """
    Return the set of flagged case numbers from InvNmbrs.csv.

    Rows 1 and 2 are always skipped (contact info and column header).
    Returns an empty set if the file is absent or contains no case number
    rows.

    Args:
        path: Absolute or relative path to InvNmbrs.csv.

    Returns:
        A set of normalized case number strings (e.g. {"C1052089"}).
    """
    if not os.path.isfile(path):
        return set()

    flagged: set = set()
    with open(path, newline="", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i < 2:
                continue  # skip contact info row and column header row
            case = line.strip().rstrip(",").strip()
            if case:
                flagged.add(case)
    return flagged


def read_admin_contact(path: str) -> Optional[str]:
    """
    Return the administrator contact string from row 1 of InvNmbrs.csv.

    Row 1 is expected to be "Name,Phone". The two fields are joined with
    " — " for display (e.g. "Jane Smith — 555-0100").

    Returns None if the file is absent or row 1 is blank.

    Args:
        path: Absolute or relative path to InvNmbrs.csv.

    Returns:
        A formatted contact string, or None.
    """
    if not os.path.isfile(path):
        return None

    with open(path, newline="", encoding="utf-8") as fh:
        first_line = fh.readline().rstrip("\r\n").strip()

    if not first_line:
        return None

    parts = first_line.split(",", 1)
    if len(parts) == 2:
        return f"{parts[0].strip()} — {parts[1].strip()}"
    return first_line


def format_flag_banner(case_number: str, contact: Optional[str]) -> list:
    """
    Return the lines to print when a flagged barcode is scanned.

    The lines use ANSI escape codes for a red background with white bold
    text.  This renders correctly on Windows 10 / Windows 11 consoles and
    on macOS/Linux terminals.  No third-party library is required.

    Args:
        case_number: The normalized case number that was flagged.
        contact: The formatted administrator contact string, or None.

    Returns:
        A list of strings to be printed, one per line.
    """
    lines = [
        "",
        f"{_RED}  FLAGGED — DO NOT ISSUE: {case_number}  {_RESET}",
    ]
    if contact:
        lines.append(f"{_RED}  Contact administrator: {contact}  {_RESET}")
    lines.append("")
    return lines
