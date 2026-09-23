"""Regenerate static/international/country_primary_currency.json from mledoze/countries."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "static" / "international" / "country_primary_currency.json"


def main() -> None:
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
        countries = json.load(response)

    mapping: dict[str, dict[str, str]] = {}
    for country in countries:
        iso2 = country.get("cca2")
        if not iso2:
            continue
        currencies = country.get("currencies") or {}
        if not currencies:
            continue
        code = next(iter(currencies.keys()))
        info = currencies[code]
        mapping[iso2.upper()] = {
            "code": code,
            "name": (info.get("name") or code).strip(),
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(mapping)} entries)")


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
