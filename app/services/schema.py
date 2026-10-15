
import logging
import sqlite3
from pathlib import Path
from app.adapters.sqlite.inspector import inspect_sqlite_database
from app.core.config import settings
from app.models.schema import DatabaseSchemaResponse
from app.services.discovery import discover_databases

logger = logging.getLogger(__name__)

class DatabaseNotFoundError(Exception):
    """La base de datos no existe en el inventario."""


class SchemaInspectionError(Exception):
    """No se pudo inspeccionar el esquema de la base de datos."""


def get_database_schema(database_id: str) -> DatabaseSchemaResponse:
    databases = discover_databases()

    database = next(
        (item for item in databases if item.id == database_id),
        None,
    )

    if database is None:
        logger.warning(
            "Schema requested for unknown database: id=%s",
            database_id,
        )
        raise DatabaseNotFoundError("Database not found.")

    directory = settings.database_directory.expanduser().resolve()
    path = (directory / database.name).resolve()

    # Defensa adicional: el archivo debe permanecer dentro del directorio autorizado.
    if path.parent != directory or not path.is_file():
        logger.warning(
            "Database file is no longer available: id=%s",
            database_id,
        )
        raise DatabaseNotFoundError("Database not found.")

    try:
        return inspect_sqlite_database(
            path=path,
            database_id=database.id,
        )

    except sqlite3.Error as exc:
        logger.exception(
            "Schema inspection failed: id=%s",
            database_id,
        )
        raise SchemaInspectionError(
            "Unable to inspect the database schema."
        ) from exc
