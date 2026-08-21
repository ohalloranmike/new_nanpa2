import csv
import os
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import requests

from app.config import Config
from app.database import db_connection

ProgressCallback = Callable[[str, str, int], None]


def _sanitize_header(value: str) -> str:
    value = value.replace("-", "").replace("/", "").replace("(", "").replace(")", "").replace(" ", "")
    return re.sub(r"[^\w]", "", value)


def _unique_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for header in headers:
        name = header or "column"
        if name not in seen:
            seen[name] = 1
            unique.append(name)
            continue
        seen[name] += 1
        unique.append(f"{name}_{seen[name]}")
    return unique


def _clean_rows(rows: list[list[str]]) -> list[list[str]]:
    cleaned = []
    for row in rows:
        cleaned.append([item.replace("'", "").replace('"', "").strip() for item in row])
    return cleaned


def _report(progress: ProgressCallback | None, stage: str, message: str, percent: int) -> None:
    if progress:
        progress(stage, message, percent)


def _download(url: str, destination: Path, verify: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, allow_redirects=True, verify=verify, timeout=120)
    response.raise_for_status()
    destination.write_bytes(response.content)


def _create_table(conn, table_name: str, headers: list[str]) -> None:
    columns = ", ".join(f'"{header}" text' for header in headers)
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute(f"CREATE TABLE {table_name} ({columns})")


def _insert_rows(conn, table_name: str, rows: list[list[str]]) -> None:
    if not rows:
        return
    placeholders = ", ".join("?" for _ in rows[0])
    conn.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)


def _create_indexes(conn) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_oc_npanxx ON oc(NPANXX)",
        "CREATE INDEX IF NOT EXISTS idx_oc_state ON oc(State)",
        "CREATE INDEX IF NOT EXISTS idx_oc_ocn ON oc(OCN)",
        "CREATE INDEX IF NOT EXISTS idx_oc_ratecenter ON oc(RateCenter)",
        "CREATE INDEX IF NOT EXISTS idx_ac_npa ON ac(NPA_ID)",
        "CREATE INDEX IF NOT EXISTS idx_ac_location ON ac(LOCATION)",
        "CREATE INDEX IF NOT EXISTS idx_caoc_npa_nxx ON caoc(NPA, COCodeNXX)",
        "CREATE INDEX IF NOT EXISTS idx_caoc_ocn ON caoc(OCN)",
        "CREATE INDEX IF NOT EXISTS idx_caoc_exchange ON caoc(ExchangeArea)",
        "CREATE INDEX IF NOT EXISTS idx_caoc_province ON caoc(Province)",
    ]
    for statement in indexes:
        try:
            conn.execute(statement)
        except Exception:
            pass


def _source_files(config: Config) -> list[Path]:
    nanpa_dir = config.NANPA_DIR
    return [
        nanpa_dir / "npa_report.csv",
        nanpa_dir / "CoCodeAssignment_Utilized_AllStates_Public.txt",
        nanpa_dir / "COCodeStatus_ALL.csv",
    ]


def _file_age_days(path: Path) -> float | None:
    if not path.exists():
        return None
    return (time.time() - path.stat().st_mtime) / 86400


def source_files_are_fresh(config: Config) -> bool:
    max_age_days = config.DB_MAX_AGE_DAYS
    for path in _source_files(config):
        age_days = _file_age_days(path)
        if age_days is None or age_days >= max_age_days:
            return False
    return True


def database_timestamp(config: Config) -> str:
    db_path = config.DB_PATH
    if not db_path.exists():
        return "Not built yet"
    return datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def database_is_fresh(config: Config) -> bool:
    db_path = config.DB_PATH
    if not db_path.exists():
        return False
    age_seconds = time.time() - db_path.stat().st_mtime
    return age_seconds < config.DB_MAX_AGE_DAYS * 86400


def _download_sources(config: Config, progress: ProgressCallback | None = None) -> None:
    verify = config.REQUESTS_VERIFY
    npa_csv = config.NANPA_DIR / "npa_report.csv"
    us_oc_zip = config.NANPA_DIR / "CoCodeAssignment_Utilized_AllStates_Public.zip"
    ca_oc_zip = config.NANPA_DIR / "COCodeStatus_ALL.zip"

    _report(progress, "download_npa", "Downloading area code report from NANPA...", 10)
    _download(config.NANPA_NPA_URL, npa_csv, verify)

    _report(progress, "download_us_oc", "Downloading US office code assignment from NANPA...", 25)
    _download(config.NANPA_OC_ZIP_URL, us_oc_zip, verify)

    _report(progress, "extract_us_oc", "Extracting US office code file...", 35)
    with ZipFile(us_oc_zip, "r") as archive:
        archive.extractall(config.NANPA_DIR)

    _report(progress, "download_ca_oc", "Downloading Canada office code status from CNAC...", 50)
    _download(config.CNAC_OC_ZIP_URL, ca_oc_zip, verify)

    _report(progress, "extract_ca_oc", "Extracting Canada office code file...", 60)
    with ZipFile(ca_oc_zip, "r") as archive:
        archive.extractall(config.NANPA_DIR)


def _rebuild_database(config: Config, progress: ProgressCallback | None = None) -> None:
    npa_csv = config.NANPA_DIR / "npa_report.csv"
    us_oc_txt = config.NANPA_DIR / "CoCodeAssignment_Utilized_AllStates_Public.txt"
    ca_oc_csv = config.NANPA_DIR / "COCodeStatus_ALL.csv"

    with db_connection(config.DB_PATH) as conn:
        _report(progress, "load_us_oc", "Loading US office codes into SQLite...", 70)
        _load_us_office_codes(conn, us_oc_txt)

        _report(progress, "load_ac", "Loading area codes into SQLite...", 80)
        _load_area_codes(conn, npa_csv)

        _report(progress, "load_ca_oc", "Loading Canada office codes into SQLite...", 88)
        _load_canada_office_codes(conn, ca_oc_csv)

        _report(progress, "load_ocn", "Building operating company index...", 94)
        _load_ocn_table(conn)

        _report(progress, "indexes", "Creating database indexes...", 97)
        _create_indexes(conn)


def refresh_database(
    config: Config | None = None,
    force: bool = False,
    progress: ProgressCallback | None = None,
) -> Path:
    config = config or Config()
    config.NANPA_DIR.mkdir(parents=True, exist_ok=True)

    need_download = force or not source_files_are_fresh(config)
    need_rebuild = (
        force
        or need_download
        or not config.DB_PATH.exists()
        or not database_is_fresh(config)
    )

    if not need_download and not need_rebuild:
        _report(progress, "uptodate", "Data is already up to date.", 100)
        return config.DB_PATH

    _report(progress, "start", "Starting data refresh...", 0)

    try:
        if need_download:
            _download_sources(config, progress)
        else:
            _report(
                progress,
                "skip_download",
                "Source files are current; skipping downloads.",
                65,
            )

        if need_rebuild:
            _rebuild_database(config, progress)

        _report(progress, "complete", "Update complete.", 100)
    except Exception as exc:
        _report(progress, "error", f"Update failed: {exc}", 0)
        raise

    return config.DB_PATH


def _load_us_office_codes(conn, path: Path) -> None:
    with path.open("r", newline="\n", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))

    headers = rows[0]
    if headers and headers[-1].strip().lower().startswith("file updated"):
        headers = headers[:-1]

    fixed_headers = _unique_headers([_sanitize_header(item) for item in headers])
    _create_table(conn, "oc", fixed_headers)
    data = _clean_rows(rows[1:])
    _insert_rows(conn, "oc", data)


def _load_area_codes(conn, path: Path) -> None:
    with path.open("r", newline="\n", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter=","))

    rows.pop(0)  # file date row
    headers = rows.pop(0)
    _create_table(conn, "ac", headers)
    data = _clean_rows(rows)

    normalized = []
    for row in data:
        if len(row) == 17:
            row.extend([""] * 15)
        if len(row) == 33:
            row.pop(22)
        if len(row) != 32:
            continue
        normalized.append(row)

    _insert_rows(conn, "ac", normalized)


def _load_canada_office_codes(conn, path: Path) -> None:
    with path.open("r", newline="\n", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter=","))

    headers = [_sanitize_header(item) for item in rows[0]]
    _create_table(conn, "caoc", headers)
    data = _clean_rows(rows[2:])  # skip header and blank metadata row
    expected = len(headers)
    valid_rows = [row[:expected] + [""] * max(0, expected - len(row)) for row in data if row]
    valid_rows = [row[:expected] for row in valid_rows]
    _insert_rows(conn, "caoc", valid_rows)


def _load_ocn_table(conn) -> None:
    conn.execute("DROP TABLE IF EXISTS ocn")
    conn.execute("CREATE TABLE ocn (OCN text, Company text)")
    rows = conn.execute(
        "SELECT DISTINCT OCN, Company FROM oc WHERE OCN IS NOT NULL AND OCN != '' ORDER BY Company, OCN"
    ).fetchall()
    conn.executemany("INSERT INTO ocn VALUES (?, ?)", [(row[0], row[1]) for row in rows])
