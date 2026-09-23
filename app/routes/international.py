from fastapi import APIRouter, Query, Request

from app.database import fetch_all, fetch_one, row_to_dict
from app.international import (
    dialing_display,
    is_nanp_member,
    itu_references,
    map_dial_label,
    special_numbering_summaries,
    validate_phone_number,
)
from app.international_currencies import primary_currency
from app.templating import render

router = APIRouter()

_INTL_COUNTRY_SORT_SQL = {
    "name": "name COLLATE NOCASE",
    "iso2": "iso2",
    "dial_code": "CAST(NULLIF(dial_code, '') AS INTEGER), dial_code",
    "continent": "continent COLLATE NOCASE",
    "exit_code": "exit_code",
}


def _intl_country_sort(sort: str, direction: str) -> tuple[str, str]:
    sort_key = (sort or "name").strip().lower()
    if sort_key not in _INTL_COUNTRY_SORT_SQL:
        sort_key = "name"
    sort_dir = "desc" if (direction or "").strip().lower() == "desc" else "asc"
    return sort_key, sort_dir


def _table_exists() -> bool:
    row = fetch_one(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'intl_country'"
    )
    return row is not None


@router.get("/international", name="international.index")
def international_index(
    request: Request,
    continent: str = Query(""),
    q: str = Query(""),
    sort: str | None = Query(None),
    dir: str | None = Query(None),
):
    if not _table_exists():
        return render(
            request,
            "error.html",
            {
                "error": "International data is not loaded yet. Use Update data now on the home page.",
                "page_header": "International Numbering",
            },
            503,
        )

    params: list = []
    clauses = []
    continent = continent.strip()
    q = q.strip()

    if continent:
        clauses.append("continent = ?")
        params.append(continent)
    if q:
        clauses.append("(name LIKE ? OR dial_code LIKE ? OR iso2 LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    if "sort" in request.query_params:
        sort_key, sort_dir = _intl_country_sort(sort or "name", dir or "asc")
    else:
        sort_key, sort_dir = "name", "asc"
    order_sql = _INTL_COUNTRY_SORT_SQL[sort_key]
    order_clause = f"ORDER BY {order_sql} {sort_dir.upper()}, iso2 ASC"
    countries = fetch_all(
        f"SELECT * FROM intl_country {where} {order_clause}",
        params,
    )
    continents = fetch_all(
        "SELECT DISTINCT continent FROM intl_country WHERE continent IS NOT NULL ORDER BY continent"
    )

    map_rows = fetch_all(
        """
        SELECT iso2, name, dial_code, national_length_min, national_length_max, nanp_linked
        FROM intl_country ORDER BY name
        """
    )
    map_countries = []
    for row in map_rows:
        country_dict = row_to_dict(row)
        map_countries.append(
            {
                "iso2": country_dict["iso2"],
                "name": country_dict["name"],
                "min": country_dict["national_length_min"],
                "max": country_dict["national_length_max"],
                "dialLabel": map_dial_label(country_dict),
                "url": str(request.url_for("international.country", iso2=country_dict["iso2"])),
            }
        )

    country_rows = [row_to_dict(row) for row in countries]
    for country in country_rows:
        country["dialing"] = dialing_display(country)

    return render(
        request,
        "international/index.html",
        {
            "countries": country_rows,
            "map_countries": map_countries,
            "continents": [row["continent"] for row in continents],
            "selected_continent": continent,
            "search_query": q,
            "sort": sort_key,
            "sort_dir": sort_dir,
            "itu_references": itu_references(),
            "page_header": "International Numbering",
        },
    )


@router.get("/international/{iso2}", name="international.country")
def international_country(
    request: Request,
    iso2: str,
    phone: str = Query(""),
):
    if not _table_exists():
        return render(
            request,
            "error.html",
            {
                "error": "International data is not loaded yet. Use Update data now on the home page.",
                "page_header": "International Numbering",
            },
            503,
        )

    iso2 = iso2.strip().upper()
    country = fetch_one("SELECT * FROM intl_country WHERE iso2 = ?", (iso2,))
    if not country:
        return render(
            request,
            "error.html",
            {"error": f"Country code {iso2} was not found.", "page_header": "International Numbering"},
            404,
        )

    country_dict = row_to_dict(country)
    dialing = dialing_display(country_dict)

    if is_nanp_member(iso2):
        same_code = fetch_all(
            """
            SELECT iso2, name FROM intl_country
            WHERE (dial_code = '1' OR dial_code LIKE '1-%') AND iso2 != ?
            ORDER BY name
            """,
            (iso2,),
        )
    else:
        same_code = fetch_all(
            "SELECT iso2, name FROM intl_country WHERE dial_code = ? AND iso2 != ? ORDER BY name",
            (country_dict["dial_code"], iso2),
        )

    validation = validate_phone_number(phone, iso2) if phone else None

    if (
        dialing["nanp_member"]
        and dialing["nanp_area_code"]
        and not country_dict.get("nanp_linked")
    ):
        page_header = f"{country_dict['name']} (+{dialing['e164']} {dialing['nanp_area_code']})"
    else:
        page_header = f"{country_dict['name']} (+{dialing['e164']})"

    return render(
        request,
        "international/country.html",
        {
            "country": country_dict,
            "dialing": dialing,
            "same_code_countries": [row_to_dict(row) for row in same_code],
            "special_numbering": special_numbering_summaries(iso2),
            "primary_currency": primary_currency(iso2),
            "validation": validation,
            "phone_query": phone,
            "itu_references": itu_references(),
            "page_header": page_header,
        },
    )
