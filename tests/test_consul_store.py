"""Adaptador de Consul sin un Consul real: conexión y traducción de errores.

El comportamiento contra un Consul real lo cubren los tests de contrato (``-m integration``).
"""

import pytest

from app.application.errors import StoreUnavailable
from app.infrastructure.consul_store import ConsulConfigStore, connect

# Nadie escucha en el puerto 1, así que la conexión se rechaza enseguida.
CONSUL_APAGADO = "http://127.0.0.1:1"


def test_connect_usa_el_esquema_el_host_y_el_puerto_de_la_url():
    with connect("https://consul.example:8501", timeout_seconds=2) as client:
        assert client.http.base_uri == "https://consul.example:8501"


@pytest.fixture
def unreachable_store():
    with connect(CONSUL_APAGADO, timeout_seconds=2) as client:
        yield ConsulConfigStore(client, root="pdf-extractext")


def test_si_consul_no_responde_leer_lanza_store_unavailable(unreachable_store):
    with pytest.raises(StoreUnavailable):
        unreachable_store.get("web/max_file_size_mb")


def test_si_consul_no_responde_escribir_lanza_store_unavailable(unreachable_store):
    with pytest.raises(StoreUnavailable):
        unreachable_store.create("web/max_file_size_mb", "10")


def test_si_consul_no_responde_el_lider_lanza_store_unavailable(unreachable_store):
    with pytest.raises(StoreUnavailable):
        unreachable_store.has_leader()
