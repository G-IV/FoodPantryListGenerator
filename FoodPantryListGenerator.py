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

from food_pantry.csv_writer import append_record, build_output_filename, count_existing_records
from food_pantry.scanner import parse_barcode


def main() -> None:
    today = datetime.date.today()
    filename = build_output_filename(today)

    # The output file is written to the current working directory.
    # In production the desktop shortcut sets "Start in" to C:\DoubleCheck\
    # so the file lands there automatically.
    # See docs/DeveloperReadme.md → Deployment for details.
    filepath = os.path.join(os.getcwd(), filename)

    record_count = count_existing_records(filepath)

    print(f"Output file:  {filename}")
    print(f"Records already in file: {record_count}")
    print()
    print("Scan a barcode, or press Enter to exit.")
    print()

    while True:
        record_count += 1
        raw = input(f"Record {record_count} — Please scan a barcode: ")

        case_number = parse_barcode(raw)

        if case_number is None:
            # Blank input — volunteer pressed Enter to exit.
            break

        now = datetime.datetime.now()
        append_record(filepath, case_number, now)

    print()
    print(f"Barcodes saved to: {filename}")


if __name__ == "__main__":
    main()
