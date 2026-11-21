"""Adaptador del puerto ConfigStore sobre el KV de Consul, con py-consul."""

from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlsplit

import consul
from consul.exceptions import ConsulException

from app.application.entities import ConfigEntry
from app.application.errors import StoreUnavailable

# Consul interpreta cas=0 como "escribir solo si la clave no existe".
_ONLY_IF_ABSENT = 0


def connect(url: str, timeout_seconds: float) -> consul.Consul:
    """Cliente de Consul a partir de una URL como ``http://consul:8500``."""
    parts = urlsplit(url)
    return consul.Consul(
        host=parts.hostname,
        port=parts.port,
        scheme=parts.scheme,
        connections_timeout=timeout_seconds,
    )


class ConsulConfigStore:
    """Guarda cada entrada como ``<root>/<clave>``; el índice es el ModifyIndex de Consul."""

    def __init__(self, client: consul.Consul, root: str) -> None:
        self._kv = client.kv
        self._status = client.status
        self._root = f"{root.strip('/')}/"

    def get(self, key: str) -> ConfigEntry | None:
        with _translate_errors():
            _, item = self._kv.get(self._root + key)
        return self._to_entry(item) if item else None

    def list(self, prefix: str) -> list[ConfigEntry]:
        with _translate_errors():
            _, items = self._kv.get(self._root + prefix, recurse=True)
        # Las claves que terminan en "/" son carpetas que crea la interfaz de Consul.
        return [self._to_entry(item) for item in items or [] if not item["Key"].endswith("/")]

    def create(self, key: str, value: str) -> ConfigEntry | None:
        return self._put(key, value, _ONLY_IF_ABSENT)

    def replace(self, key: str, value: str, index: int) -> ConfigEntry | None:
        return self._put(key, value, index)

    def delete(self, key: str) -> None:
        with _translate_errors():
            self._kv.delete(self._root + key)

    def has_leader(self) -> bool:
        with _translate_errors():
            return bool(self._status.leader())

    def _put(self, key: str, value: str, cas: int) -> ConfigEntry | None:
        with _translate_errors():
            written = self._kv.put(self._root + key, value, cas=cas)
        return self.get(key) if written else None

    def _to_entry(self, item: dict) -> ConfigEntry:
        raw = item["Value"]
        return ConfigEntry(
            key=item["Key"].removeprefix(self._root),
            value=raw.decode("utf-8") if raw else "",
            index=item["ModifyIndex"],
        )


@contextmanager
def _translate_errors() -> Iterator[None]:
    """Los errores de red de requests heredan de OSError; los de Consul, de ConsulException."""
    try:
        yield
    except (ConsulException, OSError) as error:
        raise StoreUnavailable() from error
