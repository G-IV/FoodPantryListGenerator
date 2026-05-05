"""
food_pantry — Core package for FoodPantryListGenerator

This package contains all business logic for the Food Pantry barcode
scanning application. It is intentionally separated from the entry point
(FoodPantryListGenerator.py) so that each module can be tested
independently without running the full application.

Package structure
-----------------
scanner.py      Parses raw barcode input into normalized case numbers.
csv_writer.py   Manages the output CSV file (creation, counting, appending).

Future modules (not yet implemented) should be added here as the
application grows. See GitHub Issues for the current roadmap.
"""

__version__ = "2.1.0"
