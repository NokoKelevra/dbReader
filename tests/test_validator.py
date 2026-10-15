import sqlite3
from pathlib import Path
from app.adapters.sqlite.validator import validate_sqlite_file

def test_validate_sqlite_file():
    test_dir = Path("tests/tmp")
    test_dir.mkdir(parents=True, exist_ok=True)

    valid_db = test_dir / "valid.db"
    invalid_db = test_dir / "invalid.db"

    with sqlite3.connect(valid_db) as connection:
        connection.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY)"
        )

    invalid_db.write_text(
        "Esto no es una base de datos",
        encoding="utf-8",
    )

    assert validate_sqlite_file(valid_db) is True
    assert validate_sqlite_file(invalid_db) is False

    valid_db.unlink()
    invalid_db.unlink()
    test_dir.rmdir()
