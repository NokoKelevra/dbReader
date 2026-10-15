def test_health_check(test_client):
    response = test_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "universal-db-reader",
        "version": "0.1.0",
    }


def test_list_databases_empty(test_client):
    response = test_client.get("/api/v1/databases")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
    }


def test_list_databases_with_sample(test_client, sample_database):
    response = test_client.get("/api/v1/databases")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    database = data["items"][0]
    assert database["name"] == sample_database.name
    assert database["engine"] == "sqlite"
    assert database["status"] == "available"
    assert database["size_bytes"] > 0


def test_get_database_schema(test_client, sample_database):
    # Obtener el identificador generado por la API.
    list_response = test_client.get("/api/v1/databases")
    assert list_response.status_code == 200

    databases = list_response.json()["items"]
    assert len(databases) == 1

    database_id = databases[0]["id"]

    # Consultar el esquema de la base de datos.
    response = test_client.get(
        f"/api/v1/databases/{database_id}/schema"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["engine"] == "sqlite"
    assert len(data["tables"]) == 1

    table = data["tables"][0]
    assert table["name"] == "users"
    assert table["row_count"] == 2

    column_names = [column["name"] for column in table["columns"]]
    assert column_names == ["id", "username", "email"]

    email_column = next(
        column for column in table["columns"]
        if column["name"] == "email"
    )
    assert email_column["nullable"] is True

    assert any(
        index["unique"] and index["columns"] == ["email"]
        for index in table["indexes"]
    )

def test_get_unknown_database_schema_returns_404(test_client):
    response = test_client.get(
        "/api/v1/databases/unknown-database/schema"
    )

    assert response.status_code == 404
    assert response.json()["detail"]

def test_get_database_statistics(test_client, sample_database):
    list_response = test_client.get("/api/v1/databases")
    assert list_response.status_code == 200

    database_id = list_response.json()["items"][0]["id"]

    response = test_client.get(
        f"/api/v1/databases/{database_id}/statistics"
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["summary"]

    assert data["engine"] == "sqlite"
    assert summary["table_count"] == 1
    assert summary["view_count"] == 0
    assert summary["total_rows"] == 2
    assert summary["total_columns"] == 3
    assert summary["total_foreign_keys"] == 0

    users_table = data["tables"][0]
    assert users_table["name"] == "users"
    assert users_table["row_count"] == 2
    assert users_table["column_count"] == 3

def test_upload_valid_database(test_client, sample_database):
    with sample_database.open("rb") as database_file:
        response = test_client.post(
            "/api/v1/databases/upload",
            files={
                "file": (
                    "uploaded.db",
                    database_file,
                    "application/octet-stream",
                )
            },
        )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "uploaded.db"
    assert data["status"] == "available"

    uploaded_path = sample_database.parent / "uploaded.db"
    assert uploaded_path.is_file()

def test_upload_invalid_database_returns_400(test_client):
    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "invalid.db",
                b"This is not a SQLite database",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "SQLite" in response.json()["detail"]
    assert not (test_client and False)

def test_upload_duplicate_filename_returns_409(test_client, sample_database):
    files = {
        "file": (
            "duplicate.db",
            sample_database.read_bytes(),
            "application/octet-stream",
        )
    }

    first_response = test_client.post(
        "/api/v1/databases/upload",
        files=files,
    )
    assert first_response.status_code == 201

    second_response = test_client.post(
        "/api/v1/databases/upload",
        files=files,
    )

    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["detail"]

def test_upload_unsupported_extension_returns_400(test_client):
    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "document.txt",
                b"Contenido de prueba",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower()

def test_upload_empty_file_returns_400(test_client):
    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "empty.db",
                b"",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_upload_invalid_database_cleans_temporary_file(test_client, tmp_path):
    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "invalid.db",
                b"Not a SQLite database",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert not list(tmp_path.glob(".upload_*"))

def test_upload_too_large_returns_413(test_client, monkeypatch):
    import app.services.uploads as uploads_service

    monkeypatch.setattr(uploads_service, "MAX_UPLOAD_SIZE", 10)

    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "large.db",
                b"0123456789ABCDEF",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 413
    assert "100 MiB" in response.json()["detail"]

def test_get_unknown_database_statistics_returns_404(test_client):
    response = test_client.get(
        "/api/v1/databases/unknown-database/statistics"
    )

    assert response.status_code == 404
    assert response.json()["detail"]

def test_get_database_schema_with_foreign_key(test_client, tmp_path):
    import sqlite3

    database_path = tmp_path / "relationships.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department_id INTEGER,
                FOREIGN KEY (department_id)
                    REFERENCES departments(id)
                    ON DELETE SET NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO departments (id, name) VALUES (1, 'IT')"
        )
        connection.execute(
            """
            INSERT INTO employees (id, name, department_id)
            VALUES (1, 'Alice', 1)
            """
        )

    response = test_client.get("/api/v1/databases")
    assert response.status_code == 200

    databases = response.json()["items"]
    database = next(
        item for item in databases
        if item["name"] == "relationships.db"
    )

    schema_response = test_client.get(
        f"/api/v1/databases/{database['id']}/schema"
    )

    assert schema_response.status_code == 200

    tables = {
        table["name"]: table
        for table in schema_response.json()["tables"]
    }

    assert tables["departments"]["row_count"] == 1
    assert tables["employees"]["row_count"] == 1

    foreign_keys = tables["employees"]["foreign_keys"]
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["referenced_table"] == "departments"
    assert foreign_keys[0]["source_column"] == "department_id"
    assert foreign_keys[0]["referenced_column"] == "id"
    assert foreign_keys[0]["on_delete"] == "SET NULL"

def test_get_database_schema_with_view(test_client, tmp_path):
    import sqlite3

    database_path = tmp_path / "views.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                active INTEGER NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO users (username, active) VALUES (?, ?)",
            [
                ("alice", 1),
                ("bob", 0),
            ],
        )
        connection.execute(
            """
            CREATE VIEW active_users AS
            SELECT id, username
            FROM users
            WHERE active = 1
            """
        )

    response = test_client.get("/api/v1/databases")
    assert response.status_code == 200

    database = next(
        item for item in response.json()["items"]
        if item["name"] == "views.db"
    )

    schema_response = test_client.get(
        f"/api/v1/databases/{database['id']}/schema"
    )

    assert schema_response.status_code == 200

    data = schema_response.json()
    assert len(data["tables"]) == 1
    assert data["tables"][0]["name"] == "users"
    assert data["tables"][0]["row_count"] == 2
    assert data["views"] == ["active_users"]

def test_get_database_schema_with_empty_table(test_client, tmp_path):
    import sqlite3

    database_path = tmp_path / "empty_table.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY,
                message TEXT NOT NULL
            )
            """
        )

    response = test_client.get("/api/v1/databases")
    assert response.status_code == 200

    database = next(
        item for item in response.json()["items"]
        if item["name"] == "empty_table.db"
    )

    schema_response = test_client.get(
        f"/api/v1/databases/{database['id']}/schema"
    )

    assert schema_response.status_code == 200

    data = schema_response.json()
    assert len(data["tables"]) == 1
    assert data["tables"][0]["name"] == "logs"
    assert data["tables"][0]["row_count"] == 0
    assert len(data["tables"][0]["columns"]) == 2

def test_upload_path_traversal_stays_inside_storage(
    test_client, sample_database, tmp_path
):
    response = test_client.post(
        "/api/v1/databases/upload",
        files={
            "file": (
                "../../outside.db",
                sample_database.read_bytes(),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "outside.db"

    # El archivo debe permanecer dentro del directorio configurado.
    assert (tmp_path / "outside.db").is_file()

    # No debe haberse creado en el directorio padre.
    assert not (tmp_path.parent / "outside.db").exists()

def test_schema_endpoint_rejects_path_like_identifier(test_client):
    identifiers = [
        "../outside",
        "../../etc/passwd",
        "/etc/passwd",
    ]

    for database_id in identifiers:
        response = test_client.get(
            f"/api/v1/databases/{database_id}/schema"
        )

        assert response.status_code in (404, 422), (
            f"Unexpected status for {database_id!r}: "
            f"{response.status_code}"
        )

def test_statistics_endpoint_rejects_path_like_identifier(test_client):
    identifiers = [
        "../outside",
        "../../etc/passwd",
        "/etc/passwd",
    ]

    for database_id in identifiers:
        response = test_client.get(
            f"/api/v1/databases/{database_id}/statistics"
        )

        assert response.status_code in (404, 422), (
            f"Unexpected status for {database_id!r}: "
            f"{response.status_code}"
        )

def test_schema_service_cannot_access_database_outside_storage(
    test_client, tmp_path, monkeypatch
):
    import sqlite3

    from app.services.schema import (
        DatabaseNotFoundError,
        get_database_schema,
    )

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    outside_database = tmp_path / "outside.db"
    with sqlite3.connect(outside_database) as connection:
        connection.execute("CREATE TABLE secret (value TEXT)")
        connection.execute("INSERT INTO secret VALUES ('private')")

    monkeypatch.setattr(
        "app.core.config.settings.database_directory",
        storage_dir,
    )

    try:
        get_database_schema(outside_database.name)
    except DatabaseNotFoundError:
        pass
    else:
        raise AssertionError(
            "The service must not access databases outside storage."
        )

def test_statistics_service_cannot_access_database_outside_storage(
    test_client, tmp_path, monkeypatch
):
    import sqlite3

    from app.services.statistics import (
        DatabaseNotFoundError,
        get_database_statistics,
    )

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    outside_database = tmp_path / "outside.db"
    with sqlite3.connect(outside_database) as connection:
        connection.execute("CREATE TABLE secret (value TEXT)")
        connection.execute("INSERT INTO secret VALUES ('private')")

    monkeypatch.setattr(
        "app.core.config.settings.database_directory",
        storage_dir,
    )

    try:
        get_database_statistics(outside_database.name)
    except DatabaseNotFoundError:
        pass
    else:
        raise AssertionError(
            "The statistics service must not access databases outside storage."
        )
