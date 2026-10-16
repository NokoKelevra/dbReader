import pytest
from app.services.table_data import (
    TableDataNotFoundError,
    get_table_data,
)


def get_database_id(test_client, database_name):
    response = test_client.get("/api/v1/databases")
    assert response.status_code == 200

    return next(
        database["id"]
        for database in response.json()["items"]
        if database["name"] == database_name
    )


def test_get_table_data(test_client, sample_database):
    database_id = get_database_id(test_client, sample_database.name)

    result = get_table_data(
        database_id=database_id,
        table_name="users",
    )

    assert result["table_name"] == "users"
    assert result["columns"] == ["id", "username", "email"]
    assert result["total_rows"] == 2
    assert len(result["rows"]) == 2
    assert result["limit"] == 50
    assert result["offset"] == 0


def test_get_table_data_pagination(test_client, sample_database):
    database_id = get_database_id(test_client, sample_database.name)

    result = get_table_data(
        database_id=database_id,
        table_name="users",
        limit=1,
        offset=1,
    )

    assert len(result["rows"]) == 1
    assert result["total_rows"] == 2
    assert result["offset"] == 1


def test_get_table_data_unknown_database():
    with pytest.raises(TableDataNotFoundError):
        get_table_data(
            database_id="unknown-database",
            table_name="users",
        )


def test_get_table_data_unknown_table(test_client, sample_database):
    database_id = get_database_id(test_client, sample_database.name)

    with pytest.raises(TableDataNotFoundError):
        get_table_data(
            database_id=database_id,
            table_name="table_that_does_not_exist",
        )


@pytest.mark.parametrize(
    ("limit", "offset"),
    [
        (0, 0),
        (101, 0),
        (1, -1),
    ],
)
def test_get_table_data_rejects_invalid_pagination(
    test_client,
    sample_database,
    limit,
    offset,
):
    database_id = get_database_id(test_client, sample_database.name)

    with pytest.raises(ValueError):
        get_table_data(
            database_id=database_id,
            table_name="users",
            limit=limit,
            offset=offset,
        )
        
def test_get_table_data_handles_invalid_utf8_text(
    test_client,
    sample_database,
):
    import sqlite3

    database_id = get_database_id(test_client, sample_database.name)

    with sqlite3.connect(sample_database) as connection:
        connection.execute(
            "CREATE TABLE legacy_text (id INTEGER PRIMARY KEY, name TEXT)"
        )
        connection.execute(
            "INSERT INTO legacy_text (name) VALUES (CAST(? AS TEXT))",
            (sqlite3.Binary(b"01 Electr\xf3nica del motor"),),
        )

    result = get_table_data(
        database_id=database_id,
        table_name="legacy_text",
    )

    assert result["rows"][0]["name"] == "01 Electrónica del motor"