from fastapi import APIRouter, Query, Request

from app.constants import CANADA_PT, STATES, US_STATE_QUERY_ALIASES, US_TERRITORIES
from app.database import fetch_all
from app.maps import canada_map_for_location, country_map_for_location, territory_map_for_code, us_state_map_images
from app.templating import render

router = APIRouter()


def _normalize_us_state(state: str) -> str:
    return US_STATE_QUERY_ALIASES.get(state.upper(), state.upper())


@router.get("/compstate", name="browse.companies_by_state")
def companies_by_state(request: Request, cs: str = Query("")):
    state = _normalize_us_state(cs.strip())
    if state not in STATES and state not in US_TERRITORIES:
        return render(request, "error.html", {"error": "Invalid state selection."}, 400)

    rows = fetch_all(
        "SELECT DISTINCT OCN, Company FROM oc WHERE State = ? ORDER BY Company, OCN",
        (state,),
    )
    return render(request, "browse/companies_by_state.html", {"state": state, "rows": rows})


@router.get("/rcstate", name="browse.rate_centers_by_state")
def rate_centers_by_state(request: Request, rcs: str = Query("")):
    state = _normalize_us_state(rcs.strip())
    if state not in STATES and state not in US_TERRITORIES:
        return render(request, "error.html", {"error": "Invalid state selection."}, 400)

    rows = fetch_all(
        "SELECT DISTINCT RateCenter FROM oc WHERE State = ? AND RateCenter != '' ORDER BY RateCenter",
        (state,),
    )
    return render(
        request,
        "browse/rate_centers_by_state.html",
        {
            "state": state,
            "rate_centers": [row["RateCenter"] for row in rows],
        },
    )


@router.get("/ratecenter", name="browse.rate_center_detail")
def rate_center_detail(
    request: Request,
    rc: str = Query(""),
    state: str = Query(""),
    country: str = Query(""),
):
    rate_center = rc.strip()
    state = state.strip()
    country = country.strip().upper()
    if not rate_center or not country:
        return render(request, "error.html", {"error": "Missing rate center parameters."}, 400)

    if country == "US":
        state = _normalize_us_state(state)
        by_npanxx = fetch_all(
            "SELECT NPANXX, Company FROM oc WHERE RateCenter = ? AND State = ? ORDER BY NPANXX",
            (rate_center, state),
        )
        by_company = fetch_all(
            "SELECT NPANXX, Company FROM oc WHERE RateCenter = ? AND State = ? ORDER BY Company, NPANXX",
            (rate_center, state),
        )
        return render(
            request,
            "browse/rate_center_us.html",
            {
                "rate_center": rate_center,
                "state": state,
                "by_npanxx": by_npanxx,
                "by_company": by_company,
            },
        )

    if country == "CANADA":
        by_npanxx = fetch_all(
            "SELECT NPA, COCodeNXX, Company FROM caoc WHERE ExchangeArea = ? ORDER BY NPA, COCodeNXX",
            (rate_center,),
        )
        by_company = fetch_all(
            "SELECT NPA, COCodeNXX, Company FROM caoc WHERE ExchangeArea = ? ORDER BY Company, NPA, COCodeNXX",
            (rate_center,),
        )
        return render(
            request,
            "browse/rate_center_canada.html",
            {
                "rate_center": rate_center,
                "state": state,
                "by_npanxx": by_npanxx,
                "by_company": by_company,
            },
        )

    return render(request, "error.html", {"error": "Unsupported country for rate center lookup."}, 400)


@router.get("/company", name="browse.company_detail")
def company_detail(
    request: Request,
    ocn: str = Query(""),
    companyname: str = Query(""),
    state: str = Query(""),
    country: str = Query(""),
):
    ocn = ocn.strip()
    company_name = companyname.strip()
    state = state.strip()
    country = country.strip().upper()
    if not ocn or not country:
        return render(request, "error.html", {"error": "Missing company parameters."}, 400)

    if country == "US":
        state = _normalize_us_state(state)
        by_npanxx = fetch_all(
            "SELECT NPANXX, RateCenter FROM oc WHERE OCN = ? AND State = ? ORDER BY NPANXX",
            (ocn, state),
        )
        by_rate_center = fetch_all(
            "SELECT NPANXX, RateCenter FROM oc WHERE OCN = ? AND State = ? ORDER BY RateCenter, NPANXX",
            (ocn, state),
        )
        return render(
            request,
            "browse/company_us.html",
            {
                "ocn": ocn,
                "company_name": company_name,
                "state": state,
                "by_npanxx": by_npanxx,
                "by_rate_center": by_rate_center,
            },
        )

    if country == "CANADA":
        by_npanxx = fetch_all(
            "SELECT NPA, COCodeNXX, ExchangeArea FROM caoc WHERE OCN = ? ORDER BY NPA, COCodeNXX",
            (ocn,),
        )
        by_exchange = fetch_all(
            "SELECT NPA, COCodeNXX, ExchangeArea FROM caoc WHERE OCN = ? ORDER BY ExchangeArea, NPA, COCodeNXX",
            (ocn,),
        )
        return render(
            request,
            "browse/company_canada.html",
            {
                "ocn": ocn,
                "company_name": company_name,
                "state": state,
                "by_npanxx": by_npanxx,
                "by_exchange": by_exchange,
            },
        )

    return render(request, "error.html", {"error": "Unsupported country for company lookup."}, 400)


@router.get("/acmaps", name="browse.area_code_maps")
def area_code_maps(request: Request, state: str = Query("")):
    state = state.strip().upper()
    if not state:
        return render(request, "error.html", {"error": "Please choose a state or region."}, 400)

    if state in STATES:
        npas = _npas_for_location(state)
        return render(
            request,
            "browse/maps_us_state.html",
            {
                "title": STATES[state],
                "state_code": state,
                "npas": npas,
                "map_images": us_state_map_images(state),
            },
        )

    if state in CANADA_PT:
        npas = _npas_for_location(state)
        return render(
            request,
            "browse/maps_canada.html",
            {
                "title": state.title(),
                "state_code": CANADA_PT[state],
                "npas": npas,
                "map_file": canada_map_for_location(state),
            },
        )

    if state in US_TERRITORIES:
        npas = _npas_for_location(state)
        return render(
            request,
            "browse/maps_territory.html",
            {
                "title": US_TERRITORIES[state],
                "territory_code": state,
                "npas": npas,
                "map_file": territory_map_for_code(state),
            },
        )

    if state == "DOMINICA":
        npas = _npas_for_location("DOMINICA")
    else:
        npas = _npas_like_location(state)

    map_file = country_map_for_location(state)
    return render(
        request,
        "browse/maps_country.html",
        {
            "title": state.replace("/", " / ").title(),
            "state": state,
            "npas": npas,
            "map_file": map_file,
        },
    )


def _npas_for_location(location: str) -> list[str]:
    rows = fetch_all("SELECT NPA_ID FROM ac WHERE LOCATION = ? ORDER BY NPA_ID", (location,))
    return [row["NPA_ID"] for row in rows]


def _npas_like_location(fragment: str) -> list[str]:
    rows = fetch_all("SELECT NPA_ID FROM ac WHERE LOCATION LIKE ? ORDER BY NPA_ID", (f"%{fragment}%",))
    return [row["NPA_ID"] for row in rows]
