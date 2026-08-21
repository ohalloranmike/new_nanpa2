# nanpa2

Modern rewrite of the NANPA numbering plan browser.

Repository: https://github.com/mohal2_nike/nanpa2

## Features

- FastAPI app with Jinja2 templates and Uvicorn
- Modular layout (routes, ingest, database helpers, templating separated)
- Parameterized SQLite queries
- Project-relative paths (no hardcoded user directories)
- Automatic refresh of stale NANPA/CNAC source files and SQLite database
- Separate data refresh command (`refresh_data.py`)
- Responsive UI with shared CSS
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

Or with Uvicorn directly:

```powershell
.venv\Scripts\uvicorn.exe run:app --host 127.0.0.1 --port 5000
```

Open: http://127.0.0.1:5000

Set `FLASK_DEBUG=1` to enable auto-reload during development.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NANPA_HOST` | `127.0.0.1` | Server host |
| `NANPA_PORT` | `5000` | Server port |
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
  templates/
  static/
    css/
    NANPA/               # Downloaded data and generated pn.db (mostly gitignored)
  .vscode/
    settings.json        # Local Python interpreter path
  run.py
  refresh_data.py
  requirements.txt
```

## Notes

- Map images and curated CSV lists are stored under `static/`.
- Generated NANPA download files and `pn.db` are gitignored.
- First run may take a minute while source files download and the database is built.
