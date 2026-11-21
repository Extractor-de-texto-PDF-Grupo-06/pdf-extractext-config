"""Punto de entrada: arma la aplicación FastAPI."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractContextManager, asynccontextmanager

from fastapi import FastAPI

from app.application.use_cases import ManageConfig
from app.presentation.errors import add_error_handlers
from app.presentation.routes import router

ConfigFactory = Callable[[], AbstractContextManager[ManageConfig]]


def create_app(config_factory: ConfigFactory) -> FastAPI:
    """``config_factory`` abre los recursos al arrancar y los cierra al apagarse (factor IX)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        with config_factory() as config:
            app.state.config = config
            yield

    app = FastAPI(title="pdf-extractext-config", lifespan=lifespan)
    app.include_router(router)
    add_error_handlers(app)
    return app
