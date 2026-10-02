import csv
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Query, Request

from app.database import fetch_all, row_to_dict
from app.templating import render

router = APIRouter()

_SPECIAL_SERVICE_US_CA = "United States and Canada"
_SPECIAL_SERVICE_PAGE_TITLE = "Special Service Numbers (Intl.)"


def _sort_special_service_rows(rows: list[list[str]]) -> list[list[str]]:
    """United States and Canada first, then other countries A–Z; preserve row order within each country."""
    groups: dict[str, list[list[str]]] = defaultdict(list)
    for row in rows:
        groups[row[0]].append(row)
    ordered_countries = []
    if _SPECIAL_SERVICE_US_CA in groups:
        ordered_countries.append(_SPECIAL_SERVICE_US_CA)
    ordered_countries.extend(
        sorted((name for name in groups if name != _SPECIAL_SERVICE_US_CA), key=str.casefold)
    )
    return [row for country in ordered_countries for row in groups[country]]


_ACLIST_STATUS_WHERE = {
    "assigned": "WHERE assigned = 'Yes'",
    "reserved": "WHERE assigned != 'Yes' AND reserved = 'Yes'",
    "unassigned": "WHERE assigned != 'Yes' AND (reserved IS NULL OR reserved != 'Yes')",
}

_ACLIST_STATUS_LABELS = {
    "all": "All",
    "assigned": "Assigned",
    "reserved": "Reserved",
    "unassigned": "Unassigned and not reserved",
}

# (sort query key, column header label, SQLite column name)
_ACLIST_COLUMNS: list[tuple[str, str, str]] = [
    ("npa", "NPA", "NPA_ID"),
    ("type_of_code", "Type of code", "type_of_code"),
    ("assignable", "Assignable", "ASSIGNABLE"),
    ("explanation", "Explanation", "EXPLANATION"),
    ("reserved", "Reserved", "RESERVED"),
    ("assigned", "Assigned", "ASSIGNED"),
    ("assignment_dt", "Assignment date", "ASSIGNMENT_DT"),
    ("use", "Use", "USE"),
    ("location", "Location", "LOCATION"),
    ("country", "Country", "COUNTRY"),
    ("in_service", "In service", "IN_SERVICE"),
    ("in_service_dt", "In service date", "IN_SERVICE_DT"),
    ("status", "Status", "STATUS"),
    ("planning_letters", "Planning letters", "PLANNING_LETTERS"),
    ("notes", "Notes", "NOTES"),
    ("overlay", "Overlay", "OVERLAY"),
    ("overlay_complex", "Overlay complex", "OVERLAY_COMPLEX"),
    ("parent_npa", "Parent NPA", "PARENT_NPA_ID"),
    ("service", "Service", "SERVICE"),
    ("time_zone", "Time zone", "TIME_ZONE"),
    ("area_served", "Area served", "AREA_SERVED"),
    ("map", "Map", "MAP"),
    ("in_jeopardy", "In jeopardy", "IN_JEOPARDY"),
    ("relief_planning", "Relief planning", "RELIEF_PLANNING_IN_PROGRESS"),
    ("home_npa_local", "Home NPA local", "HOME_NPA_LOCAL_CALLS"),
    ("home_npa_toll", "Home NPA toll", "HOME_NPA_TOLL_CALLS"),
    ("foreign_npa_local", "Foreign NPA local", "FOREIGN_NPA_LOCAL_CALLS"),
    ("foreign_npa_toll", "Foreign NPA toll", "FOREIGN_NPA_TOLL_CALLS"),
    ("perm_hnpa_local", "Perm HNPA local", "PERM_HNPA_LOCAL_CALLS"),
    ("perm_hnpa_toll", "Perm HNPA toll", "PERM_HNPA_TOLL_CALLS"),
    ("perm_fnpa_local", "Perm FNPA local", "PERM_HNPA_FOREIGN_LOCAL_CALLS"),
    ("dialing_plan_notes", "Dialing plan notes", "DIALING_PLAN_NOTES"),
]

_ACLIST_SORT_SQL = {key: f'"{col}" COLLATE NOCASE' if col != "NPA_ID" else col for key, _, col in _ACLIST_COLUMNS}
# type_of_code is lowercase in schema
_ACLIST_SORT_SQL["type_of_code"] = "type_of_code COLLATE NOCASE"
_ACLIST_SORT_KEYS = set(_ACLIST_SORT_SQL)


def _aclist_sort(sort: str, direction: str) -> tuple[str, str]:
    sort_key = (sort or "npa").strip().lower()
    if sort_key not in _ACLIST_SORT_KEYS:
        sort_key = "npa"
    sort_dir = "desc" if (direction or "").strip().lower() == "desc" else "asc"
    return sort_key, sort_dir


@router.get("/aclist", name="lists.area_code_list")
def area_code_list(
    request: Request,
    status: str = Query("all"),
    sort: str | None = Query(None),
    dir: str | None = Query(None),
):
    status_key = (status or "all").strip().lower()
    if status_key not in _ACLIST_STATUS_WHERE and status_key != "all":
        status_key = "all"

    if "sort" in request.query_params:
        sort_key, sort_dir = _aclist_sort(sort or "npa", dir or "asc")
    else:
        sort_key, sort_dir = "npa", "asc"

    where = _ACLIST_STATUS_WHERE.get(status_key, "")
    order_sql = _ACLIST_SORT_SQL[sort_key]
    tie = "" if sort_key == "npa" else ", NPA_ID ASC"
    rows = fetch_all(
        f"SELECT * FROM ac {where} ORDER BY {order_sql} {sort_dir.upper()}{tie}"
    )
    items = [row_to_dict(row) for row in rows]

    return render(
        request,
        "lists/aclist.html",
        {
            "items": items,
            "columns": _ACLIST_COLUMNS,
            "status": status_key,
            "status_labels": _ACLIST_STATUS_LABELS,
            "sort": sort_key,
            "sort_dir": sort_dir,
        },
    )


@router.get("/specialservicenumbers", name="lists.special_service_numbers")
def special_service_numbers(request: Request):
    csv_path = Path(request.app.state.config.NANPA_DIR) / "special_service_numbers.csv"
    headers = []
    rows = []
    try:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
            for row in reader:
                if len(row) >= 3:
                    rows.append(row[:3])
    except OSError:
        return render(request, "error.html", {"error": "Unable to load special service numbers list."}, 500)

    rows = _sort_special_service_rows(rows)

    return render(
        request,
        "lists/special_service_numbers.html",
        {
            "headers": headers,
            "rows": rows,
            "page_header": _SPECIAL_SERVICE_PAGE_TITLE,
        },
    )


@router.get("/n11", name="lists.n11_codes")
def n11_codes(request: Request):
    csv_path = Path(request.app.state.config.NANPA_DIR) / "N11-Codes.csv"
    rows = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        rows = [row for row in reader if row]
    return render(request, "lists/n11.html", {"rows": rows})


@router.get("/900codes", name="lists.codes_900")
def codes_900(request: Request):
    csv_path = Path(request.app.state.config.NANPA_DIR) / "900codes.csv"
    rows = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        rows = [row for row in reader if row]
    return render(request, "lists/900.html", {"rows": rows})
