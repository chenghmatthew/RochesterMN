"""Update the map's business list from the 'Business' tab of the Downtown Rochester Business Inventory workbook.

Download the workbook from SharePoint first (the script reads a local file; it never logs in to SharePoint):

    py scripts/load_business_data.py "C:/Users/you/Downloads/Downtown Rochester Business Inventory 20261008.xlsm"
    py scripts/load_business_data.py --dry-run   # uses the newest workbook in data/ and only prints what would change

Workbook categories are grouped into the map's three filter chips (Food & drink, Lodging, Retail & services).

Only these workbook columns are read (header names are matched loosely, any column can be missing):
    Business ID, Business name, Category, Subcategory, Description, Latitude, Longitude

They are written into the matching business in data/whats-open-data.js (matched by ID, then by name).
Every other field (hours, access notes, routes, ...) is left exactly as it is, so the page keeps working.
Businesses that are not in the data yet are added when they have a name and coordinates.
Empty cells never overwrite existing values. The same data is re-embedded in index.html so the page
works when opened straight from disk.
"""

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "whats-open-data.js"
INDEX_PATH = ROOT / "index.html"
DATA_ASSET_ID = "3034f34b-feb9-42c3-9850-f74ec9e5cc0e"  # bundled copy of whats-open-data.js
SHEET_NAMES = ("Business", "Businesses")

# Workbook header (lower case) -> field in whats-open-data.js
COLUMNS = {
    "id": ("business id", "id"),
    "name": ("business name", "name"),
    "category": ("category", "categories"),
    "subcategory": ("subcategory",),
    "description": ("description", "description from site"),
    "lat": ("latitude", "lat"),
    "lng": ("longitude", "lng", "long", "lon"),
}
# The map has three filter chips. Workbook categories are grouped into them; the original wording is kept
# in the business's "category" field for display and search.
CHIP_FOR_CATEGORY = {"food and drink": "Food & drink", "fast food": "Food & drink", "lodging": "Lodging"}
DEFAULT_CHIP = "Retail & services"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean(value):
    """Cell value as stripped text; '' for blanks."""
    return "" if value is None else str(value).strip()


def to_coord(value, low, high):
    """Cell value as a coordinate, or None when it is blank, text like 'Not geocoded', or out of range."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 6) if low <= number <= high else None


def read_sheet(path):
    """Yield one dict per business row, using only the columns that exist."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet_name = next((n for n in workbook.sheetnames if n.strip().lower() in [s.lower() for s in SHEET_NAMES]), None)
    if sheet_name is None:
        sys.exit(f"No 'Business' tab in {path.name}. Tabs found: {', '.join(workbook.sheetnames)}")
    rows = list(workbook[sheet_name].iter_rows(values_only=True))
    header_at = next((i for i, row in enumerate(rows) if any(clean(c).lower() in COLUMNS["name"] for c in row)), None)
    if header_at is None:
        sys.exit(f"Couldn't find a 'Business name' header row on the '{sheet_name}' tab.")
    headers = [clean(c).lower() for c in rows[header_at]]
    index = {}
    for field, names in COLUMNS.items():
        for name in names:
            if name in headers:
                index[field] = headers.index(name)
                break
    print(f"Reading '{sheet_name}' tab of {path.name}; columns found: {', '.join(sorted(index))}")
    missing = sorted(set(COLUMNS) - set(index))
    if missing:
        print(f"  (not in the workbook, left unchanged: {', '.join(missing)})")
    for row in rows[header_at + 1:]:
        record = {f: (row[i] if i < len(row) else None) for f, i in index.items()}
        if clean(record.get("name")):
            yield record


def chips(text, existing):
    """Filter-chip categories for a workbook category ('Food and drink; Lodging' gives both).
    A business keeps its extra chips (e.g. a hotel with a restaurant) while its main chip is unchanged."""
    found = []
    for part in re.split(r"[;|]", text):
        chip = CHIP_FOR_CATEGORY.get(part.strip().lower(), DEFAULT_CHIP)
        if part.strip() and chip not in found:
            found.append(chip)
    if len(found) == 1 and found[0] in existing:
        return existing
    return found


def find_business(businesses, record):
    wanted_id, wanted_name = clean(record.get("id")), clean(record["name"])
    for b in businesses:
        if wanted_id and b["id"] == wanted_id:
            return b
    for b in businesses:
        if slug(b["name"]) == slug(wanted_name):
            return b
    return None


def apply_record(business, record):
    """Copy non-empty workbook values onto the business. Returns the list of fields that changed."""
    updates = {}
    for field in ("name", "category", "subcategory", "description"):
        value = clean(record.get(field))
        if value:
            updates[field] = value
    if updates.get("category"):
        updates["cats"] = chips(updates["category"], business.get("cats", []))
    lat, lng = to_coord(record.get("lat"), -90, 90), to_coord(record.get("lng"), -180, 180)
    if lat is not None and lng is not None:  # only ever set the pair together
        updates["lat"], updates["lng"] = lat, lng
    changed = [k for k, v in updates.items() if business.get(k) != v]
    business.update(updates)
    return changed


def load_data():
    text = DATA_PATH.read_text(encoding="utf-8")
    start = text.index("window.WHATS_OPEN_DATA")
    header = text[:start]
    body = text[text.index("{", start):text.rindex("}") + 1]
    return header, json.loads(body)


def render_data(header, data):
    # Same layout the generator uses (JSON.stringify(data, null, 1)), so unchanged data gives an unchanged file.
    return header + "window.WHATS_OPEN_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"


def embed_in_index(js_text):
    """Replace the bundled copy of whats-open-data.js in index.html's manifest."""
    lines = INDEX_PATH.read_text(encoding="utf-8").split("\n")
    at = next(i for i, line in enumerate(lines) if '<script type="__bundler/manifest">' in line) + 1
    manifest = json.loads(lines[at])
    manifest[DATA_ASSET_ID] = {
        "mime": "application/javascript",
        "compressed": True,
        "data": base64.b64encode(gzip.compress(js_text.encode("utf-8"), mtime=0)).decode(),
    }
    lines[at] = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\u002F")
    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines))


def newest_workbook():
    found = sorted((ROOT / "data").glob("*Business Inventory*.xls[xm]"), key=lambda p: p.name)
    if not found:
        sys.exit("No workbook given and none found in data/. Pass the downloaded .xlsm path.")
    return found[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workbook", nargs="?", type=Path, help="downloaded .xlsx/.xlsm (default: newest in data/)")
    parser.add_argument("--dry-run", action="store_true", help="show the changes without writing any file")
    args = parser.parse_args()

    workbook = args.workbook or newest_workbook()
    header, data = load_data()
    businesses = data["businesses"]
    added = updated = skipped = 0
    for record in read_sheet(workbook):
        business = find_business(businesses, record)
        if business:
            changed = apply_record(business, record)
            if changed:
                updated += 1
                print(f"  updated {business['name']}: {', '.join(changed)}")
        elif to_coord(record.get("lat"), -90, 90) is not None and to_coord(record.get("lng"), -180, 180) is not None:
            business = {"id": clean(record.get("id")) or slug(clean(record["name"])), "name": clean(record["name"]),
                        "status": "Open during construction", "cats": []}
            apply_record(business, record)
            businesses.append(business)
            added += 1
            print(f"  added   {business['name']}")
        else:
            skipped += 1
            print(f"  skipped {clean(record['name'])}: new business without latitude/longitude (can't be placed on the map)")
    print(f"{updated} updated, {added} added, {skipped} skipped, {len(businesses)} businesses total")
    if args.dry_run:
        print("Dry run: no files written.")
        return
    js_text = render_data(header, data)
    DATA_PATH.write_text(js_text, encoding="utf-8", newline="")
    embed_in_index(js_text)
    print(f"Wrote {DATA_PATH.name} and re-embedded it in {INDEX_PATH.name}")


if __name__ == "__main__":
    main()
