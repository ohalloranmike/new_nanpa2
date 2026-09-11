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

## Run app

```powershell
.venv\Scripts\python.exe run.py
```

Or double-click [`start_nanpa2.bat`](start_nanpa2.bat) in the project folder. It reads `NANPA_HOST` and `NANPA_PORT` from config, stops any process already listening on that port, then starts the server. The command window stays open and waits for **Ctrl+C** to stop. If the app exits with an error, the window stays open so you can read the message.

To launch from the Desktop, create a shortcut to `start_nanpa2.bat` (**Send to → Desktop (create shortcut)**). Do not copy the bat file itself to the Desktop, because it needs to run from the project folder where `.venv` lives.

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
  refresh_data.py
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
| `oc` | US office code text file | US office code records |
| `caoc` | `COCodeStatus_ALL.csv` | Canada office code records |
| `ocn` | `oc` | Distinct US operating companies (OCN + company name) |
| `intl_country` | `international_countries.json` + phonenumbers/libphonenumber gaps + enrichments below | International country overview records |

### Runtime library metadata (not downloaded)

| Source | What you get | Used for |
|--------|--------------|----------|
| [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) (Google [libphonenumber](https://github.com/google/libphonenumber) metadata bundled in the package) | National number length ranges, example numbers, parse/validate rules, and regions missing from VoixCall | International country detail (`national_length_min` / `max`, `lib_example`), supplemental `intl_country` rows, and per-country phone validation on `/international/{iso2}?phone=...` |
| [pycountry](https://github.com/flyingcircusio/pycountry) | ISO 3166-1 country names for supplemental regions | Country names when not present in the bundled Natural Earth map data |

### Curated in code (not downloaded)

| Source | What you get | Used for |
|--------|--------------|----------|
| `app/international_regulators.py` → `REGULATORS` | National regulator name and website for selected countries (e.g. NANPA, CNAC, Ofcom, ARCEP) | Regulator links on international country pages |
| `app/international_regulators.py` → `ITU_REFERENCES` | ITU-T E.164 and dialling procedure references | Official reference links on international pages |

### Bundled static files (shipped with the repo)

| Local path | What you get | Used for |
|------------|--------------|----------|
| `static/NANPA/special_service_numbers.csv` | Reserved extensions (911, 988, 112, etc.) by country/region | Special Service Numbers list |
| `static/NANPA/N11-Codes.csv` | N11 short-code definitions (211, 311, 411, …) | N11 codes list |
| `static/NANPA/900codes.csv` | 900-series NXX assignments and entities | 900 codes list |
| `static/USACMaps/` | US state area-code map GIFs | US area code and office code pages |
| `static/USStateMaps/` | US state outline PNGs | US area code and office code pages |
| `static/USTerritoryACMaps/` | US territory area-code maps | Territory browse and lookup |
| `static/CanadaACMaps/` | Canada province/territory area-code maps | Canada area code pages |
| `static/CountryACMaps/` | Caribbean and other NANP country maps | Country browse pages (Jamaica, Bahamas, etc.) |
| `static/maps/world-countries.geojson` | [Natural Earth](https://www.naturalearthdata.com/) 110m country boundaries (`ISO_A2`, continent/subregion) | International choropleth map; continent and country names for supplemental `intl_country` rows |
| `static/js/d3.min.js` | D3.js v7 (minified, bundled) | International map rendering |
| `static/js/international-map.js` | Map interaction (choropleth, legend, zoom/pan, controls, hover, click-through) | `/international` world map |

Other CSV files under `static/NANPA/` (`AreaCodeDatabaseDefinitions.csv`, `OfficeCodeDatabaseDefinitions.csv`, `FGD-CIC.csv`, `FGB-CIC.csv`) are legacy reference material from the original app and are not loaded by current routes.

## Notes

- Map images and curated CSV lists are stored under `static/`.
- Generated NANPA download files and `pn.db` are gitignored.
- `international_countries.json` is downloaded with other source files and is also gitignored.
- First run may take a minute while source files download and the database is built.
- The US office code file parser ignores NANPA's trailing header-only `File Updated` column.
