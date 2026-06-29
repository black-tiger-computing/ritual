"""
RITUAL MCP Routes
4-Tier Memory System API + Prompt Engineer Assistant + Key Management
"""

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, field_validator

from app.mcp import (
    MCPMemory, MCPSession, MCPSystemStats, MCPTier,
    PersonalityProfile, TIER_NAMES, TIER_DISPLAY,
    generate_mcp_context, generate_system_prompt
)
from app.key_manager import KeyManager, KeyProvider, KeyType

logger = logging.getLogger(__name__)

# Routers
mcp_router = APIRouter()
memory_router = APIRouter()
personality_router = APIRouter()
keys_router = APIRouter()
assistant_router = APIRouter()


# ============================================================================
# Memory Tier Models
# ============================================================================

class MemoryCreate(BaseModel):
    key: str
    content: str
    tier: int = 1
    tags: List[str] = []
    source: str = "user"
    
    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v: int) -> int:
        if v < 0 or v > 3:
            raise ValueError('Tier must be 0-3')
        return v
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Key cannot be empty')
        if len(v) > 100:
            raise ValueError('Key too long (max 100 chars)')
        return v.strip()


class MemoryUpdate(BaseModel):
    key: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    tier: Optional[int] = None


class MemoryResponse(BaseModel):
    memory: MCPMemory
    mcp_context: str  # Current context string for this memory


# ============================================================================
# Personality Models
# ============================================================================

class PersonalityUpdate(BaseModel):
    name: Optional[str] = None
    values: Optional[List[str]] = None
    communication_style: Optional[str] = None
    expertise_domains: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    tone: Optional[str] = None
    specializations: Optional[List[str]] = None


# ============================================================================
# Key Management Models
# ============================================================================

class KeyCreate(BaseModel):
    name: str
    provider: str
    value: str
    key_type: str = "provider_api"
    expires_in_days: Optional[int] = None
    labels: Optional[Dict[str, str]] = None
    description: str = ""
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid = [p.value for p in KeyProvider]
        if v not in valid:
            raise ValueError(f'Provider must be one of: {", ".join(valid)}')
        return v


class KeyUpdate(BaseModel):
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# Assistant Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ['system', 'user', 'assistant']:
            raise ValueError('Role must be system, user, or assistant')
        return v


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    include_mcp_context: bool = True


class ChatResponse(BaseModel):
    message: ChatMessage
    mcp_context_used: bool
    memory_suggestions: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Memory Routes
# ============================================================================

@memory_router.get("/memories")
async def get_memories(
    request: Request,
    tier: Optional[int] = None,
    query: Optional[str] = None
):
    """Get all memories, optionally filtered by tier or search query."""
    mcp_storage = request.app.state.mcp_storage
    
    if query:
        memories = mcp_storage.search_memories(query, tier)
    else:
        memories = mcp_storage.get_all_memories(tier)
    
    return {
        "memories": [m.to_dict() for m in memories],
        "count": len(memories),
        "by_tier": mcp_storage.get_stats().to_dict()["by_tier"] if not query else None
    }


@memory_router.get("/memories/{memory_id}")
async def get_memory(memory_id: str, request: Request):
    """Get a specific memory and record access."""
    mcp_storage = request.app.state.mcp_storage
    memory = mcp_storage.access_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Generate context for this memory
    context = generate_mcp_context([memory])
    
    return {
        "memory": memory.to_dict(),
        "mcp_context": context
    }


@memory_router.post("/memories")
async def create_memory(data: MemoryCreate, request: Request):
    """Create a new memory entry."""
    mcp_storage = request.app.state.mcp_storage
    
    memory = mcp_storage.create_memory(
        key=data.key,
        content=data.content,
        tier=data.tier,
        tags=data.tags,
        source=data.source
    )
    
    return {
        "memory": memory.to_dict(),
        "created": True
    }


@memory_router.put("/memories/{memory_id}")
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    request: Request
):
    """Update an existing memory."""
    mcp_storage = request.app.state.mcp_storage
    
    # Validate tier if provided
    if data.tier is not None and (data.tier < 0 or data.tier > 3):
        raise HTTPException(status_code=400, detail="Invalid tier (must be 0-3)")
    
    memory = mcp_storage.update_memory(
        memory_id,
        key=data.key,
        content=data.content,
        tags=data.tags,
        tier=data.tier
    )
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"memory": memory.to_dict()}


@memory_router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, request: Request):
    """Delete a memory."""
    mcp_storage = request.app.state.mcp_storage
    success = mcp_storage.delete_memory(memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"deleted": True}


@memory_router.post("/memories/{memory_id}/access")
async def access_memory(memory_id: str, request: Request):
    """Record memory access and trigger elevation checks."""
    mcp_storage = request.app.state.mcp_storage
    memory = mcp_storage.access_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "memory": memory.to_dict(),
        "elevated": memory.elevation_score > 0.8
    }


@memory_router.post("/memories/search")
async def search_memories(
    query: str,
    tier: Optional[int] = None,
    request: Request = None
):
    """Search memories by key, content, or tags."""
    mcp_storage = request.app.state.mcp_storage
    results = mcp_storage.search_memories(query, tier)
    
    return {
        "results": [m.to_dict() for m in results],
        "count": len(results),
        "query": query
    }


# ============================================================================
# MCP Context Routes
# ============================================================================

@mcp_router.get("/context")
async def get_mcp_context(
    request: Request,
    tiers: Optional[str] = "0,1,2",  # Comma-separated tier list
    include_archive: bool = False
):
    """
    Get the full MCP context string for injection into prompts.
    Combines personality + memory tiers.
    """
    mcp_storage = request.app.state.mcp_storage
    
    # Parse tiers
    if include_archive:
        tier_list = [0, 1, 2, 3]
    else:
        tier_list = [int(t) for t in tiers.split(",")]
    
    # Get personality and memories
    personality = mcp_storage.get_personality()
    memories = mcp_storage.get_memories_for_context(tier_list)
    
    # Generate context
    context = generate_mcp_context(memories)
    system_prompt = generate_system_prompt(personality, memories, include_archive)
    
    return {
        "personality": personality.to_dict(),
        "personality_mcp": personality.to_mcp_context(),
        "memory_context": context,
        "system_prompt": system_prompt,
        "tiers_included": tier_list,
        "memory_count": len(memories)
    }


@mcp_router.get("/stats")
async def get_mcp_stats(request: Request):
    """Get MCP system statistics."""
    mcp_storage = request.app.state.mcp_storage
    return mcp_storage.get_stats().to_dict()


@mcp_router.post("/maintenance")
async def run_maintenance(request: Request):
    """Run auto-elevation and archiving maintenance."""
    mcp_storage = request.app.state.mcp_storage
    changes = mcp_storage.run_maintenance()
    return {"maintenance": "completed", "changes": changes}


@mcp_router.get("/session")
async def get_session(request: Request):
    """Get current MCP session info."""
    mcp_storage = request.app.state.mcp_storage
    session = mcp_storage.get_active_session()
    
    if not session:
        session = mcp_storage.create_session()
    
    return session.to_dict()


@mcp_router.post("/session")
async def update_session(
    data: Dict[str, Any],
    request: Request
):
    """Update current session."""
    mcp_storage = request.app.state.mcp_storage
    session = mcp_storage.get_active_session()
    
    if not session:
        session = mcp_storage.create_session()
    
    if "current_project" in data:
        session.current_project = data["current_project"]
    if "active_goals" in data:
        session.active_goals = data["active_goals"]
    if "context_window_summary" in data:
        session.context_window_summary = data["context_window_summary"]
    if "recent_interactions" in data:
        session.recent_interactions.extend(data["recent_interactions"])
    
    mcp_storage.update_session(session)
    return session.to_dict()


# ============================================================================
# Personality Routes
# ============================================================================

@personality_router.get("/")
async def get_personality(request: Request):
    """Get current personality profile."""
    mcp_storage = request.app.state.mcp_storage
    personality = mcp_storage.get_personality()
    return personality.to_dict()


@personality_router.get("/mcp")
async def get_personality_mcp(request: Request):
    """Get personality as MCP context string."""
    mcp_storage = request.app.state.mcp_storage
    personality = mcp_storage.get_personality()
    return {"mcp_context": personality.to_mcp_context()}


@personality_router.put("/")
async def update_personality(data: PersonalityUpdate, request: Request):
    """Update personality profile."""
    mcp_storage = request.app.state.mcp_storage
    personality = mcp_storage.get_personality()
    
    # Update fields if provided
    if data.name is not None:
        personality.name = data.name
    if data.values is not None:
        personality.values = data.values
    if data.communication_style is not None:
        personality.communication_style = data.communication_style
    if data.expertise_domains is not None:
        personality.expertise_domains = data.expertise_domains
    if data.goals is not None:
        personality.goals = data.goals
    if data.constraints is not None:
        personality.constraints = data.constraints
    if data.tone is not None:
        personality.tone = data.tone
    if data.specializations is not None:
        personality.specializations = data.specializations
    
    mcp_storage.update_personality(personality)
    return personality.to_dict()


@personality_router.post("/reset")
async def reset_personality(request: Request):
    """Reset personality to default prompt engineer profile."""
    mcp_storage = request.app.state.mcp_storage
    default = PersonalityProfile.default_profile()
    mcp_storage.update_personality(default)
    return {"reset": True, "personality": default.to_dict()}


# ============================================================================
# Key Management Routes
# ============================================================================

@keys_router.get("")
async def list_keys(
    request: Request,
    provider: Optional[str] = None,
    key_type: Optional[str] = None
):
    """List all stored keys (metadata only, no values)."""
    key_manager = request.app.state.key_manager
    keys = key_manager.list_keys(provider, key_type)
    return {
        "keys": [k.to_dict() for k in keys],
        "count": len(keys),
        "stats": key_manager.get_stats()
    }


@keys_router.get("/{key_id}")
async def get_key_metadata(key_id: str, request: Request):
    """Get key metadata."""
    key_manager = request.app.state.key_manager
    metadata = key_manager.get_key_metadata(key_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return metadata.to_dict()


@keys_router.post("")
async def create_key(data: KeyCreate, request: Request):
    """Store a new API key."""
    key_manager = request.app.state.key_manager
    
    metadata = key_manager.store_key(
        name=data.name,
        provider=data.provider,
        key_type=data.key_type,
        value=data.value,
        expires_in_days=data.expires_in_days,
        labels=data.labels,
        description=data.description
    )
    
    return {
        "created": True,
        "key": metadata.to_dict()
    }


@keys_router.put("/{key_id}")
async def update_key(
    key_id: str,
    data: KeyUpdate,
    request: Request
):
    """Update key metadata."""
    key_manager = request.app.state.key_manager
    
    metadata = key_manager.update_key(
        key_id,
        name=data.name,
        labels=data.labels,
        description=data.description,
        is_active=data.is_active
    )
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"updated": True, "key": metadata.to_dict()}


@keys_router.post("/{key_id}/rotate")
async def rotate_key(key_id: str, request: Request):
    """Rotate a key with a new value."""
    key_manager = request.app.state.key_manager
    
    metadata = key_manager.rotate_key(key_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"rotated": True, "key": metadata.to_dict()}


@keys_router.delete("/{key_id}")
async def delete_key(key_id: str, request: Request):
    """Delete a stored key."""
    key_manager = request.app.state.key_manager
    success = key_manager.delete_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"deleted": True}


@keys_router.get("/provider/{provider}")
async def get_provider_key(provider: str, request: Request):
    """
    Get the active key for a specific provider.
    Useful for direct API access.
    """
    key_manager = request.app.state.key_manager
    value = key_manager.get_provider_key(provider)
    
    if not value:
        raise HTTPException(status_code=404, detail=f"No active key for provider: {provider}")
    
    return {"provider": provider, "key": value}


@keys_router.get("/providers")
async def list_providers(request: Request):
    """List all supported key providers."""
    providers = [
        {"id": p.value, "name": p.name.replace("_", " ").title()}
        for p in KeyProvider
    ]
    return {"providers": providers}


@keys_router.post("/cleanup")
async def cleanup_keys(request: Request):
    """Remove all expired keys."""
    key_manager = request.app.state.key_manager
    count = key_manager.cleanup_expired()
    return {"cleaned": count, "expired_removed": count}


# ============================================================================
# Prompt Engineer Assistant Routes
# ============================================================================

@assistant_router.post("/chat")
async def chat_with_assistant(data: ChatRequest, request: Request):
    """
    Chat with the prompt engineer assistant.
    Automatically enriches with MCP context.
    Falls back to local Ollama if no model configured.
    """
    mcp_storage = request.app.state.mcp_storage
    model_manager = request.app.state.model_manager
    
    # Get MCP context if requested
    mcp_context_used = False
    memory_suggestions = None
    
    if data.include_mcp_context:
        personality = mcp_storage.get_personality()
        memories = mcp_storage.get_memories_for_context([0, 1, 2])
        
        # Build system message with MCP context
        system_content = generate_system_prompt(personality, memories)
        data.messages.insert(0, ChatMessage(role="system", content=system_content))
        mcp_context_used = True
    
    # Try configured model first, then Ollama fallback
    runner = model_manager.get_runner(data.model)
    if not runner:
        # Try Ollama as fallback
        from app.model_runner import ModelConfig
        config = ModelConfig(
            name="llama3.2",
            path="",
            backend="ollama",
            api_base="http://localhost:11434/v1"
        )
        model_manager.configure(config)
        runner = model_manager.get_runner("llama3.2")
    
    if not runner or not runner.is_available():
        return {
            "message": {"role": "assistant", "content": "No model available. Configure a model or start Ollama."},
            "mcp_context_used": mcp_context_used,
            "memory_suggestions": None
        }
    
    # Convert to internal message format
    from app.model_runner import ChatMessage as ModelChatMessage
    model_messages = [
        ModelChatMessage(role=m.role, content=m.content)
        for m in data.messages
    ]
    
    # Generate response
    response_text = model_manager.generate(
        model_messages,
        model_name=data.model,
        max_tokens=data.max_tokens,
        temperature=data.temperature
    )
    
    response_message = ChatMessage(role="assistant", content=response_text)
    
    # Suggest memories based on conversation
    if data.include_mcp_context:
        keywords = set(response_text.lower().split()) | set(
            sum([m.content.lower().split() for m in data.messages if m.role == "user"], [])
        )
        relevant_memories = []
        for mem in memories[:5]:
            if any(kw in mem.content.lower() for kw in list(keywords)[:10]):
                relevant_memories.append({
                    "id": mem.id,
                    "key": mem.key,
                    "tier": mem.tier,
                    "relevance": "high" if mem.tier == 0 else "medium"
                })
        memory_suggestions = relevant_memories
    
    return {
        "message": response_message.dict(),
        "mcp_context_used": mcp_context_used,
        "memory_suggestions": memory_suggestions
    }


@assistant_router.get("/models")
async def list_models(request: Request):
    """List available models for the assistant."""
    model_manager = request.app.state.model_manager
    
    return {
        "current_config": model_manager.get_current_config().to_dict() if model_manager.get_current_config() else None,
        "available_backends": model_manager.get_available_backends()
    }


@assistant_router.post("/models/configure")
async def configure_model(
    name: str,
    path: str,
    backend: str,
    request: Request,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    context_length: int = 2048
):
    """Configure the model to use for the assistant."""
    model_manager = request.app.state.model_manager
    
    from app.model_runner import ModelConfig
    config = ModelConfig(
        name=name,
        path=path,
        backend=backend,
        context_length=context_length,
        api_base=api_base,
        api_key=api_key
    )
    
    success = model_manager.configure(config)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to configure model")
    
    return {"configured": True, "model": config.name, "backend": backend}


@assistant_router.get("/health")
async def assistant_health(request: Request):
    """Check if the assistant is ready."""
    model_manager = request.app.state.model_manager
    
    current = model_manager.get_current_config()
    if not current:
        return {
            "ready": False,
            "message": "No model configured",
            "available_backends": model_manager.get_available_backends()
        }
    
    runner = model_manager.get_runner()
    if not runner or not runner.is_available():
        return {
            "ready": False,
            "message": "Model not available",
            "model": current.name,
            "backend": current.backend
        }
    
    return {
        "ready": True,
        "model": current.name,
        "backend": current.backend,
        "context_length": current.context_length
    }
