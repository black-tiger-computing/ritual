"""
RITUAL MCP Storage Manager
Handles persistence for the 4-tier MCP memory system
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from app.mcp import (
    MCPMemory, MCPSession, MCPSystemStats, MCPTier,
    PersonalityProfile, TIER_NAMES, MCPElevationEngine
)

logger = logging.getLogger(__name__)


class MCPStorage:
    """
    Storage manager for MCP tiered memory system.
    Extends the base StorageManager with MCP-specific operations.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.mcp_dir = data_dir / "mcp"
        self.memories_file = self.mcp_dir / "memories.json"
        self.sessions_file = self.mcp_dir / "sessions.json"
        self.personality_file = self.mcp_dir / "personality.json"
        self.stats_cache_file = self.mcp_dir / "stats_cache.json"
        
        self._memories: List[MCPMemory] = []
        self._sessions: List[MCPSession] = []
        self._personality: Optional[PersonalityProfile] = None
        self._stats_cache: Optional[MCPSystemStats] = None
        
        self._init_storage()
        self._load_all()
    
    def _init_storage(self) -> None:
        """Initialize MCP storage directories."""
        self.mcp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MCP storage initialized at {self.mcp_dir}")
    
    def _load_all(self) -> None:
        """Load all MCP data from disk."""
        self._load_memories()
        self._load_sessions()
        self._load_personality()
        self._invalidate_stats_cache()
    
    def _load_memories(self) -> None:
        """Load memories from disk."""
        if self.memories_file.exists():
            try:
                with open(self.memories_file, "r") as f:
                    data = json.load(f)
                    self._memories = [MCPMemory.from_dict(m) for m in data]
                logger.info(f"Loaded {len(self._memories)} memories")
            except Exception as e:
                logger.error(f"Error loading memories: {e}")
                self._memories = []
        else:
            self._memories = []
            self._seed_default_memories()
    
    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r") as f:
                    data = json.load(f)
                    self._sessions = [MCPSession(**s) for s in data]
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
                self._sessions = []
        else:
            self._sessions = []
    
    def _load_personality(self) -> None:
        """Load personality profile from disk."""
        if self.personality_file.exists():
            try:
                with open(self.personality_file, "r") as f:
                    data = json.load(f)
                    self._personality = PersonalityProfile.from_dict(data)
                logger.info("Loaded personality profile")
            except Exception as e:
                logger.error(f"Error loading personality: {e}")
                self._personality = PersonalityProfile.default_profile()
        else:
            self._personality = PersonalityProfile.default_profile()
            self._save_personality()
    
    def _seed_default_memories(self) -> None:
        """Seed default memories for new installations."""
        defaults = [
            MCPMemory(
                id="default-1", tier=1, key="preferred_model",
                content="User prefers efficient, concise responses",
                tags=["preference", "response_style"],
                source="system"
            ),
            MCPMemory(
                id="default-2", tier=1, key="current_project",
                content="Setting up RITUAL MCP system",
                tags=["project", "active"],
                source="system"
            ),
            MCPMemory(
                id="default-3", tier=2, key="prompt_patterns",
                content="Chain-of-thought works well for reasoning tasks. Few-shot for classification.",
                tags=["pattern", "effective"],
                source="system"
            ),
        ]
        self._memories.extend(defaults)
        self._save_memories()
    
    def _save_memories(self) -> None:
        """Save memories to disk."""
        try:
            with open(self.memories_file, "w") as f:
                json.dump([m.to_dict() for m in self._memories], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
    
    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        try:
            with open(self.sessions_file, "w") as f:
                json.dump([s.to_dict() for s in self._sessions], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _save_personality(self) -> None:
        """Save personality profile to disk."""
        if self._personality:
            try:
                with open(self.personality_file, "w") as f:
                    json.dump(self._personality.to_dict(), f, indent=2)
            except Exception as e:
                logger.error(f"Error saving personality: {e}")
    
    def _invalidate_stats_cache(self) -> None:
        """Invalidate stats cache on data changes."""
        self._stats_cache = None
    
    # Memory CRUD Operations
    
    def get_all_memories(self, tier: Optional[int] = None) -> List[MCPMemory]:
        """Get all memories, optionally filtered by tier."""
        if tier is not None:
            return [m for m in self._memories if m.tier == tier]
        return self._memories.copy()
    
    def get_memory(self, memory_id: str) -> Optional[MCPMemory]:
        """Get a specific memory by ID."""
        for memory in self._memories:
            if memory.id == memory_id:
                return memory
        return None
    
    def create_memory(
        self,
        key: str,
        content: str,
        tier: int = 1,
        tags: Optional[List[str]] = None,
        source: str = "user"
    ) -> MCPMemory:
        """Create a new memory entry."""
        import uuid
        memory = MCPMemory(
            id=str(uuid.uuid4())[:8],
            tier=tier,
            key=key,
            content=content,
            tags=tags or [],
            source=source,
            elevation_score=MCPElevationEngine.calculate_elevation_score(MCPMemory(
                id="", tier=tier, key=key, content=content, tags=tags or []
            ))
        )
        self._memories.append(memory)
        self._save_memories()
        self._invalidate_stats_cache()
        logger.info(f"Created memory: {key} in tier {tier}")
        return memory
    
    def update_memory(
        self,
        memory_id: str,
        key: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tier: Optional[int] = None
    ) -> Optional[MCPMemory]:
        """Update an existing memory."""
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        if key is not None:
            memory.key = key
        if content is not None:
            memory.content = content
        if tags is not None:
            memory.tags = tags
        if tier is not None and 0 <= tier <= 3:
            memory.tier = tier
        
        memory.updated_at = datetime.utcnow().isoformat() + "Z"
        memory.elevation_score = MCPElevationEngine.calculate_elevation_score(memory)
        
        self._save_memories()
        self._invalidate_stats_cache()
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        original_count = len(self._memories)
        self._memories = [m for m in self._memories if m.id != memory_id]
        
        if len(self._memories) < original_count:
            self._save_memories()
            self._invalidate_stats_cache()
            return True
        return False
    
    def access_memory(self, memory_id: str) -> Optional[MCPMemory]:
        """Record a memory access and potentially trigger elevation."""
        memory = self.get_memory(memory_id)
        if not memory:
            return None
        
        memory.access_count += 1
        memory.last_accessed = datetime.utcnow().isoformat() + "Z"
        memory.elevation_score = MCPElevationEngine.calculate_elevation_score(memory)
        
        # Check for auto-elevation
        if MCPElevationEngine.should_elevate(memory):
            new_tier = MCPElevationEngine.get_target_tier(memory)
            if new_tier > memory.tier:
                logger.info(f"Auto-elevating memory {memory_id} from tier {memory.tier} to {new_tier}")
                memory.tier = new_tier
        
        self._save_memories()
        self._invalidate_stats_cache()
        return memory
    
    def search_memories(self, query: str, tier: Optional[int] = None) -> List[MCPMemory]:
        """Search memories by key or content."""
        results = []
        query_lower = query.lower()
        
        for memory in self._memories:
            if tier is not None and memory.tier != tier:
                continue
            
            if (query_lower in memory.key.lower() or 
                query_lower in memory.content.lower() or
                any(query_lower in tag.lower() for tag in memory.tags)):
                results.append(memory)
        
        return sorted(results, key=lambda m: -m.elevation_score)
    
    def get_memories_for_context(self, include_tiers: Optional[List[int]] = None) -> List[MCPMemory]:
        """Get memories for building context, ordered by tier and relevance."""
        if include_tiers is None:
            include_tiers = [0, 1, 2]  # Default: personality, context, frequent
        
        memories = [m for m in self._memories if m.tier in include_tiers]
        return sorted(memories, key=lambda m: (m.tier, -m.elevation_score))
    
    # Personality Operations
    
    def get_personality(self) -> PersonalityProfile:
        """Get the current personality profile."""
        if self._personality is None:
            self._personality = PersonalityProfile.default_profile()
            self._save_personality()
        return self._personality
    
    def update_personality(self, profile: PersonalityProfile) -> PersonalityProfile:
        """Update the personality profile."""
        profile.updated_at = datetime.utcnow().isoformat() + "Z"
        self._personality = profile
        self._save_personality()
        return profile
    
    # Session Operations
    
    def get_active_session(self) -> Optional[MCPSession]:
        """Get the most recent active session."""
        if self._sessions:
            return self._sessions[-1]
        return None
    
    def create_session(self) -> MCPSession:
        """Create a new session."""
        session = MCPSession.new_session()
        self._sessions.append(session)
        self._save_sessions()
        return session
    
    def update_session(self, session: MCPSession) -> MCPSession:
        """Update an existing session."""
        session_dict = {s.id: i for i, s in enumerate(self._sessions)}
        if session.id in session_dict:
            self._sessions[session_dict[session.id]] = session
            self._save_sessions()
        return session
    
    # Statistics
    
    def get_stats(self) -> MCPSystemStats:
        """Get MCP system statistics."""
        if self._stats_cache:
            return self._stats_cache
        
        stats = MCPSystemStats()
        stats.total_memories = len(self._memories)
        stats.by_tier = {i: len([m for m in self._memories if m.tier == i]) for i in range(4)}
        
        # Most accessed
        sorted_by_access = sorted(self._memories, key=lambda m: -m.access_count)
        stats.most_accessed = [m.to_dict() for m in sorted_by_access[:10]]
        
        # Recent additions
        sorted_by_created = sorted(self._memories, key=lambda m: m.created_at, reverse=True)
        stats.recent_additions = [m.to_dict() for m in sorted_by_created[:10]]
        
        self._stats_cache = stats
        return stats
    
    # Auto-maintenance
    
    def run_maintenance(self) -> Dict[str, int]:
        """Run auto-elevation and archiving. Returns counts of changes."""
        changes = {"elevated": 0, "archived": 0}
        
        for memory in self._memories:
            if memory.tier == 3:
                continue  # Already archived
            
            # Check for elevation
            if MCPElevationEngine.should_elevate(memory):
                new_tier = MCPElevationEngine.get_target_tier(memory)
                if new_tier > memory.tier:
                    memory.tier = new_tier
                    changes["elevated"] += 1
            
            # Check for archiving
            if MCPElevationEngine.should_archive(memory):
                memory.tier = 3
                changes["archived"] += 1
        
        if changes["elevated"] > 0 or changes["archived"] > 0:
            self._save_memories()
            self._invalidate_stats_cache()
            logger.info(f"Maintenance: elevated={changes['elevated']}, archived={changes['archived']}")
        
        return changes
