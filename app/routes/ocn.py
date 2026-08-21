from fastapi import APIRouter, Query, Request

from app.database import fetch_all, fetch_one
from app.templating import render

router = APIRouter()


@router.get("/ocnall", name="ocn.ocn_all")
def ocn_all(request: Request):
    rows = fetch_all(
        "SELECT DISTINCT Company, OCN, State FROM oc "
        "WHERE Company != '' AND OCN != '' ORDER BY Company, State, OCN"
    )
    return render(request, "ocn/all_us.html", {"rows": rows})


@router.get("/ocn", name="ocn.ocn_detail")
def ocn_detail(request: Request, ocn: str = Query("")):
    ocn = ocn.strip().upper()
    if not ocn:
        return render(request, "error.html", {"error": "Please provide an OCN."}, 400)

    company_row = fetch_one("SELECT Company FROM oc WHERE OCN = ? LIMIT 1", (ocn,))
    if not company_row:
        return render(request, "error.html", {"error": f"Unable to find OCN {ocn}."}, 404)

    by_npanxx = fetch_all(
        "SELECT NPANXX, State, RateCenter FROM oc WHERE OCN = ? ORDER BY NPANXX",
        (ocn,),
    )
    by_rate_center = fetch_all(
        "SELECT NPANXX, RateCenter, State FROM oc WHERE OCN = ? ORDER BY State, RateCenter, NPANXX",
        (ocn,),
    )
    by_state = fetch_all(
        "SELECT NPANXX, State, RateCenter FROM oc WHERE OCN = ? ORDER BY State, NPANXX",
        (ocn,),
    )
    return render(
        request,
        "ocn/detail.html",
        {
            "ocn": ocn,
            "company": company_row["Company"],
            "by_npanxx": by_npanxx,
            "by_rate_center": by_rate_center,
            "by_state": by_state,
        },
    )


@router.get("/canadaocnall", name="ocn.canada_ocn_all")
def canada_ocn_all(request: Request, sort: str = Query("company")):
    if sort == "ocn":
        rows = fetch_all(
            "SELECT DISTINCT OCN, Company FROM caoc "
            "WHERE Company != '' AND OCN != '' ORDER BY OCN, Company"
        )
        headers = ["OCN", "Company"]
    else:
        rows = fetch_all(
            "SELECT DISTINCT Company, OCN, Province FROM caoc "
            "WHERE Company != '' AND OCN != '' AND Province != '' "
            "ORDER BY Company, Province, OCN"
        )
        headers = ["Company", "OCN", "Province"]
        sort = "company"

    return render(request, "ocn/all_canada.html", {"rows": rows, "headers": headers, "sort": sort})


@router.get("/canadaexall", name="ocn.canada_exchange_all")
def canada_exchange_all(request: Request, sort: str = Query("npa")):
    if sort == "company":
        rows = fetch_all(
            "SELECT ExchangeArea, Company, OCN, NPA, COCodeNXX, Status, Remarks FROM caoc "
            "WHERE Company != '' AND OCN != '' "
            "ORDER BY ExchangeArea, Company, OCN, NPA, COCodeNXX, Status"
        )
        headers = ["ExchangeArea", "Company", "OCN", "NPA", "COCodeNXX", "Status", "Remarks"]
    else:
        rows = fetch_all(
            "SELECT ExchangeArea, NPA, COCodeNXX, Company, OCN, Status, Remarks FROM caoc "
            "WHERE Company != '' AND OCN != '' "
            "ORDER BY ExchangeArea, NPA, COCodeNXX, Company, OCN, Status"
        )
        headers = ["ExchangeArea", "NPA", "COCodeNXX", "Company", "OCN", "Status", "Remarks"]
        sort = "npa"

    return render(request, "ocn/exchanges_canada.html", {"rows": rows, "headers": headers, "sort": sort})
