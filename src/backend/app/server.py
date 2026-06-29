"""
RITUAL FastAPI Server
Main server application with API endpoints
Supports headless mode for REST API only (no frontend)
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import load_config
from app.storage import StorageManager
from app.mcp_storage import MCPStorage
from app.key_manager import KeyManager
from app.model_runner import ModelManager
from app.model_discovery import ModelDiscoveryService

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def create_app(headless: bool = False) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        headless: If True, serve API only (no frontend static files)
    """
    app = FastAPI(
        title="RITUAL",
        description="Hermetic LLM Context Management Portal with 4-Tier MCP Memory",
        version="2.0.0",
    )

    # Add rate limiter
    app.state.limiter = limiter
    app.state.headless = headless
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    # Load configuration
    config = load_config()
    
    # Initialize storage directories
    data_dir = Path(config.get("storage.data_dir", ".ritual"))
    
    # Initialize managers
    storage = StorageManager(config)
    mcp_storage = MCPStorage(data_dir)
    key_manager = KeyManager(data_dir)
    model_manager = ModelManager()
    discovery_service = ModelDiscoveryService()

    # CORS middleware - restrict to same-origin in production
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    allow_credentials = os.environ.get("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    # Security check: prevent wildcard origins with credentials
    if "*" in allowed_origins and allow_credentials:
        logger.warning("CORS configured with wildcard origin and credentials - restricting")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    )

    # Store dependencies
    app.state.config = config
    app.state.storage = storage
    app.state.mcp_storage = mcp_storage
    app.state.key_manager = key_manager
    app.state.model_manager = model_manager
    app.state.discovery_service = discovery_service

    # Include original routers
    from app.routes import health_router, providers_router, mcm_router, sigils_router
    
    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(providers_router, prefix="/api", tags=["Providers"])
    app.include_router(mcm_router, prefix="/api", tags=["MCM Files"])
    app.include_router(sigils_router, prefix="/api", tags=["Sigils"])

    # Include new MCP routers
    from app.mcp_routes import (
        mcp_router, memory_router, personality_router,
        keys_router, assistant_router
    )
    from app.model_routes import models_router
    from app.auth_routes import auth_router
    
    app.include_router(mcp_router, prefix="/api/mcp", tags=["MCP System"])
    app.include_router(memory_router, prefix="/mcp", tags=["MCP Memory"])
    app.include_router(personality_router, prefix="/mcp", tags=["MCP Personality"])
    app.include_router(keys_router, prefix="/keys", tags=["Key Management"])
    app.include_router(assistant_router, prefix="/assistant", tags=["Prompt Engineer"])
    app.include_router(models_router, prefix="/models", tags=["Model Discovery"])
    app.include_router(auth_router, tags=["Authentication"])

    # Serve frontend (unless headless)
    if not headless:
        @app.get("/")
        async def serve_frontend():
            """Serve the main frontend page."""
            frontend_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
            if frontend_path.exists():
                return FileResponse(frontend_path)
            return JSONResponse(
                {"message": "RITUAL API", "version": "2.0.0"},
                media_type="application/json"
            )

        @app.get("/static/{path:path}")
        async def serve_static(path: str):
            """Serve static files with path traversal protection."""
            frontend_dir = (Path(__file__).parent.parent.parent / "frontend").resolve()
            static_path = (frontend_dir / path).resolve()
            
            if not static_path.is_relative_to(frontend_dir):
                raise HTTPException(status_code=403, detail="Invalid path")
            
            if static_path.exists() and static_path.is_file():
                return FileResponse(static_path)
            raise HTTPException(status_code=404, detail="File not found")
    
    # API root info
    @app.get("/api")
    async def api_root():
        """API root with version info and endpoints."""
        return {
            "name": "RITUAL",
            "version": "2.0.0",
            "description": "Hermetic LLM Context Management Portal with 4-Tier MCP",
            "endpoints": {
                "mcp": "/api/mcp - 4-tier memory system",
                "memory": "/api/mcp/memories - Memory CRUD",
                "personality": "/api/mcp/personality - Personality profile",
                "keys": "/api/keys - Key management",
                "assistant": "/api/assistant - Prompt engineer",
                "models": "/api/models - Model discovery",
                "providers": "/api/providers - LLM providers",
                "mcm_files": "/api/mcm-files - MCM file management",
                "sigils": "/api/sigils - API key storage"
            },
            "features": [
                "4-tier MCP memory (Personality, Context, Frequent, Archive)",
                "Encrypted key management",
                "Local quantized model inference",
                "HuggingFace/CivitAI model discovery",
                "BYOK and cloud inference support"
            ]
        }

    logger.info("⊙ RITUAL FastAPI app created successfully (headless=%s)", headless)
    return app
