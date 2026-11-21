"""Fixtures compartidas por los tests."""

from uuid import uuid4

import pytest

from app.application.errors import StoreUnavailable
from app.core.settings import Settings
from app.infrastructure.consul_store import ConsulConfigStore, connect
from tests.fakes import InMemoryConfigStore


@pytest.fixture(params=["memoria", pytest.param("consul", marks=pytest.mark.integration)])
def store(request):
    """Cada implementación del puerto ConfigStore; los tests de contrato corren contra todas."""
    if request.param == "memoria":
        yield InMemoryConfigStore()
        return
    yield from _consul_store()


def _consul_store():
    """Un Consul real (CONSUL_URL), con una raíz propia que se borra al terminar."""
    settings = Settings()
    root = f"pdf-extractext-test/{uuid4().hex}"
    with connect(settings.consul_url, settings.consul_timeout_seconds) as client:
        store = ConsulConfigStore(client, root)
        try:
            if not store.has_leader():
                pytest.skip("Consul no tiene líder")
        except StoreUnavailable:
            pytest.skip(f"Consul no responde en {settings.consul_url}")
        yield store
        client.kv.delete(f"{root}/", recurse=True)
