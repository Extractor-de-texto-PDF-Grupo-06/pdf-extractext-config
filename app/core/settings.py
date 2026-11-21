"""Única fuente de configuración: variables de entorno (factor III). Ningún otro módulo lee os.environ."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Cambiar de Consul es cambiar esta URL (factor IV).
    consul_url: str = "http://localhost:8500"
    # Todas las claves viven bajo esta raíz del KV: pdf-extractext/web/max_file_size_mb.
    consul_kv_root: str = "pdf-extractext"
    # Corto para que /health responda rápido aunque Consul no conteste.
    consul_timeout_seconds: float = 2.0
    # Puerto HTTP del servicio (factor VII).
    port: int = 8000
