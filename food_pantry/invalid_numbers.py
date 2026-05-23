"""
invalid_numbers.py — Flagged case number management

Reads InvNmbrs.csv, which the pantry administrator maintains to flag case
numbers that should not receive assistance (e.g. duplicate visits, known
fraud, administrative holds).

The file is re-read only when its modification time changes, so edits made
by the administrator between scans take effect on the next scan after saving.

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

import datetime
import os
import re
from typing import Optional


_RED = "\033[1;97;41m"
_RESET = "\033[0m"
_CASE_NUMBER_RE = re.compile(r"^C\d+$")


def ensure_invnmbrs_exists(path: str) -> bool:
    """
    Create InvNmbrs.csv with a skeleton structure if it does not exist.

    The skeleton contains the two header rows (a placeholder contact row and the
    'Case #' column header) with no flagged case numbers.  The administrator
    can open the file in Notepad to replace the placeholder name and phone
    number with the real contact details, then add case numbers below.

    Args:
        path: Absolute or relative path to InvNmbrs.csv.

    Returns:
        True if the file was created, False if it already existed.
    """
    if os.path.isfile(path):
        return False
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write("Name,(xxx) xxx-xxxx\r\nCase #\r\n")
    return True


def validate_and_clean_invnmbrs(path: str, error_log_path: str) -> list:
    """
    Validate case number rows in InvNmbrs.csv and remove any that are malformed.

    Rows 1 and 2 (contact info and column header) are always kept as-is.
    Rows 3+ must be a case number in the form C followed by digits (e.g. C1052089).

    - Blank rows are silently removed without logging.
    - Non-blank rows that do not match the case number format are removed from
      the file and appended to the error log so the data is not lost.

    If no malformed rows are found the file is not rewritten.

    Args:
        path: Absolute path to InvNmbrs.csv.
        error_log_path: Absolute path to the error log file to append bad rows to.

    Returns:
        A list of (row_number, raw_value) tuples for each bad row that was
        removed and logged.  Returns an empty list if the file is absent or
        all rows are valid.
    """
    if not os.path.isfile(path):
        return []

    with open(path, "r", newline="", encoding="utf-8") as fh:
        lines = fh.readlines()

    header_rows = lines[:2]
    case_rows = lines[2:]

    good_rows: list = []
    bad_rows: list = []  # list of (1-based row number, stripped value)

    for i, line in enumerate(case_rows, start=3):
        stripped = line.strip().rstrip(",").strip()
        if not stripped:
            continue  # blank row — drop silently
        if _CASE_NUMBER_RE.match(stripped):
            good_rows.append(line)
        else:
            bad_rows.append((i, stripped))

    if bad_rows:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            fh.writelines(header_rows)
            fh.writelines(good_rows)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(error_log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\n[{timestamp}] Removed malformed rows from InvNmbrs.csv:\n")
            for row_num, value in bad_rows:
                fh.write(f"  Row {row_num}: {value!r}\n")

    return bad_rows


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
        f"{_RED}  An administrator has flagged this barcode  {_RESET}",
    ]
    if contact:
        lines.append(f"{_RED}  Contact administrator: {contact}  {_RESET}")
    lines.append("")
    return lines


def format_duplicate_banner(case_number: str, contact: Optional[str]) -> list:
    """
    Return the lines to print when a consecutive duplicate barcode is scanned.

    Uses the same visual treatment as format_flag_banner (red background,
    white bold text).  The volunteer is shown the same contact information
    so they can reach the administrator if the situation requires it.

    Args:
        case_number: The normalized case number that was scanned twice in a row.
        contact: The formatted administrator contact string, or None.

    Returns:
        A list of strings to be printed, one per line.
    """
    lines = [
        "",
        f"{_RED}  DUPLICATE — DO NOT ISSUE: {case_number}  {_RESET}",
    ]
    if contact:
        lines.append(f"{_RED}  Contact administrator: {contact}  {_RESET}")
    lines.append("")
    return lines


def format_already_served_banner(case_number: str, contact: Optional[str]) -> list:
    """
    Return the lines to print when a barcode is re-scanned that was already
    recorded earlier in the current session (non-consecutive duplicate).

    Uses the same red background and visual treatment as format_flag_banner.
    The volunteer sees the same "DO NOT ISSUE" style alert; the only difference
    is the body line explaining why — this person was already served today
    rather than being flagged by an administrator.

    Args:
        case_number: The normalized case number that was scanned again.
        contact: The formatted administrator contact string, or None.

    Returns:
        A list of strings to be printed, one per line.
    """
    lines = [
        "",
        f"{_RED}  ALREADY SERVED — DO NOT ISSUE: {case_number}  {_RESET}",
        f"{_RED}  This barcode has been serviced earlier today  {_RESET}",
    ]
    if contact:
        lines.append(f"{_RED}  Contact administrator: {contact}  {_RESET}")
    lines.append("")
    return lines
