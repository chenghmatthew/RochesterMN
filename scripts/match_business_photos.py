"""Match the photo files in a folder to the businesses in the Business Inventory workbook, by business name.

Photo filenames are informal ("franciscos.jpg", "kahler.png", "mayo clinic1-10 145024.png"), so matching is fuzzy
and the result is a CSV to REVIEW, not something to trust blindly:

    py scripts/match_business_photos.py "C:/.../Downtown Rochester Business Inventory 20261104.xlsm" "C:/.../Business Photos"

Writes data/photo-matches.csv with one row per photo: the best business guess, a score, a confidence label
(high / review / none) and the runners-up. Fix any wrong row by editing the 'business' column in the CSV, or pin
a photo permanently in data/photo-overrides.csv (columns: photo, business; leave business blank to say
"this photo belongs to no business"). Overrides always win and are never overwritten.

Only business names are read from the workbook (the 'Business name' column; 'Business ID' too if present).
Photos in sub-folders are included; the sub-folder name (e.g. "507 Social") counts as a name hint.
Nothing is copied or uploaded: this script only reads.
"""

import argparse
import csv
import re
import shutil
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "photo-matches.csv"
OVERRIDES_PATH = ROOT / "data" / "photo-overrides.csv"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
HIGH, REVIEW = 0.85, 0.60  # score thresholds for the confidence label
TIE_GAP = 0.05  # a runner-up this close to the best score makes the match "review" instead of "high"

# Words that say nothing about which business it is.
STOP = {"the", "and", "of", "at", "by", "in", "inc", "llc", "co", "company", "rochester", "mn", "mayo", "clinic",
        "area", "logo", "photo", "image", "images", "primary", "building", "retina", "web", "stacked", "color",
        "rgb", "horizontal"}


def tokens(text):
    """Lower-case word tokens: apostrophes dropped ("Francisco's" -> "franciscos"), camelCase split, digits dropped."""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)  # "CarollsCorn" -> "Carolls Corn"
    text = re.sub(r"['\u2019\ufffd]", "", text.lower())
    return [t for t in re.findall(r"[a-z]+", text) if t not in STOP and len(t) > 1]


def photo_tokens(path, root):
    parts = [path.stem] + [p for p in path.relative_to(root).parent.parts]
    return tokens(" ".join(parts))


def token_score(a, b):
    """How well token a (from the photo) matches token b (from the business name)."""
    if a == b:
        return 1.0
    if len(a) >= 4 and (b.startswith(a) or a.startswith(b)):  # "kahler" ~ "kahlers", "nietz" ~ "nietzs"
        return 0.9
    return SequenceMatcher(None, a, b).ratio() if min(len(a), len(b)) >= 4 else 0.0


def score(photo, name):
    """0..1. Every photo token should find a partner in the name; a name with many unmatched words scores a bit lower."""
    if not photo or not name:
        return 0.0
    best = []
    for p in photo:
        s = max(token_score(p, n) for n in name)
        best.append(s if s >= 0.75 else 0.0)
    coverage = sum(best) / len(best)  # how much of the filename is explained by the name
    joined = SequenceMatcher(None, "".join(photo), "".join(name)).ratio()  # catches "cafe steam" vs "cafesteam"
    base = max(coverage, joined)
    unmatched_name = 1 - sum(1 for n in name if any(token_score(p, n) >= 0.75 for p in photo)) / len(name)
    return round(base - 0.1 * unmatched_name * (base > 0), 3)  # tie-break toward the tighter name


def read_businesses(workbook_path):
    # Read a temporary copy so the workbook is never touched.
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "inventory.xlsm"
        try:
            shutil.copyfile(workbook_path, copy)
        except PermissionError:
            sys.exit(f"Can't read {workbook_path.name} (locked, usually because it is open in Excel or still syncing "
                     "from OneDrive). Close it, or copy the file somewhere else and pass that copy.")
        wb = load_workbook(copy, read_only=True, data_only=True)
        sheet = next((n for n in wb.sheetnames if n.strip().lower() in ("business", "businesses")), None)
        if sheet is None:
            sys.exit(f"No 'Business' tab in {workbook_path.name}. Tabs: {', '.join(wb.sheetnames)}")
        rows = list(wb[sheet].iter_rows(values_only=True))
        wb.close()
    head = next((i for i, r in enumerate(rows) if any(str(c or "").strip().lower() == "business name" for c in r)), None)
    if head is None:
        sys.exit("Couldn't find a 'Business name' header row.")
    headers = [str(c or "").strip().lower() for c in rows[head]]
    name_col = headers.index("business name")
    id_col = headers.index("business id") if "business id" in headers else None
    seen, out = set(), []
    for r in rows[head + 1:]:
        name = str(r[name_col] or "").strip()
        if name and name not in seen:  # a few businesses appear on several rows; one entry is enough
            seen.add(name)
            out.append({"name": name, "id": str(r[id_col] or "").strip() if id_col is not None else "", "tok": tokens(name)})
    return out


def read_overrides():
    if not OVERRIDES_PATH.exists():
        return {}
    with open(OVERRIDES_PATH, newline="", encoding="utf-8-sig") as f:
        return {row["photo"].strip(): row["business"].strip() for row in csv.DictReader(f)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workbook", type=Path)
    parser.add_argument("photos", type=Path, help="folder of business photos (sub-folders included)")
    args = parser.parse_args()

    businesses = read_businesses(args.workbook)
    overrides = read_overrides()
    photos = sorted(p for p in args.photos.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
    print(f"{len(businesses)} businesses, {len(photos)} photos, {len(overrides)} overrides")

    OUT_PATH.parent.mkdir(exist_ok=True)
    counts = {"high": 0, "review": 0, "none": 0, "override": 0}
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig so Excel opens it cleanly
        out = csv.writer(f)
        out.writerow(["photo", "business", "business_id", "score", "confidence", "also_considered"])
        for photo in photos:
            rel = photo.relative_to(args.photos).as_posix()
            ranked = sorted(((score(photo_tokens(photo, args.photos), b["tok"]), b) for b in businesses),
                            key=lambda x: -x[0])
            top_score, top = ranked[0]
            others = "; ".join(f"{b['name']} ({s})" for s, b in ranked[1:4] if s >= REVIEW)
            if rel in overrides:
                chosen = next((b for b in businesses if b["name"] == overrides[rel]), None)
                out.writerow([rel, overrides[rel], chosen["id"] if chosen else "", "", "override", ""])
                counts["override"] += 1
            elif top_score >= REVIEW:
                tie = len(ranked) > 1 and top_score - ranked[1][0] < TIE_GAP  # e.g. "kahler" fits two businesses
                label = "high" if top_score >= HIGH and not tie else "review"
                out.writerow([rel, top["name"], top["id"], top_score, label, others])
                counts[label] += 1
            else:
                out.writerow([rel, "", "", top_score, "none", f"closest: {top['name']}"])
                counts["none"] += 1
    print(f"high {counts['high']}, review {counts['review']}, no match {counts['none']}, override {counts['override']}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
