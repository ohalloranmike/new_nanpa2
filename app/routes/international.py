from fastapi import APIRouter, Query, Request

from app.database import fetch_all, fetch_one, row_to_dict
from app.international import itu_references, validate_phone_number
from app.templating import render

router = APIRouter()


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
    countries = fetch_all(
        f"SELECT * FROM intl_country {where} ORDER BY name",
        params,
    )
    continents = fetch_all(
        "SELECT DISTINCT continent FROM intl_country WHERE continent IS NOT NULL ORDER BY continent"
    )

    return render(
        request,
        "international/index.html",
        {
            "countries": [row_to_dict(row) for row in countries],
            "continents": [row["continent"] for row in continents],
            "selected_continent": continent,
            "search_query": q,
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
    same_code = fetch_all(
        "SELECT iso2, name FROM intl_country WHERE dial_code = ? AND iso2 != ? ORDER BY name",
        (country_dict["dial_code"], iso2),
    )

    validation = validate_phone_number(phone, iso2) if phone else None

    return render(
        request,
        "international/country.html",
        {
            "country": country_dict,
            "same_code_countries": [row_to_dict(row) for row in same_code],
            "validation": validation,
            "phone_query": phone,
            "itu_references": itu_references(),
            "page_header": f"{country_dict['name']} (+{country_dict['dial_code']})",
        },
    )
