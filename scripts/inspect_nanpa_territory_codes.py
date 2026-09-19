"""Print NANPA source codes for US territories from live downloads and local DB."""

from __future__ import annotations

import csv
import sqlite3
import sys
from io import StringIO
from pathlib import Path
from zipfile import ZipFile

import requests

ROOT = Path(__file__).resolve().parent.parent
NANPA_DIR = ROOT / "static" / "NANPA"
DB_PATH = NANPA_DIR / "pn.db"

TERRITORY_NPAS = ("340", "670", "671", "684", "787", "939")

NPA_URL = "https://reports.nanpa.com/public/npa_report.csv"
OC_ZIP_URL = "https://reports.nanpa.com/public/CoCodeAssignment_Utilized_AllStates_Public.zip"


def inspect_db() -> None:
    if not DB_PATH.exists():
        print("No local pn.db")
        return
    conn = sqlite3.connect(DB_PATH)
    print("=== pn.db ac (LOCATION) ===")
    for row in conn.execute(
        "SELECT NPA_ID, LOCATION, COUNTRY FROM ac WHERE NPA_ID IN ("
        + ",".join("?" * len(TERRITORY_NPAS))
        + ") ORDER BY NPA_ID",
        TERRITORY_NPAS,
    ):
        print(row)
    print("=== pn.db oc (State) by NPA prefix ===")
    for row in conn.execute(
        """
        SELECT DISTINCT substr(NPANXX, 1, 3) AS npa, State
        FROM oc
        WHERE substr(NPANXX, 1, 3) IN ("""
        + ",".join("?" * len(TERRITORY_NPAS))
        + """)
        ORDER BY npa, State
        """,
        TERRITORY_NPAS,
    ):
        print(row)


def inspect_npa_csv(verify: bool) -> None:
    print("=== npa_report.csv (Location) ===")
    response = requests.get(NPA_URL, timeout=120, verify=verify)
    response.raise_for_status()
    rows = list(csv.reader(StringIO(response.text)))
    headers = rows[1]
    loc_idx = headers.index("LOCATION")
    country_idx = headers.index("Country")
    for row in rows[2:]:
        if row and row[0] in TERRITORY_NPAS:
            print((row[0], row[loc_idx], row[country_idx]))


def inspect_oc_file(verify: bool) -> None:
    print("=== CoCodeAssignment State column ===")
    response = requests.get(OC_ZIP_URL, timeout=120, verify=verify)
    response.raise_for_status()
    with ZipFile(__import__("io").BytesIO(response.content)) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".txt"))
        text = archive.read(name).decode("utf-8")
    rows = list(csv.reader(StringIO(text), delimiter="\t"))
    headers = rows[0]
    if headers[-1].strip().lower().startswith("file updated"):
        headers = headers[:-1]
    state_idx = next(i for i, h in enumerate(headers) if h.strip().lower() == "state")
    npanxx_idx = next(i for i, h in enumerate(headers) if "npanxx" in h.lower().replace(" ", ""))
    seen: set[tuple[str, str]] = set()
    for row in rows[1:]:
        if len(row) <= max(state_idx, npanxx_idx):
            continue
        npanxx = row[npanxx_idx].strip()
        if len(npanxx) >= 3 and npanxx[:3] in TERRITORY_NPAS:
            key = (npanxx[:3], row[state_idx].strip())
            if key not in seen:
                seen.add(key)
                print(key)


def main() -> None:
    verify = "--verify" in sys.argv
    inspect_db()
    inspect_npa_csv(verify)
    inspect_oc_file(verify)


if __name__ == "__main__":
    main()
