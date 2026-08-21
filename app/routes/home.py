from fastapi import APIRouter, Request

from app.constants import CANADA_PT, CANADA_PT_ABBR, COUNTRIES, STATES, US_TERRITORIES
from app.templating import render

router = APIRouter()


@router.get("/", name="home.index")
def index(request: Request):
    return render(
        request,
        "index.html",
        {
            "states": STATES,
            "us_territories": US_TERRITORIES,
            "canada_pt": CANADA_PT,
            "canada_pt_abbr": CANADA_PT_ABBR,
            "countries": COUNTRIES,
        },
    )
