"""Doble en memoria del puerto ConfigStore, con la misma semántica que el KV de Consul."""

from itertools import count

from app.application.entities import ConfigEntry
from app.application.errors import StoreUnavailable


class InMemoryConfigStore:
    """Guarda las entradas en un diccionario y numera cada escritura como lo hace Consul."""

    def __init__(self) -> None:
        self._entries: dict[str, ConfigEntry] = {}
        self._next_index = count(1)
        self.leader = True
        self.available = True

    def get(self, key: str) -> ConfigEntry | None:
        self._check_available()
        return self._entries.get(key)

    def list(self, prefix: str) -> list[ConfigEntry]:
        self._check_available()
        return [entry for key, entry in sorted(self._entries.items()) if key.startswith(prefix)]

    def create(self, key: str, value: str) -> ConfigEntry | None:
        self._check_available()
        if key in self._entries:
            return None
        return self._write(key, value)

    def replace(self, key: str, value: str, index: int) -> ConfigEntry | None:
        self._check_available()
        current = self._entries.get(key)
        current_index = current.index if current else 0
        if current_index != index:
            return None
        return self._write(key, value)

    def delete(self, key: str) -> None:
        self._check_available()
        self._entries.pop(key, None)

    def has_leader(self) -> bool:
        self._check_available()
        return self.leader

    def _write(self, key: str, value: str) -> ConfigEntry:
        entry = ConfigEntry(key=key, value=value, index=next(self._next_index))
        self._entries[key] = entry
        return entry

    def _check_available(self) -> None:
        if not self.available:
            raise StoreUnavailable()
