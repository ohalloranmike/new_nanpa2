from contextlib import asynccontextmanager

import sqlite3
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from app.config import Config
from app.database import close_request_connection, reset_db_context, set_db_context
from app.ingest import database_is_fresh, database_timestamp, refresh_database, source_files_are_fresh
from app.templating import init_templates


def create_app(config_class=Config) -> FastAPI:
    config = config_class()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db_last_updated = database_timestamp(config)
        if config.REFRESH_ON_START or not source_files_are_fresh(config) or not database_is_fresh(config):
            refresh_database(config, force=config.REFRESH_ON_START)
            db_last_updated = database_timestamp(config)
        app.state.config = config
        app.state.db_last_updated = db_last_updated
        yield

    app = FastAPI(title="NANPA Numbering Plan Explorer", lifespan=lifespan)
    init_templates(config.TEMPLATE_DIR)

    class NoCacheStaticMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            path = request.url.path
            if path.startswith(("/css/", "/js/")) or path.endswith((".css", ".js")):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

    app.add_middleware(NoCacheStaticMiddleware)

    @app.middleware("http")
    async def db_middleware(request: Request, call_next):
        if request.url.path.startswith("/refresh-data"):
            return await call_next(request)

        conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        db_token = set_db_context(conn)
        try:
            return await call_next(request)
        finally:
            close_request_connection()
            reset_db_context(db_token)

    from app.routes import register_routers

    register_routers(app)
    app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=False), name="static")

    return app

