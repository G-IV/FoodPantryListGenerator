"""
FoodPantryListGenerator.py — Entry point

Run this script (or the compiled FoodPantryListGenerator.exe) to start a
barcode scanning session for the food pantry.

All program logic lives in the food_pantry/ package. This file only handles
the main loop, user prompts, and wiring the pieces together. Keep it thin —
if you find yourself adding logic here, it probably belongs in a module
inside food_pantry/ instead.

Usage
-----
Normal (volunteer):   Double-click FoodPantryListGenerator.exe
Development/testing:  python FoodPantryListGenerator.py

Exiting
-------
Press Enter on a blank scan prompt to end the session and close the file.
The program will display the output filename before exiting.
"""

import datetime
import os
import sys

from food_pantry.lock import acquire_lock, release_lock
from food_pantry.csv_writer import (
    append_already_served_record,
    append_flagged_record,
    append_record,
    build_already_served_filename,
    build_flagged_filename,
    build_output_filename,
    count_existing_records,
    read_existing_case_numbers,
    read_last_case_number,
)
from food_pantry.invalid_numbers import (
    ensure_flagged_message_exists,
    format_already_served_banner,
    format_duplicate_banner,
    format_flag_banner,
    read_flagged_message,
    read_invalid_numbers,
    validate_and_clean_invnmbrs,
)
from food_pantry.scanner import parse_barcode


def main() -> None:
    if not acquire_lock():
        print("FoodPantryListGenerator is already running.")
        print("Check the taskbar at the bottom of the screen and click the existing window.")
        input("\nPress Enter to close this window.")
        sys.exit(0)
    try:
        _run_session()
    finally:
        release_lock()


def _run_session() -> None:
    today = datetime.date.today()
    filename = build_output_filename(today)

    # The output file is written to the current working directory.
    # In production the desktop shortcut sets "Start in" to C:\DoubleCheck\
    # so the file lands there automatically.
    # See docs/DeveloperReadme.md → Deployment for details.
    filepath = os.path.join(os.getcwd(), filename)
    flagged_filename = build_flagged_filename(today)
    flagged_filepath = os.path.join(os.getcwd(), flagged_filename)
    already_served_filename = build_already_served_filename(today)
    already_served_filepath = os.path.join(os.getcwd(), already_served_filename)
    invnmbrs_path = os.path.join(os.getcwd(), "InvNmbrs.csv")
    error_log_path = os.path.join(os.getcwd(), "InvNmbrs_errors.log")
    flagged_message_path = os.path.join(os.getcwd(), "flagged_message.txt")

    # Create a default flagged-message file if none exists.
    ensure_flagged_message_exists(flagged_message_path)

    # Only validate/clean if the file exists; skip silently if absent.
    if os.path.isfile(invnmbrs_path):
        validate_and_clean_invnmbrs(invnmbrs_path, error_log_path)

    record_count = count_existing_records(filepath)
    last_scanned = read_last_case_number(filepath, today)
    today_scanned_set = read_existing_case_numbers(filepath, today)
    flagged_set = read_invalid_numbers(invnmbrs_path)
    flagged_mtime = os.path.getmtime(invnmbrs_path) if os.path.isfile(invnmbrs_path) else None
    flagged_message_lines = read_flagged_message(flagged_message_path)
    flagged_message_mtime = (
        os.path.getmtime(flagged_message_path) if os.path.isfile(flagged_message_path) else None
    )

    print(f"Output file:  {filename}")
    print(f"Records already in file: {record_count}")
    print(f"Recent release:  https://github.com/G-IV/FoodPantryListGenerator/releases/latest")
    print()
    print("Scan a barcode, or press Enter to exit.")
    print()

    while True:
        raw = input(f"Record {record_count + 1} — Please scan a barcode: ")

        case_number = parse_barcode(raw)

        if case_number is None:
            # Blank input — volunteer pressed Enter to exit.
            break

        # Refresh the flagged set only if InvNmbrs.csv has changed on disk.
        # If the file has appeared since startup, pick it up; if it's gone, clear the set.
        current_mtime = os.path.getmtime(invnmbrs_path) if os.path.isfile(invnmbrs_path) else None
        if current_mtime != flagged_mtime:
            flagged_set = read_invalid_numbers(invnmbrs_path)
            flagged_mtime = current_mtime

        # Refresh banner text when flagged_message.txt changes.
        current_msg_mtime = (
            os.path.getmtime(flagged_message_path) if os.path.isfile(flagged_message_path) else None
        )
        if current_msg_mtime != flagged_message_mtime:
            flagged_message_lines = read_flagged_message(flagged_message_path)
            flagged_message_mtime = current_msg_mtime

        # Check 2: blocked by administrator.
        if case_number in flagged_set:
            now = datetime.datetime.now()
            append_flagged_record(flagged_filepath, case_number, now)
            # Keep duplicate suppression aligned to the most recent scan event,
            # even when the scan is blocked as flagged.
            last_scanned = case_number
            for line in format_flag_banner(case_number, flagged_message_lines):
                print(line)
            continue

        # Check 3: consecutive duplicate (same barcode as the very last scan).
        if case_number == last_scanned:
            if case_number in flagged_set:
                now = datetime.datetime.now()
                append_flagged_record(flagged_filepath, case_number, now)
                for line in format_flag_banner(case_number, flagged_message_lines):
                    print(line)
                continue
            # Re-check passed — genuine consecutive duplicate scan.
            for line in format_duplicate_banner(case_number):
                print(line)
            continue

        # All checks passed — record the scan.
        record_count += 1
        now = datetime.datetime.now()
        append_record(filepath, case_number, now)
        today_scanned_set.add(case_number)
        last_scanned = case_number

    print()
    print(f"Barcodes saved to: {filename}")


if __name__ == "__main__":
    main()
