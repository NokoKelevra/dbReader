import logging
from app.core.config import settings
from app.models.statistics import (
    DatabaseStatisticsResponse,
    StatisticsSummary,
    TableStatistics,
)
from app.services.discovery import discover_databases
from app.services.schema import (
    DatabaseNotFoundError,
    SchemaInspectionError,
    get_database_schema,
)

logger = logging.getLogger(__name__)


def get_database_statistics(
    database_id: str,
) -> DatabaseStatisticsResponse:
    databases = discover_databases()

    database = next(
        (item for item in databases if item.id == database_id),
        None,
    )

    if database is None:
        raise DatabaseNotFoundError("Database not found.")

    schema = get_database_schema(database_id)

    tables = [
        TableStatistics(
            name=table.name,
            row_count=table.row_count,
            column_count=len(table.columns),
            index_count=len(table.indexes),
            foreign_key_count=len(table.foreign_keys),
        )
        for table in schema.tables
    ]

    summary = StatisticsSummary(
        table_count=len(schema.tables),
        view_count=len(schema.views),
        total_rows=sum(table.row_count for table in schema.tables),
        total_columns=sum(len(table.columns) for table in schema.tables),
        total_indexes=sum(len(table.indexes) for table in schema.tables),
        total_foreign_keys=sum(
            len(table.foreign_keys) for table in schema.tables
        ),
        size_bytes=database.size_bytes,
    )

    logger.info(
        "Statistics calculated: database_id=%s tables=%d rows=%d",
        database_id,
        summary.table_count,
        summary.total_rows,
    )

    return DatabaseStatisticsResponse(
        database_id=database_id,
        engine="sqlite",
        summary=summary,
        tables=tables,
    )
