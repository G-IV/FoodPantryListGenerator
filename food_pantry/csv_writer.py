"""
csv_writer.py — Output file management

This module manages the CSV file that accumulates scanned case numbers
over the course of a pantry day.

Output file format
------------------
Filename:  scanned_barcodes20YYMMDD.csv  (e.g. scanned_barcodes20260504.csv)
Location:  The program's working directory.
           In production this is C:\\DoubleCheck\\ because the desktop
           shortcut has its "Start in" field set to that directory.
           See docs/DeveloperReadme.md for deployment details.

Each row written to the file has 6 fields:

    Field 1:    Case number     e.g. C1052089
    Fields 2-5: Empty           Reserved for the Oasis report merge
    Field 6:    Timestamp       e.g. 1/5/2026 9:07

Example row:
    C1052089,,,,,1/5/2026 9:07

Why the empty fields?
---------------------
The output file is designed to be merged with the Oasis pantry assistance
report. The empty fields align with columns in that report. Do not remove
them or change their count without confirming the merge process still works
with Tina or whoever is responsible for the downstream report.

Append behavior
---------------
The file is opened in append mode so that data is never lost if the program
is closed and reopened mid-pantry (e.g. if the screen goes dark and the
volunteer accidentally opens a second window — see the Double Screen Problem
section in docs/VolunteerInstructions.md). On startup, the program counts
rows already in the file so the record counter resumes from where it left off.
"""

import datetime
import os
from typing import Optional


def build_output_filename(date: datetime.date) -> str:
    """
    Return the dated CSV filename for a given date.

    The filename format matches the original C implementation exactly to
    preserve compatibility with any downstream processes that rely on the
    naming convention.

    Args:
        date: The date to embed in the filename.

    Returns:
        Filename string, e.g. "scanned_barcodes20260504.csv"

    Examples:
        >>> import datetime
        >>> build_output_filename(datetime.date(2026, 5, 4))
        'scanned_barcodes20260504.csv'
        >>> build_output_filename(datetime.date(2026, 12, 31))
        'scanned_barcodes20261231.csv'
    """
    return f"scanned_barcodes20{date.strftime('%y%m%d')}.csv"


def format_timestamp(dt: datetime.datetime) -> str:
    """
    Format a datetime as a non-zero-padded timestamp string.

    This matches the intent of the original C implementation. The original
    had a stray space before the hour (a bug in the C format string
    "%d/%d/%d% d:%d") — that bug is intentionally NOT replicated here.
    Minutes are zero-padded to two digits for readability.

    The string is built manually rather than using strftime to avoid a
    platform difference: non-zero-padded day/month requires "%-m" on
    Linux/macOS but "%#m" on Windows. Manual formatting is portable.

    Args:
        dt: The datetime to format.

    Returns:
        Formatted string, e.g. "1/5/2026 9:07"

    Examples:
        >>> import datetime
        >>> format_timestamp(datetime.datetime(2026, 1, 5, 9, 7))
        '1/5/2026 9:07'
        >>> format_timestamp(datetime.datetime(2026, 12, 25, 14, 30))
        '12/25/2026 14:30'
        >>> format_timestamp(datetime.datetime(2026, 1, 1, 0, 0))
        '1/1/2026 0:00'
    """
    return f"{dt.month}/{dt.day}/{dt.year} {dt.hour}:{dt.minute:02d}"


def count_existing_records(filepath: str) -> int:
    """
    Count the number of data rows already in the CSV file.

    Called at program startup so the volunteer can see how many barcodes
    have already been recorded. This supports the use case where the program
    is closed and reopened mid-pantry — the record counter picks up where
    it left off rather than restarting from 1.

    Args:
        filepath: Absolute or relative path to the CSV file.

    Returns:
        Number of rows in the file, or 0 if the file does not exist yet.
    """
    if not os.path.exists(filepath):
        return 0

    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def append_record(
    filepath: str,
    case_number: str,
    timestamp: datetime.datetime,
) -> None:
    """
    Append a single scanned record to the CSV file.

    Opens the file in append mode so existing records are never overwritten.
    Creates the file if it does not exist yet.

    Args:
        filepath:    Absolute or relative path to the CSV file.
        case_number: Normalized case number, e.g. "C1052089".
        timestamp:   The datetime at which the barcode was scanned.
    """
    ts = format_timestamp(timestamp)

    with open(filepath, "a", encoding="utf-8") as f:
        # Five commas produce the four empty fields required for the
        # downstream Oasis report merge. See module docstring for details.
        f.write(f"{case_number},,,,, {ts}\n")


def build_flagged_filename(date: datetime.date) -> str:
    """
    Return the dated CSV filename for the flagged-barcode log.

    The filename mirrors the scanned_barcodes naming convention so both
    files for a given day sort together in the C:\\DoubleCheck\\ folder.

    Args:
        date: The date to embed in the filename.

    Returns:
        Filename string, e.g. "flagged_barcodes20260504.csv"

    Examples:
        >>> import datetime
        >>> build_flagged_filename(datetime.date(2026, 5, 4))
        'flagged_barcodes20260504.csv'
    """
    return f"flagged_barcodes20{date.strftime('%y%m%d')}.csv"


def append_flagged_record(
    filepath: str,
    case_number: str,
    timestamp: datetime.datetime,
) -> None:
    """
    Append a single flagged-barcode record to the flagged log CSV.

    Opens the file in append mode so existing records are never overwritten.
    Creates the file if it does not exist yet.

    The flagged log uses the same two-column layout as the scanned log
    (Case #, Timestamp) but without the empty Oasis merge columns, since
    this file is for Tina's review only and is not merged into Oasis.

    Args:
        filepath:    Absolute or relative path to the flagged log CSV.
        case_number: Normalized case number, e.g. "C1052089".
        timestamp:   The datetime at which the barcode was scanned.
    """
    ts = format_timestamp(timestamp)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{case_number},{ts}\n")


def read_last_case_number(filepath: str, today: datetime.date) -> Optional[str]:
    """
    Return the case number from the last row of today's output file, or None.

    Used to seed last_scanned on startup so consecutive duplicate detection
    works correctly when the application is closed and reopened mid-session.

    Only reads from the file if its filename matches today's expected output
    filename — this prevents seeding from a previous pantry day's file.

    Args:
        filepath: Absolute or relative path to the output CSV file.
        today:    The current date, used to verify the file is from today.

    Returns:
        The case number string from the last row (e.g. "C1052089"), or None
        if the file does not exist, is from a different date, or is empty.
    """
    expected_name = build_output_filename(today)
    if os.path.basename(filepath) != expected_name:
        return None
    if not os.path.exists(filepath):
        return None
    last_line = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if last_line is None:
        return None
    case_number = last_line.split(",")[0].strip()
    return case_number or None


def read_existing_case_numbers(filepath: str, today: datetime.date) -> set:
    """
    Return the set of all case numbers already recorded in today's output file.

    Used at startup to seed the session-level duplicate guard.  Every barcode
    that was written to the file earlier in today's session (or in a previous
    run on the same day) is included so that re-scanning any of them triggers
    the ALREADY SERVED alert rather than recording the barcode again.

    Only reads from the file if its filename matches today's expected output
    filename — this prevents seeding from a previous pantry day's file.

    Args:
        filepath: Absolute or relative path to the output CSV file.
        today:    The current date, used to verify the file is from today.

    Returns:
        A set of case number strings (e.g. {"C1052089", "C1052090"}).
        Returns an empty set if the file does not exist, is from a different
        date, or contains no rows.
    """
    expected_name = build_output_filename(today)
    if os.path.basename(filepath) != expected_name:
        return set()
    if not os.path.exists(filepath):
        return set()
    case_numbers: set = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                case_number = stripped.split(",")[0].strip()
                if case_number:
                    case_numbers.add(case_number)
    return case_numbers
