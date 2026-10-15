import sqlite3
from app.core.config import settings
from app.services.discovery import discover_databases

def test_discovery_ignores_file_with_invalid_sqlite_header(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(settings, "database_directory", tmp_path)

    invalid_file = tmp_path / "invalid.db"
    invalid_file.write_bytes(b"This is not a SQLite database")

    databases = discover_databases()

    assert databases == []


def test_discovery_includes_file_with_valid_sqlite_header(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(settings, "database_directory", tmp_path)

    valid_file = tmp_path / "valid.db"

    with sqlite3.connect(valid_file) as connection:
        connection.execute(
            "CREATE TABLE example (id INTEGER PRIMARY KEY)"
        )

    databases = discover_databases()

    assert len(databases) == 1
    assert databases[0].name == "valid.db"
    assert databases[0].engine == "sqlite"
    assert databases[0].status == "available"
