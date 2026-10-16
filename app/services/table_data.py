import logging
import sqlite3
from pathlib import Path
from typing import Any

from app.adapters.sqlite.inspector import quote_identifier
from app.core.config import settings
from app.services.discovery import discover_databases

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

def decode_sqlite_text(value: bytes) -> str:
    """Decode UTF-8 text, falling back to Windows-1252 for legacy data."""
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return value.decode("cp1252", errors="replace")

class TableDataNotFoundError(Exception):
    """La base de datos o la tabla solicitada no existe."""


class TableDataInspectionError(Exception):
    """No se ha podido consultar el contenido de la tabla."""


def get_table_data(
    database_id: str,
    table_name: str,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict[str, Any]:
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise ValueError(f"Limit must be between 1 and {MAX_PAGE_SIZE}.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    databases = discover_databases()
    database = next(
        (item for item in databases if item.id == database_id),
        None,
    )

    if database is None:
        raise TableDataNotFoundError("Database not found.")

    directory = settings.database_directory.expanduser().resolve()
    path = directory / database.name

    if path.is_symlink() or not path.is_file():
        raise TableDataNotFoundError("Database not found.")

    path = path.resolve()

    if path.parent != directory:
        raise TableDataNotFoundError("Database not found.")

    uri = path.as_uri() + "?mode=ro"
    quoted_table = quote_identifier(table_name)

    try:
        with sqlite3.connect(uri, uri=True, timeout=5) as connection:
            connection.text_factory = decode_sqlite_text
            connection.row_factory = sqlite3.Row

            table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                  AND name NOT LIKE 'sqlite_%'
                """,
                (table_name,),
            ).fetchone()

            if table is None:
                raise TableDataNotFoundError("Table not found.")

            columns = connection.execute(
                f"PRAGMA table_info({quoted_table})"
            ).fetchall()

            if not columns:
                raise TableDataNotFoundError("Table not found.")

            total = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_table}"
            ).fetchone()[0]

            rows = connection.execute(
                f"SELECT * FROM {quoted_table} LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

            return {
                "database_id": database_id,
                "table_name": table_name,
                "columns": [column["name"] for column in columns],
                "rows": [dict(row) for row in rows],
                "total_rows": total,
                "limit": limit,
                "offset": offset,
            }

    except TableDataNotFoundError:
        raise

    except sqlite3.Error as exc:
        logger.exception(
            "Failed to read table data: database_id=%s table=%s",
            database_id,
            table_name,
        )
        raise TableDataInspectionError(
            "Unable to read table data."
        ) from exc
