"""Registro de una réplica en el catálogo de Consul, con py-consul.

Traefik lee el catálogo (provider Consul Catalog) y arma las rutas con las etiquetas de cada
servicio. Consul revisa /health de la réplica y Traefik solo le manda tráfico si está sana.
"""

import logging
import socket
from dataclasses import dataclass

import consul
from consul.exceptions import ConsulException

logger = logging.getLogger(__name__)

# Cada cuánto Consul revisa /health. Corto para que Traefik empiece a enrutar enseguida.
_CHECK_INTERVAL = "5s"
# Si la réplica muere sin darse de baja, Consul la borra sola pasado este tiempo.
_DEREGISTER_AFTER = "1m"


@dataclass(frozen=True)
class ServiceInstance:
    name: str
    address: str
    port: int
    tags: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        """Único por réplica: con varias, cada una se registra y se da de baja por separado."""
        return f"{self.name}-{self.address}-{self.port}"

    @property
    def health_url(self) -> str:
        return f"http://{self.address}:{self.port}/health"


def own_address() -> str:
    """La IP de este contenedor en la red de Docker."""
    return socket.gethostbyname(socket.gethostname())


class ConsulServiceRegistry:
    """Si Consul no responde, avisa en el log y sigue: sin registro solo se pierde la ruta
    pública de Traefik; web llega a config directo por la red interna."""

    def __init__(self, client: consul.Consul) -> None:
        self._service = client.agent.service

    def register(self, instance: ServiceInstance) -> bool:
        try:
            self._service.register(
                instance.name,
                service_id=instance.id,
                address=instance.address,
                port=instance.port,
                tags=list(instance.tags),
                check=consul.Check.http(
                    instance.health_url, _CHECK_INTERVAL, deregister=_DEREGISTER_AFTER
                ),
            )
        except (ConsulException, OSError) as error:
            logger.warning("No se pudo registrar %s en Consul: %s", instance.id, error)
            return False
        logger.info("Registrado en Consul como %s", instance.id)
        return True

    def deregister(self, instance: ServiceInstance) -> None:
        try:
            self._service.deregister(instance.id)
        except (ConsulException, OSError) as error:
            logger.warning("No se pudo dar de baja %s en Consul: %s", instance.id, error)
