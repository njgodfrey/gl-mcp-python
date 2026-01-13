"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gl_mcp import __version__
from gl_mcp.config import get_settings
from gl_mcp.mcp.transport import get_mcp_router, get_session_count
from gl_mcp.providers import (
    get_provider_registry,
    initialize_providers,
    register_all_providers,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info(f"Starting gl-mcp-python v{__version__}")

    # Register all providers
    register_all_providers()

    # Initialize providers (load credentials)
    provider_status = await initialize_providers()
    for name, status in provider_status.items():
        logger.info(f"Provider '{name}': {'ready' if status else 'unavailable'}")

    yield
    logger.info("Shutting down gl-mcp-python")


app = FastAPI(
    title="GL MCP Server",
    description="Godfrey Labs MCP Server - Python/FastAPI implementation",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MCP router
app.include_router(get_mcp_router())


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    settings = get_settings()
    registry = get_provider_registry()

    return {
        "status": "healthy",
        "service": "gl-mcp-python",
        "version": __version__,
        "auth": "enabled" if settings.auth_enabled else "disabled",
        "providers": await registry.check_all_credentials(),
        "sessions": get_session_count(),
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "gl-mcp-python",
        "version": __version__,
        "docs": "/docs",
    }
