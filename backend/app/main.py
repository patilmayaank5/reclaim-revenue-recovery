"""Reclaim FastAPI application factory.

This module creates the FastAPI application instance.
Routes, middleware, and event handlers will be added in later phases.
"""

from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    from app.api.v1 import api_router

    @app.get("/health")
    async def health_check() -> dict:
        """Basic health check endpoint."""
        return {"status": "healthy", "version": settings.VERSION}

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
