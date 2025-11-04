"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import get_logger
from app.api.routes import router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Application starting up", app_name=settings.app.name, version=settings.app.version)
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e), exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Application shutting down")
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="AI-driven academic automation tool for paper analysis and report generation",
        lifespan=lifespan,
        debug=settings.app.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app_name": settings.app.name,
            "version": settings.app.version,
            "env": settings.app.env,
        }

    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "message": "Welcome to AutoScholar API",
            "version": settings.app.version,
            "docs": "/docs",
        }

    return app


# Create application instance
app = create_app()
