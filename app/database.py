import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_db: ContextVar[sqlite3.Connection | None] = ContextVar("db", default=None)


def set_db_context(conn: sqlite3.Connection):
    return _db.set(conn)


def reset_db_context(token):
    _db.reset(token)


def close_request_connection():
    conn = _db.get()
    if conn is not None:
        conn.close()


def get_connection() -> sqlite3.Connection:
    conn = _db.get()
    if conn is None:
        raise RuntimeError("Database connection is not available outside a request")
    return conn


@contextmanager
def db_connection(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


def fetch_one(query: str, params=()):
    cur = get_connection().execute(query, params)
    return cur.fetchone()


def fetch_all(query: str, params=()):
    cur = get_connection().execute(query, params)
    return cur.fetchall()


def table_columns(table_name: str) -> list[str]:
    rows = fetch_all(f"PRAGMA table_info({table_name})")
    return [row["name"] for row in rows]
