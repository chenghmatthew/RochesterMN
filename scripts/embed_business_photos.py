"""Put the matched business photos into index.html so the cards and map popups show them.

Run scripts/match_business_photos.py first and review data/photo-matches.csv. Then:

    py scripts/embed_business_photos.py                 # high-confidence + override + 'confirmed' rows
    py scripts/embed_business_photos.py --include-review  # also use the 'review' guesses (for a quick look)
    py scripts/embed_business_photos.py --photos "C:/.../Business Photos"

Each photo is shrunk (max 640px wide, JPEG) and embedded in index.html as window.BUSINESS_PHOTOS
({business id: data URI}), because the page is opened straight from disk where separate image files
can't be loaded. One photo per business: the first matching row in the CSV. Re-running replaces the previous set.
"""

import argparse
import base64
import csv
import gzip
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.html"
DATA_PATH = ROOT / "data" / "whats-open-data.js"
MATCHES_PATH = ROOT / "data" / "photo-matches.csv"
PHOTOS_ASSET_ID = "5c1e8a40-7d3b-4f26-9a58-2b6f0c9e41d7"
SCRIPT_TAG = f'<script src="{PHOTOS_ASSET_ID}"></script>'
DEFAULT_PHOTOS = Path.home() / "OneDrive - KH" / "Downtown Rochester" / "Business Photos"
MAX_WIDTH, QUALITY = 640, 72
Image.MAX_IMAGE_PIXELS = None  # a few source photos are 11 MB camera originals


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def business_ids():
    """Map slug(name) -> business id, read from whats-open-data.js."""
    text = DATA_PATH.read_text(encoding="utf-8")
    data = json.loads(text[text.index("{", text.index("window.WHATS_OPEN_DATA")):text.rindex("}") + 1])
    return {slug(b["name"]): b["id"] for b in data["businesses"]}


def as_data_uri(path):
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA", "P"):  # logos with transparency: flatten onto white
            img = img.convert("RGBA")
            flat = Image.new("RGB", img.size, "white")
            flat.paste(img, mask=img.split()[-1])
            img = flat
        else:
            img = img.convert("RGB")
        if img.width > MAX_WIDTH:
            img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def choose_photos(include_review):
    ok = {"high", "override", "confirmed"} | ({"review"} if include_review else set())
    ids, chosen = business_ids(), {}
    with open(MATCHES_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["confidence"] not in ok or not row["business"]:
                continue
            bid = ids.get(slug(row["business"]))
            if bid is None:
                print(f"  not on the map, skipped: {row['photo']} -> {row['business']}")
            elif bid not in chosen:  # first photo wins
                chosen[bid] = row["photo"]
    return chosen


def write_index(js_text):
    lines = INDEX_PATH.read_text(encoding="utf-8").split("\n")
    at = next(i for i, line in enumerate(lines) if '<script type="__bundler/manifest">' in line) + 1
    manifest = json.loads(lines[at])
    manifest[PHOTOS_ASSET_ID] = {
        "mime": "application/javascript",
        "compressed": True,
        "data": base64.b64encode(gzip.compress(js_text.encode("utf-8"), mtime=0)).decode(),
    }
    lines[at] = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\u002F")
    t_at = next(i for i, line in enumerate(lines) if '<script type="__bundler/template">' in line) + 1
    template = json.loads(lines[t_at])
    if SCRIPT_TAG not in template:  # load the photos next to the business data
        anchor = '<script src="3034f34b-feb9-42c3-9850-f74ec9e5cc0e"></script>'
        if anchor not in template:
            sys.exit("Couldn't find the business-data script tag in the page template.")
        template = template.replace(anchor, anchor + "\n" + SCRIPT_TAG, 1)
        lines[t_at] = json.dumps(template, ensure_ascii=False).replace("</", "<\\u002F")
    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--photos", type=Path, default=DEFAULT_PHOTOS, help="the photo folder used for matching")
    parser.add_argument("--include-review", action="store_true", help="also use 'review' rows")
    args = parser.parse_args()
    if not MATCHES_PATH.exists():
        sys.exit("Run scripts/match_business_photos.py first (it writes data/photo-matches.csv).")

    chosen = choose_photos(args.include_review)
    photos = {}
    for bid, rel in chosen.items():
        path = args.photos / rel
        if path.exists():
            photos[bid] = as_data_uri(path)
        else:
            print(f"  missing file, skipped: {rel}")
    js = "window.BUSINESS_PHOTOS = " + json.dumps(photos, ensure_ascii=False, separators=(",", ":")) + ";\n"
    write_index(js)
    print(f"Embedded {len(photos)} photos ({len(js) / 1e6:.1f} MB) in {INDEX_PATH.name}")


if __name__ == "__main__":
    main()
