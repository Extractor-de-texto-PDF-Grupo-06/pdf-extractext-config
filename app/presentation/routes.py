"""Rutas del contrato. Traefik quita el prefijo /config antes de reenviar."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.application.use_cases import ManageConfig
from app.presentation.schemas import EntryCreate, EntryList, EntryOut, EntryUpdate, Health

router = APIRouter()


def get_config(request: Request) -> ManageConfig:
    return request.app.state.config


Config = Annotated[ManageConfig, Depends(get_config)]


# Va antes que /{key:path}: si no, "health" se tomaría como una clave.
@router.get("/health", response_model=Health)
def health(config: Config) -> Health:
    if not config.is_available():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Consul no tiene líder.")
    return Health(status="ok")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=EntryOut)
def create_entry(body: EntryCreate, config: Config) -> EntryOut:
    return EntryOut.from_entry(config.create(body.key, body.value))


@router.get("/", response_model=EntryList)
def list_entries(config: Config, prefix: str = "") -> EntryList:
    entries = [EntryOut.from_entry(entry) for entry in config.list(prefix)]
    return EntryList(entries=entries, total=len(entries))


@router.get("/{key:path}", response_model=EntryOut)
def get_entry(key: str, config: Config) -> EntryOut:
    return EntryOut.from_entry(config.get(key))


@router.put("/{key:path}", response_model=EntryOut)
def update_entry(key: str, body: EntryUpdate, config: Config) -> EntryOut:
    return EntryOut.from_entry(config.update(key, body.value, body.index))


@router.delete("/{key:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(key: str, config: Config) -> Response:
    config.delete(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
