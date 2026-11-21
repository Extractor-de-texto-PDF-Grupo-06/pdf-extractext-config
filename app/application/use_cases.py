"""Casos de uso del CRUD de la configuración centralizada."""

from app.application.entities import ConfigEntry, validate_key
from app.application.errors import (
    EntryAlreadyExists,
    EntryNotFound,
    IndexConflict,
    StoreUnavailable,
)
from app.application.ports import ConfigStore


class ManageConfig:
    """Crear, listar, leer, actualizar y borrar entradas. Solo conoce el puerto, no Consul."""

    def __init__(self, store: ConfigStore) -> None:
        self._store = store

    def create(self, key: str, value: str) -> ConfigEntry:
        validate_key(key)
        entry = self._store.create(key, value)
        if entry is None:
            raise EntryAlreadyExists(key)
        return entry

    def list(self, prefix: str) -> list[ConfigEntry]:
        return self._store.list(prefix)

    def get(self, key: str) -> ConfigEntry:
        entry = self._store.get(key)
        if entry is None:
            raise EntryNotFound(key)
        return entry

    def update(self, key: str, value: str, index: int | None = None) -> ConfigEntry:
        """Sin ``index`` se usa el índice leído, así una escritura concurrente tampoco se pisa."""
        current = self.get(key)
        expected = current.index if index is None else index
        entry = self._store.replace(key, value, expected)
        if entry is None:
            raise IndexConflict(key)
        return entry

    def delete(self, key: str) -> None:
        self.get(key)
        self._store.delete(key)

    def is_available(self) -> bool:
        try:
            return self._store.has_leader()
        except StoreUnavailable:
            return False
