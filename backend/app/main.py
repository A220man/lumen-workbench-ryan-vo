"""FastAPI application entry point for lumen-workbench-ryan-vo."""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import os
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup: initialize DB connections, load configurations
    from ..core.db import init_db
    init_db()
    logger.info("Application startup complete")
    yield
    # Shutdown: cleanup connections
    logger.info("Application shutdown complete")

def get_app() -> FastAPI:
    """Factory function to create FastAPI application."""
    app = FastAPI(
        title="Lumen Workbench",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Include routers
    from .api import router as api_router
    from .api.auth import router as auth_router
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "service": "lumen-workbench"}
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint returning service info."""
        return {
            "name": "Lumen Workbench API",
            "version": "1.0.0",
            "description": "AI/ML developer tools for PS5 executable porting analysis"
        }
    
    return app

# Create the app instance for Docker/local use
app = get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)