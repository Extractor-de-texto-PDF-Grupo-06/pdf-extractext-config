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
