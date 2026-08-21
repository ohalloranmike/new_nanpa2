from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import sqlite3
from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from app.config import Config
from app.database import close_request_connection, reset_db_context, set_db_context
from app.ingest import database_is_fresh, refresh_database, source_files_are_fresh
from app.templating import init_templates


def create_app(config_class=Config) -> FastAPI:
    config = config_class()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db_last_updated = _db_timestamp(config.DB_PATH)
        if config.REFRESH_ON_START or not source_files_are_fresh(config) or not database_is_fresh(config):
            refresh_database(config, force=config.REFRESH_ON_START)
            db_last_updated = _db_timestamp(config.DB_PATH)
        app.state.config = config
        app.state.db_last_updated = db_last_updated
        yield

    app = FastAPI(title="NANPA Numbering Plan Explorer", lifespan=lifespan)
    init_templates(config.TEMPLATE_DIR)

    @app.middleware("http")
    async def db_middleware(request: Request, call_next):
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


def _db_timestamp(db_path: Path) -> str:
    if not db_path.exists():
        return "Not built yet"
    return datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
