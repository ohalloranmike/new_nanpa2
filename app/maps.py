"""Map file resolution for states, territories, Canada, and countries."""

from app.config import Config

TERRITORY_MAPS = {
    "PR": "Puerto_Rico_787_939.gif",
    "AS": "American_Samoa_684.gif",
    "GU": "Guam_671.gif",
    "CNMI": "Northern_Marianna_Islands_670.gif",
    "VI": "US_Virgin_Islands_340.gif",
}

CANADA_MAPS = {
    "QUEBEC": "qc-s.png",
    "BRITISH COLUMBIA": "bc-s.png",
    "ONTARIO": "on-s.png",
}

COUNTRY_MAPS = {
    "JAMAICA": "Jamaica_876.gif",
    "BAHAMAS": "Bahamas_242.gif",
    "BARBADOS": "Barbados_246.gif",
    "ANGUILLA": "Anguilla_264.gif",
    "ANTIGUA/BARBUDA": "Antigua_and_Barbuda_268.gif",
    "BRITISH VIRGIN ISLANDS": "British_Virgin_Islands_284.gif",
    "CAYMAN ISLANDS": "Cayman_Islands_345.gif",
    "BERMUDA": "Bermuda_441.gif",
    "GRENADA": "Grenada_473.gif",
    "TURKS & CAICOS ISLANDS": "Turks_and_Caicos_Islands_649.gif",
    "MONTSERRAT": "Montserrat_664.gif",
    "SINT MAARTEN": "Sint_Maarten_721.gif",
    "ST. LUCIA": "Saint_Lucia_758.gif",
    "DOMINICA": "Dominica_767.gif",
    "ST. VINCENT & GRENADINES": "Saint_Vincent_and_The_Grenadines_784.gif",
    "DOMINICAN REPUBLIC": "Dominican_Republic_809_829_849.gif",
    "TRINIDAD & TOBAGO": "Trinidad_and_Tobago_868.gif",
    "ST. KITTS & NEVIS": "Saint_Kitts_and_Nevis_869.gif",
}


def country_map_for_location(location: str) -> str:
    if not location:
        return ""
    if location in COUNTRY_MAPS:
        return COUNTRY_MAPS[location]
    for key, value in COUNTRY_MAPS.items():
        if key in location or location in key:
            return value
    return ""


def canada_map_for_location(location: str) -> str:
    return CANADA_MAPS.get(location, "")


def canada_map_images(location: str = "") -> list[str]:
    images = []
    province_map = canada_map_for_location(location)
    if province_map:
        images.append(province_map)
    images.extend(["canada.png", "canadapt.png"])
    return images


def territory_map_for_code(code: str) -> str:
    return TERRITORY_MAPS.get(code, "")


def us_state_map_images(state_code: str) -> list[str]:
    static_dir = Config().STATIC_DIR
    candidates = [
        ("USACMaps", f"{state_code}.gif"),
        ("USACMaps", f"{state_code}-inset1.gif"),
        ("USACMaps", f"{state_code}-inset2.gif"),
        ("USStateMaps", f"{state_code}.png"),
    ]
    return [
        f"{folder}/{filename}"
        for folder, filename in candidates
        if (static_dir / folder / filename).is_file()
    ]
