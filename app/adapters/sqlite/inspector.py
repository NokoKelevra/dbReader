import logging
import sqlite3
from pathlib import Path
from app.models.schema import (
    ColumnSchema,
    DatabaseSchemaResponse,
    TableSchema,
    IndexSchema,
    ForeignKeySchema,
)


logger = logging.getLogger(__name__)

def quote_identifier(identifier: str) -> str:
    """Escapa un identificador SQL de SQLite."""
    return '"' + identifier.replace('"', '""') + '"'

def inspect_sqlite_database(
    path: Path,
    database_id: str,
) -> DatabaseSchemaResponse:
    if path.is_symlink() or not path.is_file():
        raise sqlite3.OperationalError(
            "Database path is not a regular file."
        )

    path = path.resolve()
    uri = path.as_uri() + "?mode=ro"


    logger.info("Inspecting SQLite schema: %s", path.name)

    try:
        with sqlite3.connect(uri, uri=True, timeout=5) as connection:
            connection.row_factory = sqlite3.Row

            objects = connection.execute("""
                SELECT name, type
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY type, name
            """).fetchall()

            tables = []
            views = []

            for obj in objects:
                name = obj["name"]

                if obj["type"] == "view":
                    views.append(name)
                    continue

                quoted_name = quote_identifier(name)

                column_rows = connection.execute(
                    f"PRAGMA table_info({quoted_name})"
                ).fetchall()

                columns = [
                    ColumnSchema(
                        name=column["name"],
                        declared_type=column["type"] or "",
                        nullable=not bool(column["notnull"])
                        and not bool(column["pk"]),
                        primary_key_position=column["pk"],
                        default_value=column["dflt_value"],
                    )
                    for column in column_rows
                ]

                row_count = connection.execute(
                    f"SELECT COUNT(*) FROM {quoted_name}"
                ).fetchone()[0]


                # Obtener índices de la tabla
                index_rows = connection.execute(
                    f"PRAGMA index_list({quoted_name})"
                ).fetchall()

                indexes = []

                for index in index_rows:
                    index_name = index["name"]

                    index_columns = connection.execute(
                        "PRAGMA index_info("
                        + quote_identifier(index_name)
                        + ")"
                    ).fetchall()

                    indexes.append(
                        IndexSchema(
                            name=index_name,
                            unique=bool(index["unique"]),
                            columns=[
                                column["name"]
                                for column in index_columns
                                if column["name"] is not None
                            ],
                        )
                    )

                # Obtener claves foráneas
                foreign_key_rows = connection.execute(
                    f"PRAGMA foreign_key_list({quoted_name})"
                ).fetchall()

                foreign_keys = [
                    ForeignKeySchema(
                        referenced_table=foreign_key["table"],
                        source_column=foreign_key["from"],
                        referenced_column=foreign_key["to"],
                        on_update=foreign_key["on_update"],
                        on_delete=foreign_key["on_delete"],
                    )
                    for foreign_key in foreign_key_rows
                ]

                tables.append(
                    TableSchema(
                        name=name,
                        row_count=row_count,
                        columns=columns,
                        indexes=indexes,
                        foreign_keys=foreign_keys,
                    )
                )

            return DatabaseSchemaResponse(
                database_id=database_id,
                engine="sqlite",
                tables=tables,
                views=views,
            )

    except sqlite3.Error:
        logger.exception(
            "Failed to inspect SQLite database: %s",
            path.name,
        )
        raise
