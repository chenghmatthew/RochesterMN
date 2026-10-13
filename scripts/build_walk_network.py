"""Build data/walk-network.json: the downtown Rochester pedestrian network from OpenStreetMap.

The map's "Route from parking" button walks this network from the closest City parking
ramp or lot to a business, skipping sidewalks and crosswalks the City has marked Closed.
The network is also embedded in index.html so routing works even when the page is opened
from disk, where browsers block loading data/walk-network.json.

Run it again whenever OSM sidewalks change (a few times a year is plenty):

    py scripts/build_walk_network.py
    py scripts/build_walk_network.py --overpass-json saved.json   # reuse a saved Overpass response

Uses only the Python standard library. Data (c) OpenStreetMap contributors, ODbL.
"""

import argparse
import base64
import gzip
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

# south, west, north, east: covers every business and City ramp/lot with a few blocks of margin.
BBOX = (44.0145, -92.4975, 44.0300, -92.4530)
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "walk-network.json"
INDEX_PATH = ROOT / "index.html"
# The bundle asset that index.html loads as <script src="...">; it sets window.WALK_NETWORK.
WALK_ASSET_ID = "cb8a87ba-2805-4be8-8d29-f864fdc0ad6a"

# Edge kinds. The map multiplies each segment's length by a cost per kind (WALK_COST in index.html)
# so routes prefer mapped sidewalks and only fall back to street centerlines where sidewalks are missing.
FOOTWAY, CROSSING, STEPS, LOCAL_STREET, ARTERIAL = 0, 1, 2, 3, 4
PATH_HIGHWAYS = {"footway", "path", "pedestrian", "living_street", "cycleway", "track"}
LOCAL_HIGHWAYS = {"residential", "unclassified", "service", "road"}
ARTERIAL_HIGHWAYS = {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link"}


def classify(tags):
    """Return the edge kind for an OSM way, or None if pedestrians can't (or shouldn't) use it."""
    hw = tags.get("highway")
    foot = tags.get("foot")
    if foot == "no" or tags.get("access") in ("private", "no") and foot not in ("yes", "designated", "permissive"):
        return None
    # Skyways and the pedestrian subway have opening hours; leave them out until we handle that.
    name = tags.get("name", "").lower()
    if hw == "corridor" or tags.get("indoor") in ("yes", "corridor") or "skyway" in name or "subway" in name:
        return None
    if hw == "footway" and tags.get("tunnel") == "yes":
        return None
    if hw == "steps":
        return STEPS
    if hw == "footway" and tags.get("footway") == "crossing":
        return CROSSING
    if hw in PATH_HIGHWAYS:
        return FOOTWAY
    sidewalk = tags.get("sidewalk") or tags.get("sidewalk:both")
    if sidewalk in ("separate", "no", "none"):
        return None  # sidewalks are mapped as their own ways (or don't exist)
    if hw in LOCAL_HIGHWAYS:
        return LOCAL_STREET
    if hw in ARTERIAL_HIGHWAYS:
        return ARTERIAL
    return None


def fetch_overpass():
    s, w, n, e = BBOX
    query = f'[out:json][timeout:90];way["highway"]({s},{w},{n},{e})->.w;.w out body;.w >;out skel qt;'
    body = urllib.parse.urlencode({"data": query}).encode()
    for attempt in range(1, 7):
        for url in OVERPASS_URLS:
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": "RochesterWhatsOpen/1.0"})
                with urllib.request.urlopen(req, timeout=150) as resp:
                    return json.load(resp)
            except Exception as exc:  # busy servers answer with HTML or time out; try the next mirror
                print(f"  {url} failed ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        print(f"Overpass attempt {attempt} failed; retrying in 20 s", file=sys.stderr)
        time.sleep(20)
    raise SystemExit("Overpass is unavailable. Try again later.")


def largest_component(node_ids, ways):
    """Keep only the biggest connected piece so nothing snaps to an isolated sidewalk fragment."""
    adj = {nid: [] for nid in node_ids}
    for _, nodes in ways:
        for a, b in zip(nodes, nodes[1:]):
            adj[a].append(b)
            adj[b].append(a)
    seen, best = set(), set()
    for start in adj:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        seen.add(start)
        while stack:
            for nxt in adj[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        if len(comp) > len(best):
            best = comp
    return best


def build(osm):
    coords = {el["id"]: (el["lon"], el["lat"]) for el in osm["elements"] if el["type"] == "node"}
    ways = []
    for el in osm["elements"]:
        if el["type"] != "way":
            continue
        kind = classify(el.get("tags", {}))
        nodes = [nid for nid in el.get("nodes", []) if nid in coords]
        if kind is not None and len(nodes) > 1:
            ways.append((kind, nodes))

    keep = largest_component({nid for _, nodes in ways for nid in nodes}, ways)
    ways = [(kind, nodes) for kind, nodes in ways if nodes[0] in keep]

    origin = (BBOX[1], BBOX[0])  # west, south
    scale = 1_000_000  # 1e-6 degree is about 0.1 m
    index, flat = {}, []
    for _, nodes in ways:
        for nid in nodes:
            if nid not in index:
                index[nid] = len(index)
                lon, lat = coords[nid]
                flat += [round((lon - origin[0]) * scale), round((lat - origin[1]) * scale)]

    kx = 111_320 * math.cos(math.radians(origin[1]))
    meters = sum(
        math.hypot((coords[a][0] - coords[b][0]) * kx, (coords[a][1] - coords[b][1]) * 110_540)
        for _, nodes in ways for a, b in zip(nodes, nodes[1:])
    )
    counts = {k: sum(1 for kind, _ in ways if kind == k) for k in range(5)}
    print(f"{len(ways)} ways, {len(index)} nodes, {meters / 1000:.1f} km; ways by kind {counts}")

    return {
        "source": "(c) OpenStreetMap contributors, ODbL. Built by scripts/build_walk_network.py",
        "generated": date.today().isoformat(),
        "bbox": [BBOX[1], BBOX[0], BBOX[3], BBOX[2]],
        "kinds": ["footway", "crossing", "steps", "local street", "arterial"],
        "origin": list(origin),
        "scale": scale,
        "nodes": flat,
        "ways": [[kind] + [index[nid] for nid in nodes] for kind, nodes in ways],
    }


def embed_in_index(network_json):
    """Store the network in index.html's bundle manifest (the JSON line after the manifest tag)."""
    lines = INDEX_PATH.read_text(encoding="utf-8").split("\n")
    at = next(i for i, line in enumerate(lines) if '<script type="__bundler/manifest">' in line) + 1
    manifest = json.loads(lines[at])
    script = f"window.WALK_NETWORK = {network_json};\n".encode()
    manifest[WALK_ASSET_ID] = {
        "mime": "application/javascript",
        "compressed": True,
        "data": base64.b64encode(gzip.compress(script, mtime=0)).decode(),
    }
    # Same encoding the bundler uses, so the rest of the manifest stays byte-identical.
    lines[at] = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\u002F")
    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines))
    print(f"Embedded network in {INDEX_PATH.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--overpass-json", type=Path, help="use a saved Overpass response instead of downloading")
    args = parser.parse_args()
    osm = json.loads(args.overpass_json.read_text(encoding="utf-8")) if args.overpass_json else fetch_overpass()
    network_json = json.dumps(build(osm), separators=(",", ":"))
    OUT_PATH.write_text(network_json, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
    embed_in_index(network_json)


if __name__ == "__main__":
    main()
