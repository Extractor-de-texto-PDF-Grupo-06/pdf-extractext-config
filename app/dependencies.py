"""Arma las dependencias: el único lugar que conoce las capas a la vez."""

from collections.abc import Iterator
from contextlib import contextmanager

from app.application.use_cases import ManageConfig
from app.core.settings import Settings
from app.infrastructure.consul_registry import ConsulServiceRegistry, ServiceInstance, own_address
from app.infrastructure.consul_store import ConsulConfigStore, connect


@contextmanager
def consul_config(settings: Settings) -> Iterator[ManageConfig]:
    """Los casos de uso sobre Consul. Si está activado, registra la réplica en el catálogo
    mientras está arriba. Al salir la da de baja y cierra el cliente."""
    with connect(settings.consul_url, settings.consul_timeout_seconds) as client:
        config = ManageConfig(ConsulConfigStore(client, settings.consul_kv_root))
        if not settings.service_registration:
            yield config
            return

        registry = ConsulServiceRegistry(client)
        instance = ServiceInstance(
            name=settings.service_name,
            address=settings.service_address or own_address(),
            port=settings.port,
            tags=tuple(settings.service_tags),
        )
        registry.register(instance)
        try:
            yield config
        finally:
            registry.deregister(instance)
