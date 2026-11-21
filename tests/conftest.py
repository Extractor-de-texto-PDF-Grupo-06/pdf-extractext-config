"""Fixtures compartidas por los tests."""

import pytest

from tests.fakes import InMemoryConfigStore


@pytest.fixture(params=["memoria"])
def store(request):
    """Cada implementación del puerto ConfigStore; los tests de contrato corren contra todas."""
    return InMemoryConfigStore()
