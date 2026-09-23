"""Primary legal tender per ISO 3166-1 alpha-2 (bundled ISO 4217 mapping)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "static" / "international" / "country_primary_currency.json"


@lru_cache(maxsize=1)
def _currency_by_iso2() -> dict[str, dict[str, str]]:
    if not _DATA_PATH.is_file():
        return {}
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(key).upper(): value for key, value in payload.items()}


def primary_currency(iso2: str) -> dict[str, str] | None:
    """Return primary currency ``{code, name}`` for a country/territory, or None."""
    iso2 = (iso2 or "").strip().upper()
    if not iso2:
        return None
    entry = _currency_by_iso2().get(iso2)
    if not entry:
        return None
    code = (entry.get("code") or "").strip()
    name = (entry.get("name") or "").strip()
    if not code:
        return None
    return {"code": code, "name": name or code}
