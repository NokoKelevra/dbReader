from typing import Literal
from pydantic import BaseModel, ConfigDict

class DatabaseSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    engine: Literal["sqlite"]
    size_bytes: int
    status: Literal["available", "unavailable", "error"]

class DatabaseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DatabaseSummary]
    total: int
