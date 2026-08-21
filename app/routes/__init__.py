from app.routes.browse import router as browse_router
from app.routes.home import router as home_router
from app.routes.lists import router as lists_router
from app.routes.lookup import router as lookup_router
from app.routes.ocn import router as ocn_router


def register_routers(app):
    app.include_router(home_router)
    app.include_router(lookup_router)
    app.include_router(browse_router)
    app.include_router(ocn_router)
    app.include_router(lists_router)
