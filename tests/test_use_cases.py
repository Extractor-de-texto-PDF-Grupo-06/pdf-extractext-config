"""Casos de uso del CRUD de configuración, con el almacén reemplazado por un doble en memoria."""

import pytest

from app.application.entities import ConfigEntry
from app.application.errors import (
    EntryAlreadyExists,
    EntryNotFound,
    IndexConflict,
    InvalidKey,
    StoreUnavailable,
)
from app.application.use_cases import ManageConfig
from tests.fakes import InMemoryConfigStore


@pytest.fixture
def memory_store():
    return InMemoryConfigStore()


@pytest.fixture
def config(memory_store):
    return ManageConfig(memory_store)


def test_crear_guarda_la_entrada(config):
    entry = config.create("web/max_file_size_mb", "10")

    assert entry == ConfigEntry(key="web/max_file_size_mb", value="10", index=1)
    assert config.get("web/max_file_size_mb").value == "10"


def test_crear_una_clave_existente_falla(config):
    config.create("web/max_file_size_mb", "10")

    with pytest.raises(EntryAlreadyExists):
        config.create("web/max_file_size_mb", "50")


@pytest.mark.parametrize(
    "key",
    ["Web/max_file_size_mb", "web", "web/", "/max_file_size_mb", "web/max file", "web/a/b", ""],
)
def test_crear_una_clave_sin_la_forma_servicio_nombre_falla(config, key):
    with pytest.raises(InvalidKey):
        config.create(key, "10")


def test_listar_devuelve_las_entradas_del_prefijo(config):
    config.create("web/max_file_size_mb", "10")
    config.create("documents/limit", "100")

    assert [entry.key for entry in config.list("web/")] == ["web/max_file_size_mb"]


def test_listar_sin_prefijo_devuelve_todas(config):
    config.create("web/max_file_size_mb", "10")
    config.create("documents/limit", "100")

    assert len(config.list("")) == 2


def test_obtener_una_clave_inexistente_falla(config):
    with pytest.raises(EntryNotFound):
        config.get("web/no_existe")


def test_actualizar_sin_indice_cambia_el_valor(config):
    config.create("web/max_file_size_mb", "10")

    entry = config.update("web/max_file_size_mb", "50")

    assert entry == ConfigEntry(key="web/max_file_size_mb", value="50", index=2)


def test_actualizar_con_el_indice_vigente_cambia_el_valor(config):
    created = config.create("web/max_file_size_mb", "10")

    entry = config.update("web/max_file_size_mb", "50", index=created.index)

    assert entry.value == "50"


def test_actualizar_con_un_indice_desactualizado_falla_y_no_cambia_nada(config):
    created = config.create("web/max_file_size_mb", "10")
    config.update("web/max_file_size_mb", "20")

    with pytest.raises(IndexConflict):
        config.update("web/max_file_size_mb", "50", index=created.index)
    assert config.get("web/max_file_size_mb").value == "20"


def test_actualizar_una_clave_inexistente_falla(config):
    with pytest.raises(EntryNotFound):
        config.update("web/no_existe", "50")


def test_borrar_quita_la_entrada(config):
    config.create("web/max_file_size_mb", "10")

    config.delete("web/max_file_size_mb")

    with pytest.raises(EntryNotFound):
        config.get("web/max_file_size_mb")


def test_borrar_una_clave_inexistente_falla(config):
    with pytest.raises(EntryNotFound):
        config.delete("web/no_existe")


def test_esta_disponible_si_el_almacen_tiene_lider(config):
    assert config.is_available() is True


def test_no_esta_disponible_si_el_almacen_no_tiene_lider(config, memory_store):
    memory_store.leader = False

    assert config.is_available() is False


def test_no_esta_disponible_si_el_almacen_no_responde(config, memory_store):
    memory_store.available = False

    assert config.is_available() is False


def test_si_el_almacen_no_responde_las_operaciones_fallan(config, memory_store):
    memory_store.available = False

    with pytest.raises(StoreUnavailable):
        config.get("web/max_file_size_mb")
