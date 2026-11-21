"""Puertos: lo que los casos de uso necesitan del exterior."""

from typing import Protocol

from app.application.entities import ConfigEntry


class ConfigStore(Protocol):
    """Almacén clave-valor con check-and-set. Si no responde, lanza ``StoreUnavailable``."""

    def get(self, key: str) -> ConfigEntry | None: ...

    def list(self, prefix: str) -> list[ConfigEntry]:
        """Las entradas cuya clave empieza con ``prefix``, ordenadas por clave."""
        ...

    def create(self, key: str, value: str) -> ConfigEntry | None:
        """Crea la entrada. Devuelve ``None`` si la clave ya existe."""
        ...

    def replace(self, key: str, value: str, index: int) -> ConfigEntry | None:
        """Escribe solo si el índice actual es ``index``. Devuelve ``None`` si no coincide."""
        ...

    def delete(self, key: str) -> None: ...

    def has_leader(self) -> bool: ...
