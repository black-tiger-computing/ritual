"""
RITUAL FastAPI Server
Main server application with API endpoints
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import load_config
from app.llm_discovery import discover_llm_providers
from app.storage import StorageManager

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RITUAL",
        description="Hermetic LLM Context Management Portal",
        version="1.0.0",
    )

    # Add rate limiter
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    # Load configuration
    config = load_config()
    storage = StorageManager(config)

    # CORS middleware - restrict to same-origin in production
    # For development, you may want to allow specific localhost ports
    allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    allow_credentials = os.environ.get("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    # Security check: prevent wildcard origins with credentials
    if "*" in allowed_origins and allow_credentials:
        logger.warning("CORS configured with wildcard origin and credentials - restricting to same-origin")
        allowed_origins = [o for o in allowed_origins if o != "*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Store dependencies
    app.state.config = config
    app.state.storage = storage

    # Include routers
    from app.routes import health_router, providers_router, mcm_router, sigils_router

    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(providers_router, prefix="/api", tags=["Providers"])
    app.include_router(mcm_router, prefix="/api", tags=["MCM Files"])
    app.include_router(sigils_router, prefix="/api", tags=["Sigils"])

    # Serve frontend
    @app.get("/")
    async def serve_frontend():
        """Serve the main frontend page."""
        frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
        if frontend_path.exists():
            return FileResponse(frontend_path)
        return JSONResponse(
            {"message": "RITUAL API", "version": "1.0.0"},
            media_type="application/json"
        )

    @app.get("/static/{path:path}")
    async def serve_static(path: str):
        """Serve static files with path traversal protection."""
        frontend_dir = (Path(__file__).parent.parent / "frontend").resolve()
        static_path = (frontend_dir / path).resolve()
        
        # Prevent path traversal attacks
        if not static_path.is_relative_to(frontend_dir):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        if static_path.exists() and static_path.is_file():
            return FileResponse(static_path)
        raise HTTPException(status_code=404, detail="File not found")

    logger.info("⊙ RITUAL FastAPI app created successfully")
    return app
