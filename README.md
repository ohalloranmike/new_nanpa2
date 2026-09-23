# nanpa2

Modern rewrite of the NANPA numbering plan browser.

Repository: https://github.com/mohal2_nike/nanpa2

## Features

- FastAPI app with Jinja2 templates and Uvicorn
- Modular layout (routes, ingest, database helpers, templating separated)
- Parameterized SQLite queries
- Project-relative paths (no hardcoded user directories)
- Automatic refresh of stale NANPA/CNAC source files and SQLite database
- Home page shows current data date with a live progress update window
- Separate data refresh command (`refresh_data.py`)
- Responsive UI with shared CSS and selectable themes (**NANPA** or **Nike**)
- International E.164 country overview with dialling metadata and libphonenumber validation
- Interactive zoomable world map on `/international` colored by national phone number length (scroll/pinch zoom, drag to pan, +/- and reset controls; bundled D3 + Natural Earth GeoJSON — no external map tiles at runtime)
- Supplemental international regions from libphonenumber (245 countries/territories) with NANP area-code context for +1 territories
- Feature parity with original app routes
- Zoomable clickable US state, US territory (schematic layout), and Canada province/territory maps on the home page (bundled D3 + Natural Earth boundaries) linking to area code maps per region
- Home **Lists**: full area code table (`/aclist`, all NANPA fields, status filter, sortable columns, dual horizontal scroll with pinned NPA); US/Canada operating company tables (`/ocnall`, `/canadaocnall`) with sortable column headers; Canada exchange list (`/canadaexall`) with status filter and sortable columns (NPA sort includes NXX)
- **Numbering regulator** card at the top of area code map browse (`/acmaps?state=`) and area code detail (`/areacodes?npa=`) pages: [NANPA](https://www.nanpa.com/) for US states and territories, [CNA](https://www.cnac.ca/index.htm) for Canada, and national regulators for Caribbean NANP members (see `app/nanpa_regulators.py`)

## Requirements

- Python 3.12+ recommended
- Windows: use the `py` launcher if `python` is not on PATH
- Dependencies include [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) for international number validation and [pycountry](https://github.com/flyingcircusio/pycountry) for supplemental country names

## Setup

```powershell
cd C:\Users\mohal2\PycharmProjects\nanpa2
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cursor/VS Code will use the local interpreter from `.vscode/settings.json`.

## Data refresh

The app downloads public NANPA and CNAC files, international dialling metadata, and builds `static/NANPA/pn.db`. See [Data sources](#data-sources) below for every dataset, its URL, local path, and what it powers in the app.

### Automatic refresh

On startup, the app checks whether downloaded source files in `static/NANPA/` and the SQLite database `static/NANPA/pn.db` are missing or older than 2 days. If so, it re-downloads stale files and rebuilds the database.

Set `NANPA_REFRESH_ON_START=1` to force a full download and rebuild on every launch.

### Update from the home page

The home page shows the current database date and an **Update data now** button. That opens a progress page at `/refresh-data` with:

- A progress bar and percentage
- The current step (download, extract, SQLite load, index build)
- A scrollable log of completed steps

Progress is streamed live from `/refresh-data/stream` using Server-Sent Events while source files are downloaded and the SQLite database is rebuilt.

### International numbering (Plan A)

Browse **International** in the nav, the **Browse international countries** link on the home page, or go to `/international` for country-level E.164 data. Country detail pages are at `/international/{iso2}` (for example `/international/FR`).

Features:

- **World map** — choropleth shaded by national number length (min–max digits from libphonenumber). Scroll or pinch to zoom, drag to pan, and use **+** / **−** / **Reset view** in the top-right corner. Countries highlight orange on hover; click a shaded country to open its detail page. Map assets are bundled under `static/maps/` and `static/js/` (no CDN map tiles).
- Country calling codes, international exit codes, and trunk prefixes
- Mobile/landline prefix hints and example formats
- National number length ranges from [libphonenumber](https://github.com/google/libphonenumber)
- **NANP context** — territories that share country calling code +1 (e.g. Anguilla, Jamaica) show their NANP area code on list and detail pages so +1 is not mistaken for the United States alone
- Links to national regulators where curated (e.g. Ofcom, CNAC, NANPA)
- Per-country phone number validation (syntax/rules only)
- **Special numbering** on country detail pages (outside US/Canada NANP detail): toll-free, shared-cost, premium, UAN, and related non-geographic ranges summarized from libphonenumber metadata, with national length and example formats
- **Primary currency** (ISO 4217 name and code) on international country detail pages, shown under the country name in smaller type
- US and Canada link back to existing NANP area code and office code detail
- Filter by continent or search by country name, ISO code, or calling code
- **Supplemental regions** — countries present in libphonenumber but missing from the VoixCall JSON are added at refresh time (names from Natural Earth GeoJSON or pycountry; dialling fields may show — where VoixCall had no data)

This is not exchange-level numbering data — only a trustworthy country overview layer. See [Data sources](#data-sources) for the exact datasets and URLs.

### Manual refresh

```powershell
.venv\Scripts\python.exe refresh_data.py
```

Force download and rebuild regardless of file age:

```powershell
.venv\Scripts\python.exe refresh_data.py --force
```

### US state area-code map GIFs (optional, manual review)

Tabular data refresh does **not** update map images under `static/USACMaps/`. To download **US state** GIFs from [nanpa.com](https://www.nanpa.com) inline map URLs into a review folder (same `USACMaps/` names as production), run:

```powershell
.venv\Scripts\python.exe fetch_nanpa_maps.py
```

One state only:

```powershell
.venv\Scripts\python.exe fetch_nanpa_maps.py --state TX
```

Dry-run (print URLs only):

```powershell
.venv\Scripts\python.exe fetch_nanpa_maps.py --state CA --dry-run
```

Files land in `map_fetch_review/USACMaps/` (gitignored) with a `manifest.json` summary. Copy approved GIFs into `static/USACMaps/`. The site typically provides the main `{ST}.gif` only; `-inset1` / `-inset2` files are often absent and listed as `missing` in the manifest.

## Run app

```powershell
.venv\Scripts\python.exe run.py
```

Or double-click [`start_nanpa2.bat`](start_nanpa2.bat) in the project folder. It reads `NANPA_HOST` and `NANPA_PORT` from config, stops any process already listening on that port, then starts the server. The command window stays open and waits for **Ctrl+C** to stop. If the app exits with an error, the window stays open so you can read the message.

To launch from the Desktop, create a shortcut to `start_nanpa2.bat` (**Send to → Desktop (create shortcut)**). Do not copy the bat file itself to the Desktop, because it needs to run from the project folder where `.venv` lives.

**Linux (e.g. Linux Mint)** — from the project directory (for example `~/PycharmProjects/new_nanpa2`):

```bash
chmod +x start_nanpa2.sh   # once, after clone
./start_nanpa2.sh
```

Same behavior as the Windows launcher: uses `.venv/bin/python`, frees the configured port (`fuser` or `lsof`), then runs `run.py`. Override the port with `NANPA_PORT=8003 ./start_nanpa2.sh` if needed.

Or with Uvicorn directly:

```powershell
.venv\Scripts\uvicorn.exe run:app --host 127.0.0.1 --port 8002
```

Open: http://127.0.0.1:8002

Set `FLASK_DEBUG=1` to enable auto-reload during development.

### Themes

Use the **Theme** dropdown in the page header to switch between:

- **NANPA** (default) — inspired by [nanpa.com](https://www.nanpa.com): navy top bar, blue navigation band, white content area, and dark footer
- **Nike** — matches the [ZoomAPI_Tools](https://github.com/mohal2_nike/ZoomAPI_Tools) Nike theme: black background, orange accents, uppercase Oswald headings, and the Nike swoosh in the header

Your choice is saved in the browser (`localStorage` key `nanpa2-ui-theme`) and applied before the page paints, matching the ZoomAPI_Tools pattern. Theme switching logic lives inline in `templates/base.html` (no separate JavaScript file).

HTML and static assets are sent with `Cache-Control: no-cache` so CSS updates apply reliably after a normal refresh. If styles still look stale, hard refresh once with **Ctrl+F5**.

On the **NANPA** theme, the theme dropdown uses a navy control with white text; open options use a white background and dark text for readability.

On the **Nike** theme, the header shows the orange Nike swoosh, dark cards, and orange focus/hover accents on links and form controls.

### Port already in use

`start_nanpa2.bat` stops any process listening on the configured port before launch (same approach as Zoom_Dashboard). To check manually in PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Get-Process -Id $_.OwningProcess
}
```

Stop the listener:

```powershell
Get-NetTCPConnection -LocalPort 8002 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

Or run on another port:

```powershell
$env:NANPA_PORT=8003
.venv\Scripts\python.exe run.py
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NANPA_HOST` | `127.0.0.1` | Server host |
| `NANPA_PORT` | `8002` | Server port |
| `FLASK_DEBUG` | `0` | Enable Uvicorn auto-reload |
| `NANPA_REFRESH_ON_START` | `0` | Force download and rebuild at startup |
| `NANPA_DB_MAX_AGE_DAYS` | `2` | Max age for source files and database before refresh |
| `NANPA_REQUESTS_VERIFY` | `0` | TLS certificate verification for downloads |
| `NANPA_INTERNATIONAL_DATA_URL` | `https://raw.githubusercontent.com/VoixCall/country-calling-codes/main/data/countries.json` | International dialling dataset URL |
| `SECRET_KEY` | `dev-change-me` | App secret key |

## Project layout

```text
nanpa2/
  app/
    __init__.py          # FastAPI app factory
    config.py
    constants.py
    database.py
    ingest.py            # Download and SQLite rebuild logic
    international.py     # International E.164 ingest and validation
    international_regulators.py
    nanpa_regulators.py   # NANP regulator links (US/territories, Canada, Caribbean)
    maps.py
    templating.py        # Jinja2 helpers and url_for compatibility
    routes/
      home.py            # Home page and refresh UI routes
      refresh_stream.py  # SSE progress stream for data updates
      international.py   # International browse routes
  templates/
    international/       # International country list and detail pages
    base.html            # Shared layout, theme selector, and inline theme JS
    refresh_data.html    # Live update progress page
  static/
    css/
    js/
      d3.min.js          # D3 v7 (bundled for international map)
      international-map.js
    maps/
      world-countries.geojson  # Natural Earth 110m countries (map + supplemental names)
    NANPA/               # Downloaded data and generated pn.db (mostly gitignored)
  .vscode/
    settings.json        # Local Python interpreter path
  run.py
  start_nanpa2.bat     # Double-click Windows launcher
  start_nanpa2.sh      # Linux/macOS launcher (chmod +x first)
  refresh_data.py
  fetch_nanpa_maps.py  # Optional US state AC map GIF download (see below)
  requirements.txt
```

## Data sources

All downloaded files land under `static/NANPA/` and are gitignored except bundled reference CSVs. The app rebuilds `static/NANPA/pn.db` from the downloaded files on refresh.

### Downloaded on refresh (NANPA / CNAC / international)

| Local file | Source URL | What you get | Used for |
|------------|------------|--------------|----------|
| `npa_report.csv` | [NANPA NPA report](https://reports.nanpa.com/public/npa_report.csv) | US area code (NPA) assignments: location, in-service date, overlays, pooling, and related NANPA fields | Area code lookup, browse-by-state maps, area code list |
| `CoCodeAssignment_Utilized_AllStates_Public.txt` (from zip) | [NANPA office code zip](https://reports.nanpa.com/public/CoCodeAssignment_Utilized_AllStates_Public.zip) | US office code (NPA-NXX) assignments: OCN, operating company, rate center, state, assignment status | Office code lookup, rate centers, company detail, OCN index |
| `COCodeStatus_ALL.csv` (from zip) | [CNAC office code zip](https://www.cnac.ca/data/COCodeStatus_ALL.zip) | Canada office code assignments: province, exchange area, OCN, company, NPA, CO code | Canada office code lookup, rate centers, company detail |
| `international_countries.json` | [VoixCall countries JSON](https://raw.githubusercontent.com/VoixCall/country-calling-codes/main/data/countries.json) (override with `NANPA_INTERNATIONAL_DATA_URL`) | Per-country ISO code, name, E.164 calling code, continent, international exit code, trunk/mobile/landline prefixes, example numbers, international format | International country list and detail pages (`intl_country` table) |

**Derived SQLite tables** (built during refresh, not downloaded directly):

| Table | Built from | What you get |
|-------|------------|--------------|
| `ac` | `npa_report.csv` | US area code records |
| `oc` | US office code text file | US office code records (`State` **NN** from NANPA is stored as **CNMI** to match `npa_report.csv` **LOCATION**) |
| `caoc` | `COCodeStatus_ALL.csv` | Canada office code records |
| `ocn` | `oc` | Distinct US operating companies (OCN + company name) |
| `intl_country` | `international_countries.json` + phonenumbers/libphonenumber gaps + enrichments below | International country overview records |

### Runtime library metadata (not downloaded)

| Source | What you get | Used for |
|--------|--------------|----------|
| [phonenumbers](https://github.com/daviddrysdale/python-phonenumber) (Google [libphonenumber](https://github.com/google/libphonenumber) metadata bundled in the package) | National number length ranges, example numbers, parse/validate rules, special-number-type metadata (toll-free, shared cost, premium, UAN, etc.), and regions missing from VoixCall | International country detail (`national_length_min` / `max`, `lib_example`, **Special numbering** table via `special_numbering_summaries()`), supplemental `intl_country` rows, and per-country phone validation on `/international/{iso2}?phone=...` |
| [pycountry](https://github.com/flyingcircusio/pycountry) | ISO 3166-1 country names for supplemental regions | Country names when not present in the bundled Natural Earth map data |

### Curated in code (not downloaded)

| Source | What you get | Used for |
|--------|--------------|----------|
| `app/international_regulators.py` → `REGULATORS` | National regulator name and website for selected countries (e.g. NANPA, CNAC, Ofcom, ARCEP) | Regulator links on international country pages |
| `app/international_regulators.py` → `ITU_REFERENCES` | ITU-T E.164 and dialling procedure references | Official reference links on international pages |
| `app/nanpa_regulators.py` → `NANPA_US`, `CANADIAN_NUMBERING_ADMIN`, `NANP_MEMBER_REGULATORS` | Numbering administrator/regulator name and URL for US states, US territories, Canada, and home-page Caribbean NANP countries | “Numbering regulator” card on `/acmaps` and `/areacodes` (via `regulator_card` in `templates/macros.html`). Re-check HTTPS with `scripts/verify_nanpa_regulator_links.py` after URL changes. |
| `static/international/country_primary_currency.json` | Primary ISO 4217 currency per ISO 3166-1 alpha-2 (from [mledoze/countries](https://github.com/mledoze/countries); regenerate with `scripts/build_country_primary_currency.py`) | Currency name and code under the country title on `/international/{iso2}` |

### Bundled static files (shipped with the repo)

| Local path | What you get | Used for |
|------------|--------------|----------|
| `static/NANPA/special_service_numbers.csv` | Reserved extensions (911, 988, 112, etc.) by country/region | Special Service Numbers list |
| `static/NANPA/N11-Codes.csv` | N11 short-code definitions (211, 311, 411, …) | N11 codes list |
| `static/NANPA/900codes.csv` | 900-series NXX assignments and entities | 900 codes list |
| `static/USACMaps/` | US state area-code map GIFs (main map plus optional `-inset1` / `-inset2` GIFs per state) | US area code and office code pages |
| `static/USStateMaps/` | US state outline PNGs | US area code and office code pages |
| `static/USTerritoryACMaps/` | US territory area-code maps | Territory browse and lookup |
| `static/CanadaACMaps/` | Canada province/territory area-code maps | Canada area code pages |
| `static/CountryACMaps/` | Caribbean and other NANP country maps | Country browse pages (Jamaica, The Bahamas, etc.) |
| `static/maps/world-countries.geojson` | [Natural Earth](https://www.naturalearthdata.com/) 110m country boundaries (`ISO_A2`, continent/subregion) | International choropleth map; continent and country names for supplemental `intl_country` rows |
| `static/maps/us-states.geojson` | Natural Earth 110m US state boundaries (filtered to NANPA state codes) | Home page US state map |
| `static/maps/canada-provinces.geojson` | Natural Earth 50m Canada province/territory boundaries (mapped to CNAC browse regions) | Home page Canada map |
| `static/maps/us-territories.geojson` | Natural Earth 50m territory outlines (PR, GU, AS, CNMI, VI), repositioned for a schematic home-page layout (`scripts/build_us_territories_geojson.py`) | Home page US territories map |
| `static/js/d3.min.js` | D3.js v7 (minified, bundled) | International map rendering |
| `static/js/international-map.js` | Map interaction (choropleth, legend, zoom/pan, controls, hover, click-through) | `/international` world map |
| `static/js/us-states-map.js` | US state map (zoom/pan, controls, hover, click-through to `/acmaps`) | Home page |
| `static/js/canada-provinces-map.js` | Canada province/territory map (zoom/pan, controls, grouped hover for multi-polygon browse regions such as YT-NWT-NU and NS-PEI, click-through to `/acmaps`) | Home page |
| `static/js/us-territories-map.js` | US territories map (zoom/pan, controls, hover, click-through to `/acmaps`) | Home page |

Other CSV files under `static/NANPA/` (`AreaCodeDatabaseDefinitions.csv`, `OfficeCodeDatabaseDefinitions.csv`, `FGD-CIC.csv`, `FGB-CIC.csv`) are legacy reference material from the original app and are not loaded by current routes.

## Notes

- Map images and curated CSV lists are stored under `static/`. Optional `fetch_nanpa_maps.py` downloads main US `{ST}.gif` files into gitignored `map_fetch_review/`; inset GIFs are not on nanpa.com and stay manual.
- US state map sections only render images that exist on disk (`app/maps.py` → `us_state_map_images`); states without inset GIFs do not show inset placeholders or 404 broken images.
- Generated NANPA download files and `pn.db` are gitignored.
- `international_countries.json` is downloaded with other source files and is also gitignored.
- First run may take a minute while source files download and the database is built.
- The US office code file parser ignores NANPA's trailing header-only `File Updated` column.
- US territory browse keys match NANPA area-code **LOCATION** codes (`PR`, `GU`, `AS`, `CNMI`, `VI` for the US Virgin Islands). Legacy `?state=USVI` URLs redirect to `VI`.
- Rebuild schematic territory outlines after editing layout: `python scripts/build_us_territories_geojson.py` (requires network; uses Natural Earth via GitHub).
