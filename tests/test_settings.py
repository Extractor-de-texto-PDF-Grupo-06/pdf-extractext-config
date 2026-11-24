"""Settings: toda la configuración entra por variables de entorno (factor III)."""

from app.core.settings import Settings


def test_valores_por_defecto_para_desarrollo_local(monkeypatch):
    for name in ("CONSUL_URL", "CONSUL_KV_ROOT", "CONSUL_TIMEOUT_SECONDS", "PORT"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.consul_url == "http://localhost:8500"
    assert settings.consul_kv_root == "pdf-extractext"
    assert settings.consul_timeout_seconds == 2.0
    assert settings.port == 8000


def test_las_variables_de_entorno_pisan_los_valores_por_defecto(monkeypatch):
    monkeypatch.setenv("CONSUL_URL", "http://consul:8500")
    monkeypatch.setenv("PORT", "9000")

    settings = Settings(_env_file=None)

    assert settings.consul_url == "http://consul:8500"
    assert settings.port == 9000


def test_el_registro_en_consul_esta_apagado_por_defecto(monkeypatch):
    for name in ("SERVICE_REGISTRATION", "SERVICE_NAME", "SERVICE_ADDRESS", "SERVICE_TAGS"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.service_registration is False
    assert settings.service_name == "config"
    assert settings.service_address is None
    assert settings.service_tags == []


def test_las_etiquetas_del_registro_llegan_como_json(monkeypatch):
    # Una etiqueta de Traefik puede tener comas (middlewares=a,b): por eso JSON y no CSV.
    monkeypatch.setenv("SERVICE_REGISTRATION", "true")
    monkeypatch.setenv("SERVICE_TAGS", '["traefik.enable=true", "traefik.http.routers.config.middlewares=a,b"]')

    settings = Settings(_env_file=None)

    assert settings.service_registration is True
    assert settings.service_tags == [
        "traefik.enable=true",
        "traefik.http.routers.config.middlewares=a,b",
    ]
