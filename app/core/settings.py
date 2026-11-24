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

    # Registro en el catálogo de Consul, para que Traefik descubra config (provider Consul
    # Catalog). Apagado por defecto: en desarrollo y en los tests no hay a quién avisarle.
    service_registration: bool = False
    service_name: str = "config"
    # Dirección con la que Consul y Traefik llegan a esta réplica. Sin valor, la IP propia.
    service_address: str | None = None
    # Las etiquetas de Traefik (rutas y middlewares). Las decide quien despliega, no config.
    # En JSON, porque una etiqueta puede tener comas: ["traefik.enable=true", "..."].
    service_tags: list[str] = []
