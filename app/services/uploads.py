import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from app.adapters.sqlite.validator import validate_sqlite_file
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MiB
CHUNK_SIZE = 1024 * 1024  # 1 MiB

SUPPORTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}


class UploadError(Exception):
    """Error controlado durante la subida de una base de datos."""


class UploadConflictError(UploadError):
    """Ya existe un archivo con el mismo nombre."""


class InvalidDatabaseError(UploadError):
    """El archivo recibido no es una base de datos SQLite válida."""


class UploadTooLargeError(UploadError):
    """El archivo supera el tamaño máximo permitido."""


async def save_database_upload(upload: UploadFile) -> Path:
    directory = settings.database_directory.expanduser().resolve()
    temp_path = None

    try:
        directory.mkdir(parents=True, exist_ok=True)

        filename = Path(upload.filename or "").name

        if (
            not filename
            or filename in {".", ".."}
            or Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS
        ):
            raise InvalidDatabaseError(
                "Unsupported filename or file extension."
            )

        destination = directory / filename

        # No sobrescribir archivos existentes.
        if destination.exists() or destination.is_symlink():
            raise UploadConflictError(
                "A file with this name already exists."
            )

        size = 0

        with NamedTemporaryFile(
            mode="wb",
            dir=directory,
            prefix=".upload_",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)

                if size > MAX_UPLOAD_SIZE:
                    raise UploadTooLargeError(
                        "Maximum upload size is 100 MiB."
                    )

                temp_file.write(chunk)

        if size == 0:
            raise InvalidDatabaseError("The uploaded file is empty.")

        if not validate_sqlite_file(temp_path):
            raise InvalidDatabaseError(
                "The uploaded file is not a valid SQLite database."
            )

        # Publicación atómica: no reemplaza un destino existente.
        try:
            import os
            os.link(temp_path, destination)
        except FileExistsError as exc:
            raise UploadConflictError(
                "A file with this name already exists."
            ) from exc

        logger.info(
            "Database uploaded successfully: name=%s size_bytes=%d",
            filename,
            size,
        )

        return destination

    except UploadError:
        raise

    except OSError:
        logger.exception("Filesystem error during database upload")
        raise UploadError("Unable to store the uploaded database.")

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        await upload.close()
