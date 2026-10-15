from app.models.statistics import (
    DatabaseStatisticsResponse,
    StatisticsSummary,
    TableStatistics,
)


def test_database_statistics_response():
    response = DatabaseStatisticsResponse(
        database_id="db_test",
        engine="sqlite",
        summary=StatisticsSummary(
            table_count=1,
            view_count=0,
            total_rows=10,
            total_columns=2,
            total_indexes=1,
            total_foreign_keys=0,
            size_bytes=4096,
        ),
        tables=[
            TableStatistics(
                name="users",
                row_count=10,
                column_count=2,
                index_count=1,
                foreign_key_count=0,
            )
        ],
    )

    assert response.summary.total_rows == 10
    assert response.tables[0].name == "users"
    assert response.summary.table_count == len(response.tables)
