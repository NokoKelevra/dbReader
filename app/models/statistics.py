from pydantic import BaseModel, ConfigDict

class TableStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    row_count: int
    column_count: int
    index_count: int
    foreign_key_count: int

class StatisticsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_count: int
    view_count: int
    total_rows: int
    total_columns: int
    total_indexes: int
    total_foreign_keys: int
    size_bytes: int

class DatabaseStatisticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_id: str
    engine: str
    summary: StatisticsSummary
    tables: list[TableStatistics]
