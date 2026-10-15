import logging
from fastapi import APIRouter, HTTPException
from app.models.database import DatabaseListResponse
from app.services.discovery import discover_databases
from fastapi import File, UploadFile, status
from app.services.uploads import (InvalidDatabaseError,UploadConflictError,UploadError,UploadTooLargeError,save_database_upload,)
from app.models.schema import DatabaseSchemaResponse
from app.services.schema import (DatabaseNotFoundError,SchemaInspectionError,get_database_schema,)
from app.models.statistics import DatabaseStatisticsResponse
from app.services.statistics import get_database_statistics
from app.services.table_data import (TableDataNotFoundError,TableDataInspectionError,get_table_data,MAX_PAGE_SIZE,DEFAULT_PAGE_SIZE,)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/databases",
    tags=["Databases"],
)

@router.get("", response_model=DatabaseListResponse)
def list_databases() -> DatabaseListResponse:
    try:
        databases = discover_databases()

        return DatabaseListResponse(
            items=databases,
            total=len(databases),
        )

    except Exception as exc:
        logger.exception("Unexpected error listing databases")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while listing databases.",
        ) from exc


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_database(file: UploadFile = File(...)):
    try:
        path = await save_database_upload(file)

        return {
            "name": path.name,
            "status": "available",
            "message": "Database uploaded successfully.",
        }

    except UploadConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=str(exc),
        ) from exc

    except InvalidDatabaseError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except UploadError as exc:
        logger.exception("Database upload failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to store the uploaded database.",
        ) from exc

@router.get(
    "/{database_id}/schema",
    response_model=DatabaseSchemaResponse,
)
def get_database_schema_endpoint(
    database_id: str,
) -> DatabaseSchemaResponse:
    try:
        return get_database_schema(database_id)

    except DatabaseNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except SchemaInspectionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/{database_id}/statistics",response_model=DatabaseStatisticsResponse,)
def get_database_statistics_endpoint(
    database_id: str,
) -> DatabaseStatisticsResponse:
    try:
        return get_database_statistics(database_id)

    except DatabaseNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except SchemaInspectionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@router.get("/{database_id}/tables/{table_name}/rows")
def get_table_data_endpoint(
    database_id: str,
    table_name: str,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
):
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Limit must be between 1 and {MAX_PAGE_SIZE}.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="Offset cannot be negative.",
        )

    try:
        return get_table_data(
            database_id=database_id,
            table_name=table_name,
            limit=limit,
            offset=offset,
        )

    except TableDataNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except TableDataInspectionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
