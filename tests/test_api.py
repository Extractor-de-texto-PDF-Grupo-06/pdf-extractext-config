"""Contrato HTTP de config (SPEC.md), con el almacén reemplazado por un doble en memoria."""

from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from app.application.use_cases import ManageConfig
from app.main import create_app
from tests.fakes import InMemoryConfigStore


@pytest.fixture
def memory_store():
    return InMemoryConfigStore()


@pytest.fixture
def client(memory_store):
    app = create_app(lambda: nullcontext(ManageConfig(memory_store)))
    with TestClient(app) as client:
        yield client


def test_post_crea_la_entrada(client):
    response = client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    assert response.status_code == 201
    assert response.json() == {"key": "web/max_file_size_mb", "value": "10", "index": 1}


def test_post_de_una_clave_existente_responde_409(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.post("/", json={"key": "web/max_file_size_mb", "value": "50"})

    assert response.status_code == 409
    assert response.json() == {"detail": "La clave 'web/max_file_size_mb' ya existe."}


def test_post_de_una_clave_mal_formada_responde_422(client):
    response = client.post("/", json={"key": "Web/Max", "value": "10"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "La clave 'Web/Max' no tiene la forma <servicio>/<nombre> en minúsculas."
    }


def test_post_sin_valor_responde_422_con_detail_de_texto(client):
    response = client.post("/", json={"key": "web/max_file_size_mb"})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
    assert "value" in response.json()["detail"]


def test_get_lista_las_entradas_del_prefijo(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})
    client.post("/", json={"key": "documents/limit", "value": "100"})

    response = client.get("/", params={"prefix": "web/"})

    assert response.status_code == 200
    assert response.json() == {
        "entries": [{"key": "web/max_file_size_mb", "value": "10", "index": 1}],
        "total": 1,
    }


def test_get_sin_prefijo_lista_todas_las_entradas(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})
    client.post("/", json={"key": "documents/limit", "value": "100"})

    assert client.get("/").json()["total"] == 2


def test_get_de_una_clave_devuelve_la_entrada(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.get("/web/max_file_size_mb")

    assert response.status_code == 200
    assert response.json() == {"key": "web/max_file_size_mb", "value": "10", "index": 1}


def test_get_de_una_clave_inexistente_responde_404(client):
    response = client.get("/web/no_existe")

    assert response.status_code == 404
    assert response.json() == {"detail": "La clave 'web/no_existe' no existe."}


def test_put_actualiza_el_valor(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.put("/web/max_file_size_mb", json={"value": "50"})

    assert response.status_code == 200
    assert response.json() == {"key": "web/max_file_size_mb", "value": "50", "index": 2}


def test_put_con_el_indice_vigente_actualiza_el_valor(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.put("/web/max_file_size_mb", json={"value": "50", "index": 1})

    assert response.status_code == 200
    assert response.json()["value"] == "50"


def test_put_con_un_indice_desactualizado_responde_409(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})
    client.put("/web/max_file_size_mb", json={"value": "20"})

    response = client.put("/web/max_file_size_mb", json={"value": "50", "index": 1})

    assert response.status_code == 409
    assert client.get("/web/max_file_size_mb").json()["value"] == "20"


def test_put_de_una_clave_inexistente_responde_404(client):
    response = client.put("/web/no_existe", json={"value": "50"})

    assert response.status_code == 404


def test_put_sin_valor_responde_422(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.put("/web/max_file_size_mb", json={})

    assert response.status_code == 422


def test_delete_borra_la_entrada(client):
    client.post("/", json={"key": "web/max_file_size_mb", "value": "10"})

    response = client.delete("/web/max_file_size_mb")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/web/max_file_size_mb").status_code == 404


def test_delete_de_una_clave_inexistente_responde_404(client):
    assert client.delete("/web/no_existe").status_code == 404


def test_health_responde_200_si_consul_tiene_lider(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_responde_503_si_consul_no_tiene_lider(client, memory_store):
    memory_store.leader = False

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Consul no tiene líder."}


def test_si_consul_no_responde_las_operaciones_responden_503(client, memory_store):
    memory_store.available = False

    response = client.get("/web/max_file_size_mb")

    assert response.status_code == 503
    assert response.json() == {"detail": "El almacén de configuración no responde."}
