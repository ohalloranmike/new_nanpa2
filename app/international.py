import json
import sqlite3
from pathlib import Path

import phonenumbers
import requests

from phonenumbers import PhoneNumberType

from app.config import Config
from app.international_regulators import ITU_REFERENCES, NANP_ISO2, REGULATORS

INTERNATIONAL_FILENAME = "international_countries.json"

_TYPE_LABELS = {
    PhoneNumberType.MOBILE: "mobile",
    PhoneNumberType.FIXED_LINE: "fixed line",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed line or mobile",
    PhoneNumberType.TOLL_FREE: "toll free",
    PhoneNumberType.PREMIUM_RATE: "premium rate",
    PhoneNumberType.SHARED_COST: "shared cost",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.PERSONAL_NUMBER: "personal number",
    PhoneNumberType.PAGER: "pager",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "voicemail",
}


def international_source_path(config: Config) -> Path:
    return config.NANPA_DIR / INTERNATIONAL_FILENAME


def download_international_data(config: Config, verify: bool) -> Path:
    destination = international_source_path(config)
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(config.INTERNATIONAL_DATA_URL, allow_redirects=True, verify=verify, timeout=120)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def _national_length_range(iso2: str) -> tuple[int | None, int | None]:
    try:
        metadata = phonenumbers.PhoneMetadata.metadata_for_region(iso2)
    except Exception:
        return None, None
    if metadata is None or metadata.general_desc is None:
        return None, None
    lengths = list(metadata.general_desc.possible_length or [])
    if not lengths:
        return None, None
    return min(lengths), max(lengths)


def _lib_example_number(iso2: str) -> str | None:
    try:
        example = phonenumbers.example_number(iso2)
    except Exception:
        return None
    if example is None:
        return None
    return phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.INTERNATIONAL)


def _normalize_record(entry: dict) -> dict | None:
    iso2 = (entry.get("iso2") or "").strip().upper()
    name = (entry.get("name") or "").strip()
    dial_code = (entry.get("dial_code") or "").strip()
    if not iso2 or not name or not dial_code:
        return None

    length_min, length_max = _national_length_range(iso2)
    regulator = REGULATORS.get(iso2, {})
    example_mobile = (entry.get("example_mobile") or "").strip() or None
    example_landline = (entry.get("example_landline") or "").strip() or None
    lib_example = _lib_example_number(iso2)

    return {
        "iso2": iso2,
        "name": name,
        "dial_code": dial_code,
        "continent": (entry.get("continent") or "").strip() or None,
        "exit_code": (entry.get("exit_code") or "").strip() or None,
        "trunk_prefix": (entry.get("trunk_prefix") or "").strip() or None,
        "mobile_prefix": (entry.get("mobile_prefix") or "").strip() or None,
        "landline_prefix": (entry.get("landline_prefix") or "").strip() or None,
        "example_mobile": example_mobile,
        "example_landline": example_landline,
        "lib_example": lib_example,
        "international_format": (entry.get("international_format") or "").strip() or None,
        "national_length_min": length_min,
        "national_length_max": length_max,
        "regulator_name": regulator.get("name"),
        "regulator_url": regulator.get("url"),
        "nanp_linked": 1 if iso2 in NANP_ISO2 else 0,
    }


def load_international_countries(conn: sqlite3.Connection, source_path: Path) -> int:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("International country data must be a JSON array")

    conn.execute("DROP TABLE IF EXISTS intl_country")
    conn.execute(
        """
        CREATE TABLE intl_country (
            iso2 TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            dial_code TEXT NOT NULL,
            continent TEXT,
            exit_code TEXT,
            trunk_prefix TEXT,
            mobile_prefix TEXT,
            landline_prefix TEXT,
            example_mobile TEXT,
            example_landline TEXT,
            lib_example TEXT,
            international_format TEXT,
            national_length_min INTEGER,
            national_length_max INTEGER,
            regulator_name TEXT,
            regulator_url TEXT,
            nanp_linked INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    rows = []
    for entry in payload:
        record = _normalize_record(entry)
        if record:
            rows.append(record)

    conn.executemany(
        """
        INSERT INTO intl_country (
            iso2, name, dial_code, continent, exit_code, trunk_prefix,
            mobile_prefix, landline_prefix, example_mobile, example_landline,
            lib_example, international_format, national_length_min, national_length_max,
            regulator_name, regulator_url, nanp_linked
        ) VALUES (
            :iso2, :name, :dial_code, :continent, :exit_code, :trunk_prefix,
            :mobile_prefix, :landline_prefix, :example_mobile, :example_landline,
            :lib_example, :international_format, :national_length_min, :national_length_max,
            :regulator_name, :regulator_url, :nanp_linked
        )
        """,
        rows,
    )

    conn.execute("CREATE INDEX IF NOT EXISTS idx_intl_dial_code ON intl_country(dial_code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_intl_continent ON intl_country(continent)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_intl_name ON intl_country(name)")
    return len(rows)


def validate_phone_number(phone: str, iso2: str) -> dict:
    iso2 = iso2.strip().upper()
    phone = phone.strip()
    if not phone:
        return {"valid": False, "message": "Enter a phone number to validate."}

    try:
        parsed = phonenumbers.parse(phone, iso2)
    except phonenumbers.NumberParseException as exc:
        return {"valid": False, "message": str(exc)}

    valid = phonenumbers.is_valid_number_for_region(parsed, iso2)
    possible = phonenumbers.is_possible_number(parsed)
    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    number_type = phonenumbers.number_type(parsed)
    type_label = _TYPE_LABELS.get(number_type, "unknown")

    if valid:
        message = f"Valid {type_label} number for {iso2}."
    elif possible:
        message = f"Possible but not fully valid {type_label} number for {iso2}."
    else:
        message = f"Not a valid number for {iso2}."

    return {
        "valid": valid,
        "possible": possible,
        "message": message,
        "formatted": formatted,
        "e164": e164,
        "type": type_label,
    }


def itu_references() -> list[dict[str, str]]:
    return ITU_REFERENCES
