from fastapi import APIRouter, Query, Request

from app.database import fetch_all, fetch_one, row_to_dict
from app.templating import render

router = APIRouter()


_US_OCN_SORT_SQL = {
    "ocn": "OCN",
    "company": "Company COLLATE NOCASE",
    "state": "State",
}

_US_OCN_SORT_TIE = {
    "ocn": "Company COLLATE NOCASE ASC, State ASC",
    "company": "State ASC, OCN ASC",
    "state": "Company COLLATE NOCASE ASC, OCN ASC",
}


_CANADA_OCN_SORT_SQL = {
    "ocn": "OCN",
    "company": "Company COLLATE NOCASE",
    "province": "Province COLLATE NOCASE",
}

_CANADA_OCN_SORT_TIE = {
    "ocn": "Company COLLATE NOCASE ASC, Province COLLATE NOCASE ASC",
    "company": "Province COLLATE NOCASE ASC, OCN ASC",
    "province": "Company COLLATE NOCASE ASC, OCN ASC",
}


def _ocn_list_sort(
    sort: str,
    direction: str,
    columns: dict[str, str],
) -> tuple[str, str]:
    sort_key = (sort or "company").strip().lower()
    if sort_key not in columns:
        sort_key = "company"
    sort_dir = "desc" if (direction or "").strip().lower() == "desc" else "asc"
    return sort_key, sort_dir


def _rows_as_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


_CANADA_EX_WHERE = "Company != '' AND OCN != ''"

# First tuple item is sort query key, or None if the column is not sortable.
_CANADA_EX_COLUMNS: list[tuple[str | None, str, str]] = [
    ("npa", "NPA", "NPA"),
    (None, "NXX", "COCodeNXX"),
    ("cnac_status", "Status", "Status"),
    ("pooled", "Pooled", "Pooled"),
    ("exchange", "Exchange area", "ExchangeArea"),
    ("province", "Province", "Province"),
    ("company", "Company", "Company"),
    ("ocn", "OCN", "OCN"),
    ("date_assigned", "Date assigned", "DateAssigned"),
    ("remarks", "Remarks", "Remarks"),
]

_CANADA_EX_SORT_SQL = {
    key: f'"{col}" COLLATE NOCASE'
    for key, _, col in _CANADA_EX_COLUMNS
    if key is not None and key != "npa"
}
_CANADA_EX_SORT_KEYS = set(_CANADA_EX_SORT_SQL) | {"npa"}


def _canada_exchange_sort(sort: str, direction: str) -> tuple[str, str]:
    sort_key = (sort or "npa").strip().lower()
    if sort_key == "nxx":
        sort_key = "npa"
    if sort_key not in _CANADA_EX_SORT_KEYS:
        sort_key = "npa"
    sort_dir = "desc" if (direction or "").strip().lower() == "desc" else "asc"
    return sort_key, sort_dir


def _canada_exchange_order_clause(sort_key: str, sort_dir: str) -> str:
    direction = sort_dir.upper()
    if sort_key == "npa":
        return f"NPA {direction}, COCodeNXX {direction}"
    tie = ", NPA ASC, COCodeNXX ASC"
    return f"{_CANADA_EX_SORT_SQL[sort_key]} {direction}{tie}"


def _canada_exchange_status_filter(status: str, valid_statuses: set[str]) -> tuple[str, str, tuple]:
    status_key = (status or "all").strip()
    if status_key.lower() == "all":
        return "all", "", ()
    if status_key in valid_statuses:
        return status_key, " AND Status = ?", (status_key,)
    return "all", "", ()


@router.get("/ocnall", name="ocn.ocn_all")
def ocn_all(
    request: Request,
    sort: str | None = Query(None),
    dir: str | None = Query(None),
):
    if "sort" in request.query_params:
        sort_key, sort_dir = _ocn_list_sort(sort or "company", dir or "asc", _US_OCN_SORT_SQL)
    else:
        sort_key, sort_dir = "company", "asc"

    order_sql = _US_OCN_SORT_SQL[sort_key]
    tie_sql = _US_OCN_SORT_TIE[sort_key]
    rows = fetch_all(
        "SELECT DISTINCT OCN, Company, State FROM oc "
        "WHERE Company != '' AND OCN != '' "
        f"ORDER BY {order_sql} {sort_dir.upper()}, {tie_sql}"
    )

    return render(
        request,
        "ocn/all_us.html",
        {
            "rows": _rows_as_dicts(rows),
            "sort": sort_key,
            "sort_dir": sort_dir,
        },
    )


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
def canada_ocn_all(
    request: Request,
    sort: str | None = Query(None),
    dir: str | None = Query(None),
):
    if "sort" in request.query_params:
        sort_key, sort_dir = _ocn_list_sort(sort or "company", dir or "asc", _CANADA_OCN_SORT_SQL)
    else:
        sort_key, sort_dir = "company", "asc"

    order_sql = _CANADA_OCN_SORT_SQL[sort_key]
    tie_sql = _CANADA_OCN_SORT_TIE[sort_key]
    rows = fetch_all(
        "SELECT DISTINCT OCN, Company, Province FROM caoc "
        "WHERE Company != '' AND OCN != '' AND Province != '' "
        f"ORDER BY {order_sql} {sort_dir.upper()}, {tie_sql}"
    )

    return render(
        request,
        "ocn/all_canada.html",
        {
            "rows": _rows_as_dicts(rows),
            "sort": sort_key,
            "sort_dir": sort_dir,
        },
    )


@router.get("/canadaexall", name="ocn.canada_exchange_all")
def canada_exchange_all(
    request: Request,
    sort: str | None = Query(None),
    dir: str | None = Query(None),
    status: str = Query("all"),
):
    if "sort" in request.query_params:
        sort_key, sort_dir = _canada_exchange_sort(sort or "npa", dir or "asc")
    else:
        sort_key, sort_dir = "npa", "asc"

    status_rows = fetch_all(
        "SELECT DISTINCT Status FROM caoc "
        f"WHERE {_CANADA_EX_WHERE} AND Status IS NOT NULL AND TRIM(Status) != '' "
        "ORDER BY Status"
    )
    valid_statuses = {(row["Status"] or "").strip() for row in status_rows}
    status_key, status_sql, status_params = _canada_exchange_status_filter(status, valid_statuses)

    status_labels: dict[str, str] = {"all": "All"}
    for value in sorted(valid_statuses):
        status_labels[value] = value

    order_clause = _canada_exchange_order_clause(sort_key, sort_dir)
    rows = fetch_all(
        f"SELECT * FROM caoc WHERE {_CANADA_EX_WHERE}{status_sql} ORDER BY {order_clause}",
        status_params,
    )
    items = [row_to_dict(row) for row in rows]

    return render(
        request,
        "ocn/exchanges_canada.html",
        {
            "items": items,
            "columns": _CANADA_EX_COLUMNS,
            "sort": sort_key,
            "sort_dir": sort_dir,
            "status": status_key,
            "status_labels": status_labels,
        },
    )
