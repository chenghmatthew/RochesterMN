# What's Open: Downtown Rochester

Interactive directory of downtown Rochester businesses that remain open during construction. Visitors can browse by map, cards, or list, check hours and construction access notes, and see walking routes from parking or the pedestrian walkway.

Live site (after GitHub Pages is enabled): `https://YOUR-GITHUB-USERNAME.github.io/REPO-NAME/`

## Repository structure

```
.
├── index.html                  The full app, a single self-contained file served by GitHub Pages
├── .nojekyll                   Tells GitHub Pages to serve files as-is
├── README.md
├── data/
│   ├── Downtown Rochester Business Inventory 20260915.xlsx   Source spreadsheet (maintained by the City)
│   └── whats-open-data.js      Business data generated from the spreadsheet (reference copy)
└── embed/
    └── squarespace-code-block.html   Code to paste into the Squarespace What's Open page
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

City street-maintenance impacts load live from the City of Rochester ArcGIS service each time the map opens, so they do not need manual updates.

## Before launch

- Remove the eight sample businesses (IDs beginning with `sample-`) and the illustrative closure zones.
- Add photo URLs to the spreadsheet's image column. Photos dropped onto cards in the design tool are saved only in that browser.
- In your Mapbox account, restrict the access token to `YOUR-GITHUB-USERNAME.github.io` and your Squarespace domain.

## Technical notes

- Map: Mapbox GL JS v3 (Standard style with 3D buildings), loaded from the Mapbox CDN. An internet connection is required.
- Construction impacts: `Construction_Impacts_Maintenance_PublicView` FeatureServer (City of Rochester ArcGIS Online).
- No build step or server code; `index.html` is fully static.
