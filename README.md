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
- Responsive UI with shared CSS and selectable themes (**Basic** or **NANPA**)
- Feature parity with original app routes

## Requirements

- Python 3.12+ recommended
- Windows: use the `py` launcher if `python` is not on PATH

## Setup

```powershell
cd C:\Users\mohal2\PycharmProjects\nanpa2
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cursor/VS Code will use the local interpreter from `.vscode/settings.json`.

## Data refresh

The app downloads public NANPA and CNAC files and builds `static/NANPA/pn.db`.

### Automatic refresh

On startup, the app checks:

1. **Source files** in `static/NANPA/`:
   - `npa_report.csv`
   - `CoCodeAssignment_Utilized_AllStates_Public.txt`
   - `COCodeStatus_ALL.csv`
2. **SQLite database**: `static/NANPA/pn.db`

If any source file is missing or older than 7 days, new files are downloaded and the database is rebuilt. If source files are still fresh but the database is missing or stale, the database is rebuilt from the existing files without re-downloading.

Set `NANPA_REFRESH_ON_START=1` to force a full download and rebuild on every launch.

### Update from the home page

The home page shows the current database date and an **Update data now** button. That opens a progress page at `/refresh-data` with:

- A progress bar and percentage
- The current step (download, extract, SQLite load, index build)
- A scrollable log of completed steps

Progress is streamed live from `/refresh-data/stream` using Server-Sent Events while NANPA and CNAC files are downloaded and the SQLite database is rebuilt.

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

- **Basic** — the default light layout with rounded cards and soft blue accents
- **NANPA** — a look inspired by [nanpa.com](https://www.nanpa.com): navy top bar, blue navigation band, white content area, and dark footer

Your choice is saved in the browser (`localStorage` key `nanpa2-ui-theme`) and applied before the page paints, matching the ZoomAPI_Tools pattern. Theme switching logic lives inline in `templates/base.html` (no separate JavaScript file).

HTML and static assets are sent with `Cache-Control: no-cache` so CSS updates apply reliably after a normal refresh. If styles still look stale, hard refresh once with **Ctrl+F5**.

On the **NANPA** theme, the theme dropdown uses a navy control with white text; open options use a white background and dark text for readability.

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
| `NANPA_DB_MAX_AGE_DAYS` | `7` | Max age for source files and database before refresh |
| `NANPA_REQUESTS_VERIFY` | `0` | TLS certificate verification for downloads |
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
    maps.py
    templating.py        # Jinja2 helpers and url_for compatibility
    routes/
      home.py            # Home page and refresh UI routes
      refresh_stream.py  # SSE progress stream for data updates
  templates/
    base.html            # Shared layout, theme selector, and inline theme JS
    refresh_data.html    # Live update progress page
  static/
    css/
    NANPA/               # Downloaded data and generated pn.db (mostly gitignored)
  .vscode/
    settings.json        # Local Python interpreter path
  run.py
  start_nanpa2.bat     # Double-click Windows launcher
  refresh_data.py
  requirements.txt
```

## Notes

- Map images and curated CSV lists are stored under `static/`.
- Generated NANPA download files and `pn.db` are gitignored.
- First run may take a minute while source files download and the database is built.
- The US office code file parser ignores NANPA's trailing header-only `File Updated` column.
