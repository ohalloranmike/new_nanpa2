from fastapi import APIRouter, Query, Request

from app.constants import (
    CANADA_PT,
    STATES,
    TERRITORY_STATE_ALIASES,
    US_OFFICE_USE,
    US_TERRITORIES,
)
from app.database import fetch_all, fetch_one, row_to_dict
from app.maps import (
    canada_map_for_location,
    country_map_for_location,
    territory_map_for_code,
    us_state_map_images,
)
from app.templating import render

router = APIRouter()


@router.get("/areacodes", name="lookup.area_codes")
def area_codes(request: Request, npa: str = Query("", min_length=0)):
    npa = npa.strip()
    if len(npa) != 3 or not npa.isdigit():
        return render(request, "error.html", {"error": "Please provide a valid 3-digit area code."}, 400)

    ac_row = fetch_one("SELECT * FROM ac WHERE NPA_ID = ?", (npa,))
    if not ac_row:
        return render(request, "error.html", {"error": f"Unable to find area code {npa}."}, 404)

    ac_data = row_to_dict(ac_row)
    location = ac_row["LOCATION"]
    country = ac_row["country"]
    office_codes_by_status = {}

    if country == "US":
        statuses = fetch_all(
            "SELECT DISTINCT Use FROM oc WHERE NPANXX LIKE ? ORDER BY Use",
            (f"{npa}-%",),
        )
        for status in statuses:
            codes = fetch_all(
                "SELECT SUBSTR(NPANXX, 5, 3) AS nxx FROM oc WHERE NPANXX LIKE ? AND Use = ? ORDER BY nxx",
                (f"{npa}-%", status["Use"]),
            )
            office_codes_by_status[status["Use"]] = [row["nxx"] for row in codes]

        if location in STATES:
            return render(
                request,
                "lookup/us_area_code.html",
                {
                    "npa": npa,
                    "ac": ac_data,
                    "state_name": STATES[location],
                    "state_code": location,
                    "office_codes_by_status": office_codes_by_status,
                    "map_images": us_state_map_images(location),
                },
            )

        territory_code = TERRITORY_STATE_ALIASES.get(location, location)
        if territory_code in US_TERRITORIES:
            return render(
                request,
                "lookup/territory_area_code.html",
                {
                    "npa": npa,
                    "ac": ac_data,
                    "state_name": US_TERRITORIES[territory_code],
                    "territory_code": territory_code,
                    "office_codes_by_status": office_codes_by_status,
                    "map_file": territory_map_for_code(territory_code),
                },
            )

    if country == "CANADA":
        statuses = fetch_all(
            "SELECT DISTINCT Status FROM caoc WHERE NPA = ? ORDER BY Status",
            (npa,),
        )
        for status in statuses:
            codes = fetch_all(
                "SELECT COCodeNXX FROM caoc WHERE NPA = ? AND Status = ? ORDER BY COCodeNXX",
                (npa, status["Status"]),
            )
            office_codes_by_status[status["Status"]] = [row["COCodeNXX"] for row in codes]

        province_abbr = CANADA_PT.get(location, "")
        return render(
            request,
            "lookup/canada_area_code.html",
            {
                "npa": npa,
                "ac": ac_data,
                "province_name": location,
                "province_abbr": province_abbr,
                "office_codes_by_status": office_codes_by_status,
                "map_file": canada_map_for_location(location),
            },
        )

    map_file = country_map_for_location(location)
    return render(
        request,
        "lookup/country_area_code.html",
        {
            "npa": npa,
            "ac": ac_data,
            "location": location,
            "map_file": map_file,
        },
    )


@router.get("/officecodes", name="lookup.office_codes")
def office_codes(request: Request, npa_nxx: str = Query("", alias="npa-nxx")):
    npanxx = npa_nxx.strip().upper()
    if len(npanxx) != 7 or npanxx[3] != "-":
        return render(request, "error.html", {"error": "Please provide office code as ###-###."}, 400)

    npa, nxx = npanxx.split("-", 1)
    oc_row = fetch_one("SELECT * FROM oc WHERE NPANXX = ?", (npanxx,))
    ca_row = None
    if not oc_row:
        ca_row = fetch_one("SELECT * FROM caoc WHERE NPA = ? AND COCodeNXX = ?", (npa, nxx))

    if not oc_row and not ca_row:
        return render(request, "error.html", {"error": f"Unable to find office code {npanxx}."}, 404)

    ac_row = fetch_one("SELECT * FROM ac WHERE NPA_ID = ?", (npa,))
    if not ac_row:
        return render(request, "error.html", {"error": f"Unable to find area code {npa}."}, 404)

    ac_data = row_to_dict(ac_row)

    if oc_row:
        oc_data = row_to_dict(oc_row)
        state = oc_row["State"]
        territory_code = TERRITORY_STATE_ALIASES.get(state, state)
        if state in STATES:
            return render(
                request,
                "lookup/us_office_code.html",
                {
                    "npanxx": npanxx,
                    "npa": npa,
                    "ac": ac_data,
                    "oc": oc_data,
                    "state_code": state,
                    "state_name": STATES[state],
                    "rate_center": oc_row["RateCenter"],
                    "ocn": oc_row["OCN"],
                    "company": oc_row["Company"],
                    "use_definitions": US_OFFICE_USE,
                },
            )
        if territory_code in US_TERRITORIES:
            return render(
                request,
                "lookup/territory_office_code.html",
                {
                    "npanxx": npanxx,
                    "npa": npa,
                    "ac": ac_data,
                    "oc": oc_data,
                    "territory_code": territory_code,
                    "territory_name": US_TERRITORIES[territory_code],
                    "rate_center": oc_row["RateCenter"],
                    "ocn": oc_row["OCN"],
                    "company": oc_row["Company"],
                    "use_definitions": US_OFFICE_USE,
                    "map_file": territory_map_for_code(territory_code),
                },
            )
        return render(request, "error.html", {"error": f"Unable to resolve state for {npanxx}."}, 404)

    ca_data = row_to_dict(ca_row)
    province = ca_row["Province"]
    return render(
        request,
        "lookup/canada_office_code.html",
        {
            "npanxx": npanxx,
            "npa": npa,
            "ac": ac_data,
            "oc": ca_data,
            "province": province,
            "exchange_area": ca_row["ExchangeArea"],
            "ocn": ca_row["OCN"],
            "company": ca_row["Company"],
            "map_file": canada_map_for_location(ac_row["LOCATION"]),
        },
    )
