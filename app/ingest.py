import csv
import os
import re
import time
from pathlib import Path
from zipfile import ZipFile

import requests

from app.config import Config
from app.database import db_connection


def _sanitize_header(value: str) -> str:
    value = value.replace("-", "").replace("/", "").replace("(", "").replace(")", "").replace(" ", "")
    return re.sub(r"[^\w]", "", value)


def _clean_rows(rows: list[list[str]]) -> list[list[str]]:
    cleaned = []
    for row in rows:
        cleaned.append([item.replace("'", "").replace('"', "").strip() for item in row])
    return cleaned


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


def database_is_fresh(config: Config) -> bool:
    db_path = config.DB_PATH
    if not db_path.exists():
        return False
    age_seconds = time.time() - db_path.stat().st_mtime
    return age_seconds < config.DB_MAX_AGE_DAYS * 86400


def refresh_database(config: Config | None = None, force: bool = False) -> Path:
    config = config or Config()
    config.NANPA_DIR.mkdir(parents=True, exist_ok=True)

    if not force and database_is_fresh(config):
        return config.DB_PATH

    verify = config.REQUESTS_VERIFY
    npa_csv = config.NANPA_DIR / "npa_report.csv"
    us_oc_zip = config.NANPA_DIR / "CoCodeAssignment_Utilized_AllStates_Public.zip"
    us_oc_txt = config.NANPA_DIR / "CoCodeAssignment_Utilized_AllStates_Public.txt"
    ca_oc_zip = config.NANPA_DIR / "COCodeStatus_ALL.zip"
    ca_oc_csv = config.NANPA_DIR / "COCodeStatus_ALL.csv"

    _download(config.NANPA_NPA_URL, npa_csv, verify)
    _download(config.NANPA_OC_ZIP_URL, us_oc_zip, verify)
    with ZipFile(us_oc_zip, "r") as archive:
        archive.extractall(config.NANPA_DIR)

    _download(config.CNAC_OC_ZIP_URL, ca_oc_zip, verify)
    with ZipFile(ca_oc_zip, "r") as archive:
        archive.extractall(config.NANPA_DIR)

    with db_connection(config.DB_PATH) as conn:
        _load_us_office_codes(conn, us_oc_txt)
        _load_area_codes(conn, npa_csv)
        _load_canada_office_codes(conn, ca_oc_csv)
        _load_ocn_table(conn)
        _create_indexes(conn)

    return config.DB_PATH


def _load_us_office_codes(conn, path: Path) -> None:
    with path.open("r", newline="\n", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))

    headers = rows[0]
    headers[-1] = "InService"
    fixed_headers = [_sanitize_header(item) for item in headers]
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
