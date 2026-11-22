"""Arma las dependencias: el único lugar que conoce las capas a la vez."""

from collections.abc import Iterator
from contextlib import contextmanager

from app.application.use_cases import ManageConfig
from app.core.settings import Settings
from app.infrastructure.consul_store import ConsulConfigStore, connect


@contextmanager
def consul_config(settings: Settings) -> Iterator[ManageConfig]:
    """Los casos de uso sobre Consul. Cierra el cliente al salir."""
    with connect(settings.consul_url, settings.consul_timeout_seconds) as client:
        yield ManageConfig(ConsulConfigStore(client, settings.consul_kv_root))
