"""Regulatory bodies for NANP numbering (US, territories, Canada, Caribbean members)."""

from __future__ import annotations

from app.constants import CANADA_PT, COUNTRIES, STATES, US_TERRITORIES

NANPA_US = {
    "name": "North American Numbering Plan Administrator (NANPA)",
    "url": "https://www.nanpa.com/",
}

CANADIAN_NUMBERING_ADMIN = {
    "name": "Canadian Numbering Administrator (CNA)",
    "url": "https://www.cnac.ca/index.htm",
}

# Keys match COUNTRIES / ac.LOCATION (see app/maps.py COUNTRY_MAPS).
NANP_MEMBER_REGULATORS: dict[str, dict[str, str]] = {
    "ANGUILLA": {
        "name": "Public Utilities Commission, Anguilla",
        "url": "https://pucanguilla.com/",
    },
    "ANTIGUA/BARBUDA": {
        "name": "Ministry of Information, Communication Technologies, Utilities and Energy",
        "url": "https://ab.gov.ag/detail_template.php?page=government_info%2Fmin_information",
    },
    "BAHAMAS": {
        "name": "Utilities Regulation and Competition Authority (URCA)",
        "url": "https://urcabahamas.bs/",
    },
    "BARBADOS": {
        "name": "Telecommunications Unit, Government of Barbados",
        # telecoms.gov.bb currently serves an expired TLS certificate; gov.bb is the live portal.
        "url": "https://www.gov.bb/Departments/telecommunications",
    },
    "BERMUDA": {
        "name": "Regulatory Authority of Bermuda",
        "url": "https://www.ra.bm/",
    },
    "BRITISH VIRGIN ISLANDS": {
        "name": "Telecommunications Regulatory Commission (TRC)",
        "url": "https://www.trc.vg/",
    },
    "CAYMAN ISLANDS": {
        "name": "Utility Regulation and Competition Office (OfReg)",
        "url": "https://www.ofreg.ky/",
    },
    "DOMINICA": {
        "name": "National Telecommunications Regulatory Commission (NTRC)",
        "url": "https://ntrcdom.org/",
    },
    "DOMINICAN REPUBLIC": {
        "name": "Instituto Dominicano de las Telecomunicaciones (INDOTEL)",
        "url": "https://indotel.gob.do/",
    },
    "GRENADA": {
        "name": "National Telecommunications Regulatory Commission (NTRC)",
        "url": "https://ntrc.gd/",
    },
    "JAMAICA": {
        "name": "Office of Utilities Regulation (OUR)",
        "url": "https://our.org.jm/",
    },
    "MONTSERRAT": {
        "name": "Montserrat Info-Communications Authority (MICA)",
        "url": "https://www.mica.ms/",
    },
    "SINT MAARTEN": {
        "name": "Bureau Telecommunications and Post (BTP)",
        "url": "https://btp.sx/",
    },
    "ST. KITTS & NEVIS": {
        "name": "National Telecommunications Regulatory Commission (NTRC)",
        "url": "https://www.ntrc.kn/",
    },
    "ST. LUCIA": {
        "name": "National Telecommunications Regulatory Commission (NTRC)",
        "url": "https://www.ntrcslu.lc/",
    },
    "ST. VINCENT & GRENADINES": {
        "name": "National Telecommunications Regulatory Commission (NTRC)",
        "url": "https://www.ntrc.vc/",
    },
    "TRINIDAD & TOBAGO": {
        "name": "Telecommunications Authority of Trinidad and Tobago (TATT)",
        "url": "https://tatt.org.tt/",
    },
    "TURKS & CAICOS ISLANDS": {
        "name": "Turks and Caicos Islands Telecommunications Commission",
        "url": "https://telecommission.tc/",
    },
}


def _regulator_for_location_key(location: str) -> dict[str, str] | None:
    if not location:
        return None
    key = location.strip().upper()
    if key in NANP_MEMBER_REGULATORS:
        return NANP_MEMBER_REGULATORS[key]
    for country_key, regulator in NANP_MEMBER_REGULATORS.items():
        if country_key in key or key in country_key:
            return regulator
    return None


def regulator_for_browse_state(state: str) -> dict[str, str]:
    """Resolve regulator for /acmaps?state= browse keys."""
    if state in STATES or state in US_TERRITORIES:
        return NANPA_US
    if state in CANADA_PT:
        return CANADIAN_NUMBERING_ADMIN
    if state in COUNTRIES:
        return NANP_MEMBER_REGULATORS[state]
    located = _regulator_for_location_key(state)
    if located:
        return located
    return NANPA_US


def regulator_for_area_code(country: str, location: str) -> dict[str, str]:
    """Resolve regulator for /areacodes?npa= from ac.country and ac.LOCATION."""
    country_norm = (country or "").strip().upper()
    if country_norm == "US":
        return NANPA_US
    if country_norm == "CANADA":
        return CANADIAN_NUMBERING_ADMIN
    located = _regulator_for_location_key(location)
    if located:
        return located
    return NANPA_US
