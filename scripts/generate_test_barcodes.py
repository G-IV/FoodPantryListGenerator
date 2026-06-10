"""
Generate a printable Code 128 barcode test sheet from sample_scanned_barcodes.csv.

Usage:
    python scripts/generate_test_barcodes.py

Output:
    tests/fixtures/test_barcodes.html

Each barcode encodes the numeric portion of the case number only (no 'C' prefix),
which matches the raw value the Tera D5100 scanner reads from physical Oasis client
cards.  The 'C' prefix is added by scanner.py after stripping the scanner's own
{[C]…} wrapper and any leading zeros.
"""

import csv
import io
import os
import re
import sys

import barcode
from barcode.writer import SVGWriter

# ---------------------------------------------------------------------------
# Paths (relative to repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_CSV = os.path.join(REPO_ROOT, "tests", "fixtures", "sample_scanned_barcodes.csv")
INVNMBRS_CSV = os.path.join(REPO_ROOT, "tests", "fixtures", "InvNmbrs.csv")
OUTPUT_HTML = os.path.join(REPO_ROOT, "tests", "manual_tests", "test_barcodes.html")

# Section order and labels — must match the floating nav in the generated HTML.
# Each tuple: (case-number prefix, display label, anchor id)
SECTIONS = [
    ("C11", "Clean match — once in scanned, once in Oasis",   "c11"),
    ("C13", "Multiple in scanned, once in Oasis",             "c13"),
    ("C17", "Multiple in scanned only",                       "c17"),
    ("C15", "Scanned only (not in Oasis)",                    "c15"),
    ("C14", "Multiple in both scanned and Oasis",             "c14"),
    ("C12", "Once in scanned, multiple in Oasis",             "c12"),
]


def barcode_svg(value: str) -> str:
    """Return an inline SVG string for a Code 128 barcode encoding *value*.

    The hardcoded width/height attributes are replaced with a viewBox so that
    CSS can freely resize the element.
    """
    writer = SVGWriter()
    code = barcode.Code128(value, writer=writer)
    buf = io.BytesIO()
    code.write(buf, options={"write_text": True, "module_height": 12.0, "font_size": 8})
    svg_str = buf.getvalue().decode("utf-8")

    # Extract width and height in mm so we can build a viewBox.
    # The SVG writer emits values like: width="23.080mm" height="23.411mm"
    w_match = re.search(r'<svg[^>]*\swidth="([\d.]+)mm"', svg_str)
    h_match = re.search(r'<svg[^>]*\sheight="([\d.]+)mm"', svg_str)
    if w_match and h_match:
        w_mm = float(w_match.group(1))
        h_mm = float(h_match.group(1))
        # Replace the opening <svg …> tag: remove fixed dimensions, add viewBox.
        svg_str = re.sub(
            r'(<svg\b[^>]*?)\s+width="[\d.]+mm"\s+height="[\d.]+mm"',
            rf'\1 viewBox="0 0 {w_mm} {h_mm}"',
            svg_str,
        )
        # Strip 'mm' unit suffixes from all attribute values so element
        # coordinates are unitless user units that align with the viewBox.
        svg_str = re.sub(r'((?:x|y|width|height|x1|y1|x2|y2)="[\d.]+)mm"', r'\1"', svg_str)
        # Replace absolute font-size (e.g. 8pt) with a user-unit value so the
        # text scales in proportion with the bars as the SVG is resized.
        svg_str = re.sub(r'font-size:[\d.]+pt', 'font-size:2', svg_str)

    # Drop the XML declaration and DOCTYPE lines so it embeds cleanly in HTML.
    lines = [l for l in svg_str.splitlines() if not l.startswith("<?xml")]
    return "\n".join(lines)


def load_case_numbers(csv_path: str) -> list[str]:
    """Return deduplicated, sorted case numbers from the first column."""
    seen: set[str] = set()
    ordered: list[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            value = row[0].strip()
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
    return ordered


def load_flagged_numbers(csv_path: str) -> set[str]:
    """Return the set of flagged case numbers from InvNmbrs.csv.

    Skips the header row ('Case #') and any non-case-number rows gracefully.
    Returns an empty set if the file does not exist.
    """
    flagged: set[str] = set()
    if not os.path.isfile(csv_path):
        return flagged
    pattern = re.compile(r"^C\d+$")
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for line in fh:
            value = line.strip().rstrip(",")
            if pattern.match(value):
                flagged.add(value)
    return flagged


def numeric_part(case_number: str) -> str:
    """Strip the leading 'C' from a case number like C1100001 → '1100001'."""
    return case_number.lstrip("C").lstrip("c")


# ---------------------------------------------------------------------------
# HTML template helpers
# ---------------------------------------------------------------------------
HTML_HEAD = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Food Pantry – Barcode Test Sheet</title>
  <style>
    body  { font-family: Arial, sans-serif; margin: 20px; padding-left: 175px; }
    h1    { font-size: 16px; margin-bottom: 4px; }
    p.sub { font-size: 11px; color: #555; margin-top: 0; margin-bottom: 16px; }
    .grid { display: flex; flex-direction: column; align-items: center; gap: 12px; }

    /* ── Section heading ── */
    .section-heading {
      width: 500px;
      font-size: 13px;
      font-weight: bold;
      color: #333;
      border-bottom: 2px solid #bbb;
      padding: 12px 0 4px;
      margin-top: 4px;
      text-align: left;
    }
    .section-heading .range {
      font-weight: normal;
      color: #888;
      font-size: 11px;
      margin-left: 8px;
    }

    /* ── Barcode card ── */
    .card {
      padding: 6px 10px;
      text-align: center;
    }
    .card svg { width: 500px; height: 350px; }
    .card .label {
      font-size: 11px;
      font-weight: bold;
      margin-bottom: 4px;
      color: #333;
    }
    .card.flagged .label { color: #a93226; }
    .flagged-badge {
      display: inline-block;
      background: #a93226;
      color: #fff;
      font-size: 9px;
      font-weight: bold;
      padding: 1px 5px;
      border-radius: 3px;
      margin-left: 6px;
      vertical-align: middle;
      letter-spacing: 0.04em;
    }

    /* ── Floating section nav ── */
    #section-nav {
      position: fixed;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      background: #fff;
      border: 1px solid #ccc;
      border-left: none;
      border-radius: 0 6px 6px 0;
      box-shadow: 2px 2px 8px rgba(0,0,0,0.12);
      padding: 10px 0;
      z-index: 100;
      min-width: 158px;
    }
    #section-nav p {
      font-size: 10px;
      font-weight: bold;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin: 0 0 6px 12px;
      padding: 0;
    }
    #section-nav a {
      display: block;
      padding: 6px 12px;
      font-size: 12px;
      text-decoration: none;
      color: #333;
      line-height: 1.4;
    }
    #section-nav a:hover { background: #f0f4ff; color: #1a56db; }
    #section-nav a .range { display: block; font-size: 10px; color: #888; }

    @media print {
      body { margin: 8px; padding-left: 8px; }
      h1, p.sub, #section-nav { display: none; }
      .card { break-inside: avoid; }
      .section-heading { break-after: avoid; }
    }
  </style>
</head>
<body>

  <nav id="section-nav">
    <p>Jump to</p>
    <a href="#c11">Clean match<span class="range">C11xxxxx</span></a>
    <a href="#c13">Multi-scanned, once Oasis<span class="range">C13xxxxx</span></a>
    <a href="#c17">Multi-scanned only<span class="range">C17xxxxx</span></a>
    <a href="#c15">Scanned only<span class="range">C15xxxxx</span></a>
    <a href="#c14">Multi in both<span class="range">C14xxxxx</span></a>
    <a href="#c12">Once scanned, multi Oasis<span class="range">C12xxxxx</span></a>
  </nav>

  <h1>Food Pantry List Generator – Code 128 Barcode Test Sheet</h1>
  <p class="sub">
    Each barcode encodes the <strong>numeric portion only</strong> (no&nbsp;C&nbsp;prefix).<br>
    Scan with the Tera D5100 to verify the application resolves the correct case number.<br>
    <span style="color:#a93226;font-weight:bold;">&#9873; FLAGGED</span> barcodes are in <code>tests/fixtures/InvNmbrs.csv</code> — scanning one will trigger the red alert banner.
  </p>
  <div class="grid">
"""

HTML_FOOT = """\
  </div>
</body>
</html>
"""


def main() -> None:
    case_numbers = load_case_numbers(FIXTURE_CSV)
    if not case_numbers:
        print("ERROR: no case numbers found in fixture CSV.", file=sys.stderr)
        sys.exit(1)

    flagged_set = load_flagged_numbers(INVNMBRS_CSV)

    # Group case numbers by section prefix.
    groups: dict[str, list[str]] = {prefix: [] for prefix, _, _ in SECTIONS}
    ungrouped: list[str] = []
    for cn in case_numbers:
        matched = False
        for prefix, _, _ in SECTIONS:
            if cn.startswith(prefix):
                groups[prefix].append(cn)
                matched = True
                break
        if not matched:
            ungrouped.append(cn)

    blocks: list[str] = []

    for prefix, label, anchor_id in SECTIONS:
        members = groups[prefix]
        if not members:
            continue
        # Section heading
        range_str = f"{prefix}xxxxx"
        heading = (
            f'    <div class="section-heading" id="{anchor_id}">'
            f'{label}<span class="range">{range_str}</span>'
            f'</div>'
        )
        blocks.append(heading)

        for cn in members:
            num = numeric_part(cn)
            try:
                svg = barcode_svg(num)
            except Exception as exc:
                print(f"WARNING: could not generate barcode for {cn}: {exc}", file=sys.stderr)
                continue
            is_flagged = cn in flagged_set
            card_class = 'card flagged' if is_flagged else 'card'
            badge = ' <span class="flagged-badge">&#9873; FLAGGED</span>' if is_flagged else ''
            card = (
                f'    <div class="{card_class}">\n'
                f'      <div class="label">{cn}{badge}</div>\n'
                f'      {svg}\n'
                f'    </div>'
            )
            blocks.append(card)

    # Append any case numbers that didn't match a known section prefix.
    for cn in ungrouped:
        num = numeric_part(cn)
        try:
            svg = barcode_svg(num)
        except Exception as exc:
            print(f"WARNING: could not generate barcode for {cn}: {exc}", file=sys.stderr)
            continue
        is_flagged = cn in flagged_set
        card_class = 'card flagged' if is_flagged else 'card'
        badge = ' <span class="flagged-badge">&#9873; FLAGGED</span>' if is_flagged else ''
        card = (
            f'    <div class="{card_class}">\n'
            f'      <div class="label">{cn}{badge}</div>\n'
            f'      {svg}\n'
            f'    </div>'
        )
        blocks.append(card)

    total_cards = sum(
        1 for b in blocks
        if b.strip().startswith('<div class="card')
    )
    html = HTML_HEAD + "\n".join(blocks) + "\n" + HTML_FOOT
    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    flagged_count = sum(1 for cn in case_numbers if cn in flagged_set)
    print(f"Generated {total_cards} barcodes ({flagged_count} flagged) → {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
