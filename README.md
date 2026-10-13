# What's Open: Downtown Rochester

Interactive directory of downtown Rochester businesses that remain open during construction. Visitors can browse by map, cards, or list, check hours and construction access notes, and see walking routes from the closest public parking ramp, lot, or open block of on-street parking.

Live site (after GitHub Pages is enabled): `https://YOUR-GITHUB-USERNAME.github.io/REPO-NAME/`

## Repository structure

```
.
├── index.html                  The full app, a single self-contained file served by GitHub Pages
├── .nojekyll                   Tells GitHub Pages to serve files as-is
├── README.md
├── data/
│   ├── Downtown Rochester Business Inventory 20260915.xlsx   Source spreadsheet (maintained by the City)
│   ├── whats-open-data.js      Business data generated from the spreadsheet (reference copy)
│   └── walk-network.json       Downtown sidewalk network from OpenStreetMap (also embedded in index.html)
├── embed/
│   └── squarespace-code-block.html   Code to paste into the Squarespace What's Open page
└── scripts/
    └── build_walk_network.py   Rebuilds the sidewalk network from OpenStreetMap
```

## Publish with GitHub Pages

1. Create an empty repository on GitHub (public, no README).
2. Copy the contents of this folder into your local clone, then commit and push:
   ```
   git add .
   git commit -m "Initial What's Open directory"
   git push origin main
   ```
3. On GitHub, go to **Settings → Pages**.
4. Under **Build and deployment**, set **Source** to *Deploy from a branch*, **Branch** to `main`, folder `/ (root)`, then **Save**.
5. After a minute or two the site is live at `https://YOUR-GITHUB-USERNAME.github.io/REPO-NAME/`.

## Add it to Squarespace

1. Open `embed/squarespace-code-block.html` and replace `YOUR-GITHUB-USERNAME` and `REPO-NAME`.
2. On the What's Open page, add a **Code** block, set it to HTML, and paste the contents.
3. Check the page in a private/incognito window. Code blocks may not render while you are logged in.

Notes:
- Iframes in code blocks require a Squarespace Core, Plus, or Advanced plan.
- If the block is blank, disable Ajax loading and make sure the page is not inside an index page.

## Updating business data

The business list comes from the spreadsheet in `data/`. To update:

1. Edit the spreadsheet (hours, access notes, status, coordinates, image URLs).
2. Upload the new version to the design project and ask for a refresh. A new `index.html` and `data/whats-open-data.js` are produced.
3. Replace both files in this repo, commit, and push. GitHub Pages republishes automatically. Squarespace needs no changes.

City street-maintenance impacts, road and sidewalk closures, and parking load live from City of Rochester ArcGIS services each time the map opens, so they do not need manual updates.

## Updating the sidewalk network

"Route from parking" walks the OpenStreetMap sidewalk network. The script saves it to `data/walk-network.json` and embeds the same data in `index.html`, so routes work even when the page is opened straight from disk. Refresh it when OSM sidewalks change (a few times a year is plenty):

```
py scripts/build_walk_network.py
```

The script uses only the Python standard library and downloads from the public Overpass API, which is often busy; it retries several mirrors. If Python can't verify Overpass's certificate (common on corporate networks), download the data with `curl` and pass the file in:

```
curl -s -o osm.json --data-urlencode 'data=[out:json][timeout:90];way["highway"](44.0145,-92.4975,44.0300,-92.4530)->.w;.w out body;.w >;out skel qt;' https://overpass-api.de/api/interpreter
py scripts/build_walk_network.py --overpass-json osm.json
```

Commit both `data/walk-network.json` and `index.html`.

## Previewing the phone layout

On a desktop browser, open `index.html` locally (or the live site with `?preview` added, e.g. `https://chenghmatthew.github.io/RochesterMN/?preview`) and select **Phone preview** next to the Map / Cards / List tabs. The page reloads inside a phone-sized frame (Android 360×800, iPhone 390×844 or iPhone Pro Max 430×932), so it shows the real mobile layout. Press Esc to close. The button is hidden in the Squarespace embed and on the live site without `?preview`.

## Before launch

- Remove the eight sample businesses (IDs beginning with `sample-`).
- Add photo URLs to the spreadsheet's image column. Photos dropped onto cards in the design tool are saved only in that browser.
- In your Mapbox account, restrict the access token to `YOUR-GITHUB-USERNAME.github.io` and your Squarespace domain.

## Technical notes

- Map: Mapbox GL JS v3 (Standard style, monochrome theme, with 3D buildings; falls back to Mapbox Light if Standard fails to load), loaded from the Mapbox CDN. An internet connection is required.
- Live City of Rochester ArcGIS Online layers (City GIS contact: Kelsey Gates). All but City street work can be toggled under **Live City data** in the map legend:

  | Layer | Service | Filter applied by the map |
  |---|---|---|
  | City street work | `Construction_Impacts_Maintenance_PublicView/FeatureServer/0` | downtown extent |
  | Road closures | `BFUConstructionInformation_RoadImpact_V2_PublicView/FeatureServer/3` | none (view is already Active road impacts) |
  | Sidewalk closures | `BFUConstructionInformation_PublicPedImpact_View/FeatureServer/2` | `PedImpactStatus <> 'Open'` |
  | Parking ramps & lots | `Public_Parking_view/FeatureServer/0` | `type IN ('Ramp','Surface Lot')` (drops Park & Rides) |
  | On-street parking | `Downtown_Parking_Spaces_ViewLayer/FeatureServer/0` | `Space_STAT = 'Active'`; off by default, loads when toggled on, visible at zoom 15.5+ |

  The layer list lives in `liveDefs()` inside the bundled `index.html` template.
- Parking wayfinding. Each business offers two walking routes, both on the OSM network in `data/walk-network.json`:
  - **From ramp or lot** picks the public ramp or surface lot with the shortest *walking* distance to the business.
  - **From street parking** groups public curbside spaces (metered or unmetered; `Curbside` = `YES-*`, so lot spaces, loading zones, bus stops and other restricted spaces are left out) into block faces by street and hundred block. A space is skipped if it overlaps, or comes within 3 m of, any road impact (full closure, reduced lanes or periodic closure), a sidewalk/crosswalk closure marked `Closed` or `Partial Closure`, or a current City street-work segment marked `Partially Closed`. The route starts from the closest block that still has at least 3 open spaces, and those spaces are highlighted on the map.
  - Routes never cross, touch or run inside a closure area shown on the map: any road impact (full closure, reduced lanes or periodic closure) or a sidewalk/crosswalk marked `Closed` or `Partial Closure`. This is an exact geometric test on every path segment and on the short connectors from the parking spot and to the business. `Temporary` sidewalks (signed detours) stay walkable. They prefer mapped sidewalks and crossings and only use street centerlines where OSM has no separate sidewalk. Skyways and the pedestrian subway are excluded for now (opening hours).
  - Routes draw on top of 3D buildings (`line-occlusion-opacity: 1`). If the network data is missing, the map falls back to a straight-line estimate.
- Walking times assume about 80 m (260 ft) per minute.
- No build step or server code; `index.html` is fully static.
