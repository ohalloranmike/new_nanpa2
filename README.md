# nanpa2

Modern rewrite of the NANPA numbering plan browser.

## Features

- Modular Flask app (routes, ingest, database helpers separated)
- Parameterized SQLite queries
- Project-relative paths (no hardcoded user directories)
- Separate data refresh command (`refresh_data.py`)
- Updated responsive UI with shared CSS
- Feature parity with original app routes

## Setup

```bash
cd C:\Users\mohal2\PycharmProjects\nanpa2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Refresh data

Downloads NANPA/CNAC source files and rebuilds `static/NANPA/pn.db`:

```bash
python refresh_data.py --force
```

## Run app

```bash
python run.py
```

Open: http://127.0.0.1:5000

On startup, the app rebuilds the database only when `pn.db` is missing or older than 7 days.
Set `NANPA_REFRESH_ON_START=1` to always refresh on launch.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NANPA_HOST` | `127.0.0.1` | Flask host |
| `NANPA_PORT` | `5000` | Flask port |
| `FLASK_DEBUG` | `0` | Enable Flask debug mode |
| `NANPA_REFRESH_ON_START` | `0` | Force refresh at startup |
| `NANPA_DB_MAX_AGE_DAYS` | `7` | Auto-refresh threshold |
| `NANPA_REQUESTS_VERIFY` | `0` | TLS cert verification for downloads |

## Project layout

```text
nanpa2/
  app/
    config.py
    constants.py
    database.py
    ingest.py
    maps.py
    routes/
  templates/
  static/
  run.py
  refresh_data.py
```

## Notes

- Map images and curated CSV lists are stored under `static/`.
- Generated NANPA download files and `pn.db` are gitignored.
