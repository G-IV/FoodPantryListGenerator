# Test Fixtures

Synthetic datasets for developing and testing the comparison feature (Issue #2).
All names and case numbers are fabricated — no real pantry data is stored here.

For full documentation of both file formats, the ideal-state definition, and the
complete scenario catalogue, see the
[Data formats](../../docs/DeveloperReadme.md#data-formats) section of the
Developer README.

---

## Scenario key

Each scenario is identified by its case-number prefix. Use this table when
writing tests to find the rows that exercise a specific scenario.

| Case range | Scenario |
|------------|----------|
| C1100001–C1100035 | Clean match — once in each file |
| C1200001–C1200003 | Once in scanned, multiple in Oasis |
| C1300001–C1300003 | Multiple in scanned, once in Oasis |
| C1400001–C1400002 | Multiple in both |
| C1500001–C1500003 | Scanned only (once) |
| C1600001–C1600005 | Oasis only (once) |
| C1700001–C1700002 | Multiple in scanned only |
| C1800001–C1800002 | Multiple in Oasis only |
