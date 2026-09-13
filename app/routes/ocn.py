from fastapi import APIRouter, Query, Request

from app.database import fetch_all, fetch_one
from app.templating import render

router = APIRouter()


def _caoc_npanxx_sort_key(row) -> tuple[str, str]:
    return (row["NPA"] or "", row["COCodeNXX"] or "")


def _caoc_company_sort_key(row) -> tuple[str, str, str, str]:
    return (
        (row["Company"] or "").casefold(),
        row["OCN"] or "",
        row["NPA"] or "",
        row["COCodeNXX"] or "",
    )


def _group_caoc_by_status(rows, sort: str) -> list[dict]:
    order: list[str] = []
    grouped: dict[str, list] = {}
    for row in rows:
        status = (row["Status"] or "").strip() or "Unknown"
        if status not in grouped:
            grouped[status] = []
            order.append(status)
        grouped[status].append(row)
    row_sort_key = _caoc_company_sort_key if sort == "company" else _caoc_npanxx_sort_key
    sections = []
    for status in order:
        rows_for_status = grouped[status]
        rows_for_status.sort(key=row_sort_key)
        sections.append({"status": status, "rows": rows_for_status})
    return sections


@router.get("/ocnall", name="ocn.ocn_all")
def ocn_all(request: Request, sort: str = Query("company")):
    if sort == "ocn":
        rows = fetch_all(
            "SELECT DISTINCT Company, OCN, State FROM oc "
            "WHERE Company != '' AND OCN != '' ORDER BY OCN, Company, State"
        )
        sort = "ocn"
    else:
        rows = fetch_all(
            "SELECT DISTINCT Company, OCN, State FROM oc "
            "WHERE Company != '' AND OCN != '' ORDER BY Company, State, OCN"
        )
        sort = "company"

    return render(request, "ocn/all_us.html", {"rows": rows, "sort": sort})


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
            "SELECT DISTINCT OCN, Company, Province FROM caoc "
            "WHERE Company != '' AND OCN != '' AND Province != '' "
            "ORDER BY OCN, Company, Province"
        )
        headers = ["OCN", "Company", "Province"]
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
            "ORDER BY Status"
        )
        sort = "company"
    else:
        rows = fetch_all(
            "SELECT ExchangeArea, NPA, COCodeNXX, Company, OCN, Status, Remarks FROM caoc "
            "WHERE Company != '' AND OCN != '' "
            "ORDER BY Status"
        )
        sort = "npa"

    return render(
        request,
        "ocn/exchanges_canada.html",
        {
            "status_sections": _group_caoc_by_status(rows, sort),
            "sort": sort,
        },
    )
