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

from food_pantry.csv_writer import (
    append_flagged_record,
    append_record,
    build_flagged_filename,
    build_output_filename,
    count_existing_records,
)
from food_pantry.invalid_numbers import (
    ensure_invnmbrs_exists,
    format_flag_banner,
    read_admin_contact,
    read_invalid_numbers,
    validate_and_clean_invnmbrs,
)
from food_pantry.scanner import parse_barcode


def main() -> None:
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

        status_prefix = f"  \u2192 {case_number}"
        print(f"{status_prefix}  processing...", end="\r", flush=True)

        flagged = read_invalid_numbers(invnmbrs_path)
        if case_number in flagged:
            contact = read_admin_contact(invnmbrs_path)
            now = datetime.datetime.now()
            append_flagged_record(flagged_filepath, case_number, now)
            print(f"{status_prefix}  \033[1;31m\u2717\033[0m" + "              ")
            for line in format_flag_banner(case_number, contact):
                print(line)
            continue

        record_count += 1
        now = datetime.datetime.now()
        append_record(filepath, case_number, now)
        print(f"{status_prefix}  \033[1;32m\u2713\033[0m" + "              ")

    print()
    print(f"Barcodes saved to: {filename}")


if __name__ == "__main__":
    main()
