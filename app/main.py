
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.databases import router as databases_router
from app.core.logging_config import configure_logging

app = FastAPI(
    title="Universal DB Reader",
    description="API para inspeccionar bases de datos y generar estadísticas.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

app.include_router(
    databases_router,
    prefix="/api/v1",
)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "universal-db-reader",
        "version": app.version,
    }
