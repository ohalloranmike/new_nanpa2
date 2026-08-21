import csv
from pathlib import Path

from fastapi import APIRouter, Request

from app.database import fetch_all
from app.templating import render

router = APIRouter()


@router.get("/aclist", name="lists.area_code_list")
def area_code_list(request: Request):
    rows = fetch_all(
        "SELECT NPA_ID, type_of_code, location, country, assigned, reserved, in_service "
        "FROM ac ORDER BY NPA_ID"
    )
    assigned, reserved, unassigned = [], [], []
    for row in rows:
        item = {
            "NPA_ID": row["NPA_ID"],
            "type_of_code": row["type_of_code"],
            "location": row["location"],
            "country": row["country"],
        }
        if row["assigned"] == "Yes":
            assigned.append(item)
        elif row["reserved"] == "Yes":
            reserved.append(item)
        else:
            unassigned.append(item)

    return render(
        request,
        "lists/aclist.html",
        {
            "assigned": assigned,
            "reserved": reserved,
            "unassigned": unassigned,
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

    return render(
        request,
        "lists/special_service_numbers.html",
        {
            "headers": headers,
            "rows": rows,
            "page_header": "Special Service Codes",
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
