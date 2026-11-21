"""Entidades de la configuración centralizada."""

import re
from dataclasses import dataclass

from app.application.errors import InvalidKey

_KEY_FORMAT = re.compile(r"[a-z0-9_-]+/[a-z0-9_-]+")


@dataclass(frozen=True)
class ConfigEntry:
    """Un valor de configuración. ``index`` cambia con cada escritura y sirve para el check-and-set."""

    key: str
    value: str
    index: int


def validate_key(key: str) -> None:
    """Exige la forma ``<servicio>/<nombre>`` en minúsculas, por ejemplo ``web/max_file_size_mb``."""
    if not _KEY_FORMAT.fullmatch(key):
        raise InvalidKey(key)
