"""Build schematic us-territories.geojson from Natural Earth country boundaries."""

from __future__ import annotations

import json
import urllib.request
from copy import deepcopy
from pathlib import Path

NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)

# App browse codes (see app/constants.py US_TERRITORIES)
TERRITORY_ISO = {
    "PR": "PR",
    "VI": "VI",
    "GU": "GU",
    "MP": "CNMI",
    "AS": "AS",
}

TERRITORY_NAMES = {
    "PR": "PUERTO RICO",
    "VI": "US VIRGIN ISLANDS",
    "GU": "GUAM",
    "CNMI": "NORTHERN MARIANNA ISLANDS",
    "AS": "AMERICAN SAMOA",
}

# Schematic layout: (center_x, center_y, max_span) in arbitrary units
LAYOUT = {
    "PR": (240, 170, 220),
    "VI": (760, 165, 140),
    "GU": (210, 430, 170),
    "CNMI": (500, 420, 200),
    "AS": (790, 435, 165),
}


def iter_positions(geometry: dict):
    geom_type = geometry["type"]
    coords = geometry["coordinates"]
    if geom_type == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield lon, lat
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                for lon, lat in ring:
                    yield lon, lat
    else:
        raise ValueError(geom_type)


def map_positions(geometry: dict, mapper):
    geom = deepcopy(geometry)
    geom_type = geom["type"]
    if geom_type == "Polygon":
        geom["coordinates"] = [
            [list(mapper(lon, lat)) for lon, lat in ring] for ring in geom["coordinates"]
        ]
    elif geom_type == "MultiPolygon":
        geom["coordinates"] = [
            [[list(mapper(lon, lat)) for lon, lat in ring] for ring in polygon]
            for polygon in geom["coordinates"]
        ]
    return geom


def bbox(geometry: dict) -> tuple[float, float, float, float]:
    lons, lats = zip(*iter_positions(geometry))
    return min(lons), min(lats), max(lons), max(lats)


def place_geometry(geometry: dict, center_x: float, center_y: float, max_span: float) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox(geometry)
    width = max(max_lon - min_lon, 1e-9)
    height = max(max_lat - min_lat, 1e-9)
    span = max(width, height)
    scale = max_span / span
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2

    def mapper(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - mid_lon) * scale + center_x
        y = -(lat - mid_lat) * scale + center_y
        return [x, y]

    return map_positions(geometry, mapper)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out_path = root / "static" / "maps" / "us-territories.geojson"

    with urllib.request.urlopen(NE_URL, timeout=120) as response:
        collection = json.load(response)

    by_iso: dict[str, dict] = {}
    for feature in collection["features"]:
        iso = (feature.get("properties") or {}).get("ISO_A2") or ""
        if iso in TERRITORY_ISO:
            by_iso[iso] = feature

    missing = set(TERRITORY_ISO) - set(by_iso)
    if missing:
        raise SystemExit(f"Missing territories in Natural Earth data: {missing}")

    features = []
    for iso, code in TERRITORY_ISO.items():
        source = by_iso[iso]
        cx, cy, span = LAYOUT[code]
        geometry = place_geometry(source["geometry"], cx, cy, span)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "code": code,
                    "name": TERRITORY_NAMES[code],
                    "iso_a2": iso,
                },
                "geometry": geometry,
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {out_path} ({len(features)} features)")


if __name__ == "__main__":
    main()
