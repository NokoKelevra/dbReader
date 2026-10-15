import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """Cliente HTTP con un directorio de bases de datos aislado."""
    monkeypatch.setattr(settings, "database_directory", tmp_path)

    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_database(tmp_path, monkeypatch):
    """Crea una base SQLite de prueba con una tabla y algunos registros."""
    monkeypatch.setattr(settings, "database_directory", tmp_path)

    database_path = tmp_path / "test.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE
            )
            """
        )
        connection.executemany(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            [
                ("alice", "alice@example.com"),
                ("bob", "bob@example.com"),
            ],
        )

    return database_path
