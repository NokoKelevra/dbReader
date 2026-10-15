from pydantic import BaseModel, ConfigDict

class ColumnSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    declared_type: str
    nullable: bool
    primary_key_position: int
    default_value: str | None

class ForeignKeySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    referenced_table: str
    source_column: str
    referenced_column: str | None
    on_update: str
    on_delete: str

class IndexSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    unique: bool
    columns: list[str]

class TableSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    row_count: int
    columns: list[ColumnSchema]
    indexes: list[IndexSchema]
    foreign_keys: list[ForeignKeySchema]

class DatabaseSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_id: str
    engine: str
    tables: list[TableSchema]
    views: list[str]
