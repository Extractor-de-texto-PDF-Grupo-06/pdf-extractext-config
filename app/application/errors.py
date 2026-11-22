"""Errores de los casos de uso. El mensaje es el que recibe el cliente en ``detail``."""


class ConfigError(Exception):
    """Base de los errores de configuración."""


class InvalidKey(ConfigError):
    def __init__(self, key: str) -> None:
        super().__init__(
            f"La clave '{key}' no tiene la forma <servicio>/<nombre> en minúsculas."
        )


class EntryNotFound(ConfigError):
    def __init__(self, key: str) -> None:
        super().__init__(f"La clave '{key}' no existe.")


class EntryAlreadyExists(ConfigError):
    def __init__(self, key: str) -> None:
        super().__init__(f"La clave '{key}' ya existe.")


class IndexConflict(ConfigError):
    def __init__(self, key: str) -> None:
        super().__init__(
            f"La clave '{key}' cambió desde que se leyó. Volvé a leerla y reintentá."
        )


class StoreUnavailable(ConfigError):
    def __init__(self) -> None:
        super().__init__("El almacén de configuración no responde.")
