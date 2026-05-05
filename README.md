# FoodPantryListGenerator

A barcode scanning tool used at the St. Andrew's food pantry to log case numbers as customers enter the shopping area. Volunteers scan each customer's ID card barcode; the program records the case numbers to a CSV file that is later merged with the Oasis pantry assistance report.

## For volunteers

See [docs/VolunteerInstructions.md](docs/VolunteerInstructions.md) for step-by-step instructions including how to start the program, scan barcodes, handle problem situations, and transfer the file at the end of pantry.

## How it works

1. Double-click the **FoodPantry ListGenerator** icon on the desktop.
2. The program opens and shows the output filename and how many records are already saved.
3. Scan each customer's barcode. The case number appears on screen after each scan.
4. To exit, press **Enter** on a blank scan prompt.
5. At the end of pantry, copy the output file from `C:\DoubleCheck\` to the thumb drive.

The output file is a CSV named `scanned_barcodes20YYMMDD.csv` (e.g. `scanned_barcodes20260504.csv`), saved to `C:\DoubleCheck\`. If any barcodes were flagged during the session, a second file named `flagged_barcodes20YYMMDD.csv` is also written to `C:\DoubleCheck\` — it records the flagged case numbers and the times they were scanned, for the administrator's review.

## For developers

See [docs/DeveloperReadme.md](docs/DeveloperReadme.md) for setup instructions, project structure, how to run tests, and how to build and deploy a new release.
