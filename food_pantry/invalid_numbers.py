"""
invalid_numbers.py — Flagged case number management

Reads InvNmbrs.csv, which the pantry administrator maintains to flag case
numbers that should not receive assistance (e.g. duplicate visits, known
fraud, administrative holds).

The file is re-read only when its modification time changes, so edits made
by the administrator between scans take effect on the next scan after saving.

File format
-----------
Row 1: Column header (ignored — typically "Case #")
Row 2+: One flagged case number per row (the C-prefixed normalized form,
        e.g. C1052089). Trailing commas and surrounding whitespace are
        tolerated.

If the file does not exist the application behaves exactly as it did
before this feature was added — reads return empty sets and all scans are
logged normally.

Where to put InvNmbrs.csv
--------------------------
In production, place the file in C:\\DoubleCheck\\ (the same folder as the
.exe). The application looks for it in the current working directory.
For local development, place it in the project root (same directory as
FoodPantryListGenerator.py).
"""

from __future__ import annotations

import datetime
import os
import re


_RED = "\033[1;97;41m"
_GREEN = "\033[1;32m"
_RESET = "\033[0m"
_CASE_NUMBER_RE = re.compile(r"^C\d+$")

# Default flagged banner text used when no external message file exists.
DEFAULT_FLAGGED_MESSAGE_LINES = [
    "This barcode has been flagged.",
    "Please write the data from the barcode card/image",
    '   on the "Customer Scan-In Problems" form.',
    "Take a picture of the card/image using your phone.",
    "Text the image to the Oasis Administrator: Tina Tarbox (512) 492-5957",
]


def ensure_flagged_message_exists(path: str) -> bool:
    """
    Create flagged_message.txt with default banner text if it does not exist.

    Args:
        path: Absolute or relative path to flagged_message.txt.

    Returns:
        True if the file was created, False if it already existed or could
        not be created.
    """
    if os.path.isfile(path):
        return False

    try:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            fh.write("\r\n".join(DEFAULT_FLAGGED_MESSAGE_LINES))
            fh.write("\r\n")
    except OSError:
        return False

    return True


def ensure_invnmbrs_exists(path: str) -> bool:
    """
    Create InvNmbrs.csv with a skeleton structure if it does not exist.

    Note: this function is no longer called by the application (issue #27).
    It is retained here for convenience if manual bootstrapping is ever needed.

    The skeleton contains a single 'Case #' header row with no flagged case
    numbers.

    Args:
        path: Absolute or relative path to InvNmbrs.csv.

    Returns:
        True if the file was created, False if it already existed.
    """
    if os.path.isfile(path):
        return False
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write("Case #\r\n")
    return True


def validate_and_clean_invnmbrs(path: str, error_log_path: str) -> list:
    """
    Validate case number rows in InvNmbrs.csv and remove any that are malformed.

    Row 1 (column header) is always kept as-is.
    Rows 2+ must be a case number in the form C followed by digits (e.g. C1052089).

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

    header_rows = lines[:1]
    case_rows = lines[1:]

    good_rows: list = []
    bad_rows: list = []  # list of (1-based row number, stripped value)

    for i, line in enumerate(case_rows, start=2):
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

    Row 1 (column header) is always skipped.
    Returns an empty set if the file is absent or contains no case number rows.

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
            if i < 1:
                continue  # skip column header row
            case = line.strip().rstrip(",").strip()
            if case:
                flagged.add(case)
    return flagged


def read_flagged_message(path: str) -> list[str]:
    """
    Return flagged-banner message lines from a plain-text file.

    If the file does not exist, cannot be read, or contains no non-blank text,
    a built-in default message is returned.

    Args:
        path: Absolute or relative path to a plain-text message file.

    Returns:
        A list of message lines to render in the flagged red banner.
    """
    if not os.path.isfile(path):
        return list(DEFAULT_FLAGGED_MESSAGE_LINES)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = [line.rstrip("\r\n") for line in fh.readlines()]
    except OSError:
        return list(DEFAULT_FLAGGED_MESSAGE_LINES)

    if not any(line.strip() for line in lines):
        return list(DEFAULT_FLAGGED_MESSAGE_LINES)

    return lines


def format_flag_banner(case_number: str, message_lines: list[str] | None = None) -> list:
    """
    Return the lines to print when a flagged barcode is scanned.

    The lines use ANSI escape codes for a red background with white bold
    text.  This renders correctly on Windows 10 / Windows 11 consoles and
    on macOS/Linux terminals.  No third-party library is required.

    Args:
        case_number: The normalized case number that was flagged.
        message_lines: Optional banner text lines to show; when omitted,
            built-in defaults are used.

    Returns:
        A list of strings to be printed, one per line.
    """
    lines = message_lines if message_lines is not None else DEFAULT_FLAGGED_MESSAGE_LINES
    rendered = [""]
    for line in lines:
        rendered.append(f"{_RED}  {line}  {_RESET}")
    rendered.append("")
    return rendered


def format_duplicate_banner(case_number: str) -> list:
    """
    Return the lines to print when a consecutive duplicate barcode is scanned.

    Displays a calm green reassurance message so the volunteer knows nothing
    went wrong and can continue processing the next customer.

    Args:
        case_number: The normalized case number that was scanned twice in a row.

    Returns:
        A list of strings to be printed, one per line.
    """
    return [
        "",
        f"{_GREEN}  Duplicate scan — proceed to next customer  {_RESET}",
        "",
    ]


def format_already_served_banner(case_number: str) -> list:
    """
    Return the lines to print when a barcode is re-scanned that was already
    recorded earlier in the current session (non-consecutive duplicate).

    Uses the same red background and visual treatment as format_flag_banner.

    Args:
        case_number: The normalized case number that was scanned again.

    Returns:
        A list of strings to be printed, one per line.
    """
    return [
        "",
        f"{_RED}  ALREADY SERVED — DO NOT ISSUE: {case_number}  {_RESET}",
        f"{_RED}  This barcode has been serviced earlier today  {_RESET}",
        "",
    ]
