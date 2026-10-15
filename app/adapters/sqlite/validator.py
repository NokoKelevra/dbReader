import sqlite3
from pathlib import Path

SQLITE_HEADER = b"SQLite format 3\x00"

def has_sqlite_header(path: Path) -> bool:
    """Comprueba únicamente la cabecera de un archivo SQLite."""
    try:
        with path.open("rb") as file:
            return file.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except OSError:
        return False
    
def validate_sqlite_file(path: Path) -> bool:
    """
    Comprueba la cabecera y la integridad estructural
    de una base de datos SQLite en modo de solo lectura.
    """
    try:
        with path.open("rb") as file:
            header = file.read(len(SQLITE_HEADER))

        if header != SQLITE_HEADER:
            return False

        uri = path.resolve().as_uri() + "?mode=ro"

        with sqlite3.connect(uri, uri=True, timeout=5) as connection:
            result = connection.execute(
                "PRAGMA quick_check"
            ).fetchone()

            return result is not None and result[0] == "ok"

    except (OSError, sqlite3.Error, ValueError):
        return False
