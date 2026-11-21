"""Traduce los errores de los casos de uso a respuestas HTTP con la forma {"detail": "…"}."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.errors import (
    ConfigError,
    EntryAlreadyExists,
    EntryNotFound,
    IndexConflict,
    InvalidKey,
    StoreUnavailable,
)

_STATUS_BY_ERROR: dict[type[ConfigError], int] = {
    InvalidKey: status.HTTP_422_UNPROCESSABLE_CONTENT,
    EntryNotFound: status.HTTP_404_NOT_FOUND,
    EntryAlreadyExists: status.HTTP_409_CONFLICT,
    IndexConflict: status.HTTP_409_CONFLICT,
    StoreUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def add_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ConfigError, _config_error)
    app.add_exception_handler(RequestValidationError, _validation_error)


async def _config_error(request: Request, exc: ConfigError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=_STATUS_BY_ERROR[type(exc)])


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI devuelve una lista de errores; el contrato pide un solo texto."""
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'][1:])}: {error['msg']}"
        for error in exc.errors()
    )
    return JSONResponse(
        {"detail": f"Pedido inválido: {problems}"},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
