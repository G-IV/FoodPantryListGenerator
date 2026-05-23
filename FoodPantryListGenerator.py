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
    append_flagged_record,
    append_record,
    build_flagged_filename,
    build_output_filename,
    count_existing_records,
    read_existing_case_numbers,
    read_last_case_number,
)
from food_pantry.invalid_numbers import (
    ensure_invnmbrs_exists,
    format_already_served_banner,
    format_duplicate_banner,
    format_flag_banner,
    read_admin_contact,
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
    invnmbrs_path = os.path.join(os.getcwd(), "InvNmbrs.csv")
    error_log_path = os.path.join(os.getcwd(), "InvNmbrs_errors.log")

    created = ensure_invnmbrs_exists(invnmbrs_path)
    validate_and_clean_invnmbrs(invnmbrs_path, error_log_path)

    record_count = count_existing_records(filepath)
    last_scanned = read_last_case_number(filepath, today)
    today_scanned_set = read_existing_case_numbers(filepath, today)
    flagged_set = read_invalid_numbers(invnmbrs_path)
    flagged_mtime = os.path.getmtime(invnmbrs_path)

    print(f"Output file:  {filename}")
    print(f"Records already in file: {record_count}")
    print(f"Source code:  https://github.com/G-IV/FoodPantryListGenerator")
    if created:
        print()
        print("NOTE: InvNmbrs.csv was not found and has been created automatically.")
        print("      Please open C:\\DoubleCheck\\InvNmbrs.csv in Notepad and update")
        print("      line 1 with the Oasis Administrator's name and phone number.")
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
        current_mtime = os.path.getmtime(invnmbrs_path)
        if current_mtime != flagged_mtime:
            flagged_set = read_invalid_numbers(invnmbrs_path)
            flagged_mtime = current_mtime

        # Check 2: blocked by administrator.
        if case_number in flagged_set:
            contact = read_admin_contact(invnmbrs_path)
            now = datetime.datetime.now()
            append_flagged_record(flagged_filepath, case_number, now)
            for line in format_flag_banner(case_number, contact):
                print(line)
            continue

        # Check 3: scanned earlier this session (not the immediately prior scan).
        if case_number in today_scanned_set and case_number != last_scanned:
            contact = read_admin_contact(invnmbrs_path)
            now = datetime.datetime.now()
            append_flagged_record(flagged_filepath, case_number, now)
            for line in format_already_served_banner(case_number, contact):
                print(line)
            continue

        # Check 4: same barcode as the very last scan (consecutive duplicate).
        if case_number == last_scanned:
            # Re-apply checks 2 and 3 in case status changed mid-session.
            # (In practice check 2 was just evaluated above with a fresh
            # flagged_set, and check 3 is logically False when
            # case_number == last_scanned — both are included per spec.)
            if case_number in flagged_set:
                contact = read_admin_contact(invnmbrs_path)
                now = datetime.datetime.now()
                append_flagged_record(flagged_filepath, case_number, now)
                for line in format_flag_banner(case_number, contact):
                    print(line)
                continue
            if case_number in today_scanned_set and case_number != last_scanned:
                contact = read_admin_contact(invnmbrs_path)
                for line in format_already_served_banner(case_number, contact):
                    print(line)
                continue
            # Both re-checks passed — genuine consecutive duplicate scan.
            contact = read_admin_contact(invnmbrs_path)
            for line in format_duplicate_banner(case_number, contact):
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
