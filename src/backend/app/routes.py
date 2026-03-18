"""
RITUAL API Routes
All REST API endpoints for the application
"""

import logging
import re
from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.llm_discovery import LLMProvider, check_provider_connection, discover_llm_providers

logger = logging.getLogger(__name__)

# Rate limiter instance (must match server.py configuration)
limiter = Limiter(key_func=get_remote_address)

# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    version: str


# Constants for input validation
MAX_NAME_LENGTH = 255
MAX_CONTENT_LENGTH = 1_000_000  # 1MB
VALID_NAME_PATTERN = re.compile(r'^[\w\s\-\.\,\:\;]+$')


class MCMFileCreate(BaseModel):
    name: str
    content: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > MAX_NAME_LENGTH:
            raise ValueError(f'Name cannot exceed {MAX_NAME_LENGTH} characters')
        if not VALID_NAME_PATTERN.match(v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) > MAX_CONTENT_LENGTH:
            raise ValueError(f'Content cannot exceed {MAX_CONTENT_LENGTH} characters')
        return v


class MCMFileUpdate(BaseModel):
    name: str
    content: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > MAX_NAME_LENGTH:
            raise ValueError(f'Name cannot exceed {MAX_NAME_LENGTH} characters')
        if not VALID_NAME_PATTERN.match(v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) > MAX_CONTENT_LENGTH:
            raise ValueError(f'Content cannot exceed {MAX_CONTENT_LENGTH} characters')
        return v


class SigilCreate(BaseModel):
    name: str
    provider: str
    api_key: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > MAX_NAME_LENGTH:
            raise ValueError(f'Name cannot exceed {MAX_NAME_LENGTH} characters')
        return v.strip()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed_providers = ['lm-studio', 'msty', 'openai', 'anthropic']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        if len(v) > 2048:
            raise ValueError('API key is too long (max 2048 characters)')
        return v


# Health Router
health_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


# Providers Router
providers_router = APIRouter()


@providers_router.get("/providers")
async def get_providers(request: Request):
    """Get all available LLM providers."""
    config = request.app.state.config
    providers = discover_llm_providers(config)

    # Check connection status for each provider
    for provider in providers:
        if provider.enabled:
            check_provider_connection(provider)

    return {"providers": [p.to_dict() for p in providers]}


@providers_router.get("/providers/{provider_id}/models")
async def get_provider_models(provider_id: str, request: Request):
    """Get models from a specific provider."""
    from app.llm_discovery import get_provider_models

    config = request.app.state.config
    providers = discover_llm_providers(config)

    provider = None
    for p in providers:
        if p.id == provider_id:
            provider = p
            break

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    models = get_provider_models(provider)
    return {"provider": provider.name, "models": models}


# MCM Files Router
mcm_router = APIRouter()


@mcm_router.get("/mcm-files")
async def get_mcm_files(request: Request):
    """Get all MCM files."""
    storage = request.app.state.storage
    files = storage.get_mcm_files()
    return {"files": files}


@mcm_router.get("/mcm-files/{file_id}")
async def get_mcm_file(file_id: str, request: Request):
    """Get a specific MCM file."""
    storage = request.app.state.storage
    file = storage.get_mcm_file(file_id)

    if not file:
        raise HTTPException(status_code=404, detail="MCM file not found")

    return file


@mcm_router.post("/mcm-files")
@limiter.limit("30/minute")
async def create_mcm_file(request: Request, mcm_data: MCMFileCreate):
    """Create a new MCM file."""
    storage = request.app.state.storage
    file = storage.create_mcm_file(mcm_data.name, mcm_data.content)
    return file


@mcm_router.put("/mcm-files/{file_id}")
@limiter.limit("30/minute")
async def update_mcm_file(request: Request, file_id: str, mcm_data: MCMFileUpdate):
    """Update an existing MCM file."""
    storage = request.app.state.storage
    file = storage.update_mcm_file(file_id, mcm_data.name, mcm_data.content)

    if not file:
        raise HTTPException(status_code=404, detail="MCM file not found")

    return file


@mcm_router.delete("/mcm-files/{file_id}")
@limiter.limit("30/minute")
async def delete_mcm_file(request: Request, file_id: str):
    """Delete an MCM file."""
    storage = request.app.state.storage
    success = storage.delete_mcm_file(file_id)

    if not success:
        raise HTTPException(status_code=404, detail="MCM file not found")

    return {"success": True}


# Sigils Router
sigils_router = APIRouter()


@sigils_router.get("/sigils")
async def get_sigils(request: Request):
    """Get all stored API keys."""
    storage = request.app.state.storage
    sigils = storage.get_sigils()
    return {"sigils": sigils}


@sigils_router.post("/sigils")
@limiter.limit("10/minute")
async def create_sigil(request: Request, sigil_data: SigilCreate):
    """Create a new sigil (API key)."""
    storage = request.app.state.storage
    sigil = storage.create_sigil(sigil_data.name, sigil_data.provider, sigil_data.api_key)
    return sigil


@sigils_router.delete("/sigils/{sigil_id}")
@limiter.limit("10/minute")
async def delete_sigil(request: Request, sigil_id: str):
    """Delete a sigil (API key)."""
    storage = request.app.state.storage
    success = storage.delete_sigil(sigil_id)

    if not success:
        raise HTTPException(status_code=404, detail="Sigil not found")

    return {"success": True}
