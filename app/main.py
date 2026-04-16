from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import dispose_engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

configure_logging()
logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    yield
    await dispose_engine()
    logger.info("Shutting down %s", settings.app_name)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["root"], summary="Root endpoint")
    async def root() -> dict[str, str]:
        return {
            "message": "WM Distribuidora API online.",
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
            "api_base": settings.api_v1_prefix,
        }

    return app


app = create_application()
