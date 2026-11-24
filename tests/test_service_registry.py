"""Registro de config en el catálogo de Consul, para que Traefik lo descubra (provider Consul Catalog)."""

from uuid import uuid4

import pytest

from app.core.settings import Settings
from app.infrastructure.consul_registry import ConsulServiceRegistry, ServiceInstance
from app.infrastructure.consul_store import connect

# Nadie escucha en el puerto 1, así que la conexión se rechaza enseguida.
CONSUL_APAGADO = "http://127.0.0.1:1"

INSTANCIA = ServiceInstance(
    name="config",
    address="172.18.0.7",
    port=8000,
    tags=("traefik.enable=true", "traefik.http.routers.config.rule=PathPrefix(`/config`)"),
)


class FakeAgentService:
    def __init__(self):
        self.registered = []
        self.deregistered = []

    def register(self, name, **kwargs):
        self.registered.append({"name": name, **kwargs})
        return True

    def deregister(self, service_id):
        self.deregistered.append(service_id)
        return True


class FakeClient:
    def __init__(self):
        self.agent = type("Agent", (), {})()
        self.agent.service = FakeAgentService()


def test_cada_replica_tiene_un_id_propio():
    otra = ServiceInstance(name="config", address="172.18.0.8", port=8000)

    assert INSTANCIA.id == "config-172.18.0.7-8000"
    assert INSTANCIA.id != otra.id


def test_registra_el_servicio_con_sus_etiquetas_y_un_health_check():
    client = FakeClient()

    assert ConsulServiceRegistry(client).register(INSTANCIA) is True

    [registro] = client.agent.service.registered
    assert registro["name"] == "config"
    assert registro["service_id"] == "config-172.18.0.7-8000"
    assert registro["address"] == "172.18.0.7"
    assert registro["port"] == 8000
    assert registro["tags"] == list(INSTANCIA.tags)
    # Consul solo da por sana la instancia si responde /health, y Traefik solo enruta a las sanas.
    assert registro["check"]["http"] == "http://172.18.0.7:8000/health"
    # Si la instancia muere sin darse de baja, Consul la borra sola.
    assert "DeregisterCriticalServiceAfter" in registro["check"]


def test_al_apagarse_se_da_de_baja():
    client = FakeClient()

    ConsulServiceRegistry(client).deregister(INSTANCIA)

    assert client.agent.service.deregistered == ["config-172.18.0.7-8000"]


def test_si_consul_no_responde_el_registro_no_impide_arrancar():
    # web no pasa por Traefik para llegar a config: sin registro solo se pierde la ruta pública.
    with connect(CONSUL_APAGADO, timeout_seconds=2) as client:
        registry = ConsulServiceRegistry(client)

        assert registry.register(INSTANCIA) is False
        registry.deregister(INSTANCIA)


@pytest.mark.integration
def test_contra_consul_real_aparece_en_el_catalogo_y_se_va_al_darse_de_baja():
    settings = Settings()
    instancia = ServiceInstance(
        name=f"config-test-{uuid4().hex[:8]}",
        address="127.0.0.1",
        port=8000,
        tags=("traefik.enable=true",),
    )
    with connect(settings.consul_url, settings.consul_timeout_seconds) as client:
        registry = ConsulServiceRegistry(client)
        if not registry.register(instancia):
            pytest.skip(f"Consul no responde en {settings.consul_url}")
        try:
            _, servicios = client.catalog.service(instancia.name)
            assert [s["ServiceID"] for s in servicios] == [instancia.id]
            assert servicios[0]["ServiceTags"] == ["traefik.enable=true"]
        finally:
            registry.deregister(instancia)

        _, servicios = client.catalog.service(instancia.name)
        assert servicios == []


class RecordingRegistry:
    calls: list = []

    def __init__(self, client):
        pass

    def register(self, instance):
        RecordingRegistry.calls.append(("register", instance))
        return True

    def deregister(self, instance):
        RecordingRegistry.calls.append(("deregister", instance))


def test_config_se_registra_al_arrancar_y_se_da_de_baja_al_apagarse(monkeypatch):
    from app import dependencies

    RecordingRegistry.calls = []
    monkeypatch.setattr(dependencies, "ConsulServiceRegistry", RecordingRegistry)
    settings = Settings(
        _env_file=None,
        service_registration=True,
        service_address="172.18.0.7",
        service_tags=["traefik.enable=true"],
    )

    with dependencies.consul_config(settings):
        assert RecordingRegistry.calls == [
            ("register", ServiceInstance("config", "172.18.0.7", 8000, ("traefik.enable=true",)))
        ]

    assert RecordingRegistry.calls[-1][0] == "deregister"


def test_sin_registro_activado_no_toca_el_catalogo(monkeypatch):
    from app import dependencies

    RecordingRegistry.calls = []
    monkeypatch.setattr(dependencies, "ConsulServiceRegistry", RecordingRegistry)

    with dependencies.consul_config(Settings(_env_file=None, service_registration=False)):
        pass

    assert RecordingRegistry.calls == []
