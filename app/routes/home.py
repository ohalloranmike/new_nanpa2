from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.constants import CANADA_PT, CANADA_PT_ABBR, COUNTRIES, STATES, US_TERRITORIES
from app.routes.refresh_stream import refresh_event_stream
from app.templating import render

router = APIRouter()


@router.get("/", name="home.index")
def index(request: Request):
    refresh_message = None
    if request.query_params.get("updated") == "1":
        refresh_message = "Data updated successfully from NANPA and CNAC."

    return render(
        request,
        "index.html",
        {
            "states": STATES,
            "us_territories": US_TERRITORIES,
            "canada_pt": CANADA_PT,
            "canada_pt_abbr": CANADA_PT_ABBR,
            "countries": COUNTRIES,
            "refresh_message": refresh_message,
        },
    )


@router.get("/refresh-data", name="home.refresh_data")
def refresh_data(request: Request):
    return render(request, "refresh_data.html", {})


@router.get("/refresh-data/stream", name="home.refresh_data_stream")
async def refresh_data_stream(request: Request):
    config = request.app.state.config
    return StreamingResponse(
        refresh_event_stream(request, config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
