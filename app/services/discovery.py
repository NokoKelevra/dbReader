import logging
from uuid import uuid5, NAMESPACE_URL
from app.core.config import settings
from app.models.database import DatabaseSummary
from app.adapters.sqlite.validator import has_sqlite_header

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}

def discover_databases() -> list[DatabaseSummary]:
    directory = settings.database_directory.expanduser().resolve()

    logger.info("Starting database discovery in %s", directory)

    if not directory.is_dir():
        logger.warning(
            "Database directory does not exist or is inaccessible: %s",
            directory,
        )
        return []

    databases = []

    try:
        paths = sorted(
            directory.iterdir(),
            key=lambda path: path.name.lower(),
        )
    except OSError:
        logger.exception(
            "Unable to list database directory: %s",
            directory,
        )
        return []

    for path in paths:
        try:
            if path.is_symlink() or not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            stat = path.stat()
            
            if not has_sqlite_header(path):
                logger.warning(
                    "Ignoring file with invalid SQLite header: %s",
                    path.name,
                )
                continue

            database = DatabaseSummary(
                id=str(
                    uuid5(
                        NAMESPACE_URL,
                        str(path.resolve()),
                    )
                ),
                name=path.name,
                engine="sqlite",
                size_bytes=stat.st_size,
                status="available",
            )

            databases.append(database)

            logger.info(
                "Database discovered: name=%s size_bytes=%d",
                path.name,
                stat.st_size,
            )

        except OSError:
            logger.exception(
                "Unable to inspect filesystem entry: %s",
                path.name,
            )

        except Exception:
            logger.exception(
                "Unexpected error processing filesystem entry: %s",
                path.name,
            )

    logger.info(
        "Database discovery completed: found=%d",
        len(databases),
    )

    return databases

def get_discovered_database(database_id: str) -> DatabaseSummary | None:
    """Devuelve una base de datos del inventario por su identificador."""
    return next(
        (
            database
            for database in discover_databases()
            if database.id == database_id
        ),
        None,
    )