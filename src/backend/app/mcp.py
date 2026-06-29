"""
RITUAL MCP - Model Context Protocol
4-Tier Memory System with increasing specificity

Tier Architecture:
- Tier 0 (Personality): Core identity, values, communication style, goals
- Tier 1 (Context): Current session/project context, active goals
- Tier 2 (Frequent): Frequently used patterns, recent learnings
- Tier 3 (Archive): Historical, dormant, highly specific memories
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import json


class MCPTier(Enum):
    """The 4 tiers of MCP memory, from broad to specific."""
    PERSONALITY = 0  # Core identity, values, communication style
    CONTEXT = 1      # Current session, project, active goals
    FREQUENT = 2     # Frequently used patterns, recent learnings
    ARCHIVE = 3      # Historical, dormant, highly specific


TIER_NAMES = {0: "personality", 1: "context", 2: "frequent", 3: "archive"}
TIER_DISPLAY = {
    0: "🜃 Personality",
    1: "☉ Context",
    2: "☽ Frequent",
    3: "☄ Archive"
}


@dataclass
class MCPMemory:
    """A single memory entry in the MCP system."""
    id: str
    tier: int
    key: str
    content: str
    tags: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    confidence: float = 1.0  # 0.0 - 1.0, how confident we are this is accurate
    elevation_score: float = 0.0  # Used for auto-elevation decisions
    source: str = "user"  # user, assistant, system, auto
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier,
            "tier_name": TIER_NAMES.get(self.tier, "unknown"),
            "key": self.key,
            "content": self.content,
            "tags": self.tags,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confidence": self.confidence,
            "elevation_score": self.elevation_score,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMemory":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            tier=data.get("tier", 1),
            key=data.get("key", ""),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat() + "Z"),
            confidence=data.get("confidence", 1.0),
            elevation_score=data.get("elevation_score", 0.0),
            source=data.get("source", "user")
        )


@dataclass
class PersonalityProfile:
    """Tier 0: Core identity and communication style."""
    id: str
    name: str
    values: List[str]  # Core values
    communication_style: str  # formal, casual, technical, etc.
    expertise_domains: List[str]
    goals: List[str]  # Short and long term goals
    constraints: List[str]  # What to avoid, boundaries
    tone: str  # Overall tone description
    specializations: List[str]  # Areas of deep knowledge
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "values": self.values,
            "communication_style": self.communication_style,
            "expertise_domains": self.expertise_domains,
            "goals": self.goals,
            "constraints": self.constraints,
            "tone": self.tone,
            "specializations": self.specializations,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_mcp_context(self) -> str:
        """Generate the MCP context string for this personality."""
        return f"""You are {self.name}.
Communication style: {self.communication_style}
Tone: {self.tone}
Core values: {', '.join(self.values)}
Areas of expertise: {', '.join(self.expertise_domains)}
Specializations: {', '.join(self.specializations)}
Goals: {'; '.join(self.goals)}
Constraints: {'; '.join(self.constraints)}"""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalityProfile":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Assistant"),
            values=data.get("values", []),
            communication_style=data.get("communication_style", "balanced"),
            expertise_domains=data.get("expertise_domains", []),
            goals=data.get("goals", []),
            constraints=data.get("constraints", []),
            tone=data.get("tone", "helpful"),
            specializations=data.get("specializations", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat() + "Z")
        )
    
    @classmethod
    def default_profile(cls) -> "PersonalityProfile":
        """Create a default prompt engineer personality."""
        return cls(
            id="default",
            name="Ritual Prompt Engineer",
            values=["clarity", "efficiency", "precision", "creativity"],
            communication_style="technical but accessible",
            expertise_domains=["prompt engineering", "LLM optimization", "context management"],
            goals=[
                "Help users craft optimal prompts",
                "Minimize token usage while maximizing relevance",
                "Adapt to user's communication style",
                "Provide actionable suggestions"
            ],
            constraints=[
                "Keep prompts concise",
                "Avoid hallucinated information",
                "Respect user's privacy and data"
            ],
            tone="Professional, knowledgeable, helpful",
            specializations=["few-shot learning", "chain-of-thought", "role-playing", "system prompts"]
        )


@dataclass 
class MCPSession:
    """Tracks the current session context."""
    id: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    current_project: Optional[str] = None
    active_goals: List[str] = field(default_factory=list)
    recent_interactions: List[Dict[str, str]] = field(default_factory=list)
    context_window_summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "started_at": self.started_at,
            "current_project": self.current_project,
            "active_goals": self.active_goals,
            "recent_interactions": self.recent_interactions[-10:],  # Last 10
            "context_window_summary": self.context_window_summary
        }
    
    @classmethod
    def new_session(cls) -> "MCPSession":
        return cls(id=str(uuid.uuid4())[:8])


@dataclass
class MCPSystemStats:
    """Statistics about the MCP system."""
    total_memories: int = 0
    by_tier: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0, 3: 0})
    auto_elevations: int = 0
    auto_archives: int = 0
    most_accessed: List[Dict[str, Any]] = field(default_factory=list)
    recent_additions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_memories": self.total_memories,
            "by_tier": self.by_tier,
            "auto_elevations": self.auto_elevations,
            "auto_archives": self.auto_archives,
            "most_accessed": self.most_accessed[:10],
            "recent_additions": self.recent_additions[:10]
        }


class MCPElevationEngine:
    """
    Determines when memories should be elevated or archived.
    
    Elevation Rules:
    - Memory accessed 5+ times → consider elevation to more specific tier
    - High elevation_score (>0.8) → auto-elevate
    - Low access_count (<2) + old (>30 days) → consider archive
    
    Tier Flow:
    - New entries → Tier 1 (Context)
    - Frequent access → Elevate to more specific tier
    - No access for 30+ days → Archive
    """
    
    ELEVATION_THRESHOLD = 0.8
    ACCESS_COUNT_FOR_ELEVATION = 5
    DAYS_WITHOUT_ACCESS_FOR_ARCHIVE = 30
    
    @staticmethod
    def calculate_elevation_score(memory: MCPMemory) -> float:
        """Calculate if a memory should be elevated."""
        now = datetime.utcnow()
        created = datetime.fromisoformat(memory.created_at.replace("Z", "+00:00"))
        
        # Base score from access count (logarithmic scaling)
        access_score = min(memory.access_count / 10, 1.0) * 0.4
        
        # Recency bonus
        if memory.last_accessed:
            last = datetime.fromisoformat(memory.last_accessed.replace("Z", "+00:00"))
            days_since = (now - last.replace(tzinfo=None)).days
            recency_score = max(0, 1 - (days_since / 30)) * 0.3
        else:
            recency_score = 0
        
        # Confidence bonus
        confidence_score = memory.confidence * 0.3
        
        return min(access_score + recency_score + confidence_score, 1.0)
    
    @staticmethod
    def should_elevate(memory: MCPMemory) -> bool:
        """Determine if memory should move to a more specific tier."""
        score = MCPElevationEngine.calculate_elevation_score(memory)
        return score >= MCPElevationEngine.ELEVATION_THRESHOLD
    
    @staticmethod
    def should_archive(memory: MCPMemory) -> bool:
        """Determine if memory should be archived."""
        if memory.access_count > 0:
            return False  # Never archive accessed memories
        
        if memory.last_accessed:
            last = datetime.fromisoformat(memory.last_accessed.replace("Z", "+00:00"))
            days_since = (datetime.utcnow() - last.replace(tzinfo=None)).days
            return days_since > MCPElevationEngine.DAYS_WITHOUT_ACCESS_FOR_ARCHIVE
        
        return False
    
    @staticmethod
    def get_target_tier(memory: MCPMemory) -> int:
        """
        Determine the target tier based on memory characteristics.
        Returns the appropriate tier (0-3).
        """
        # Check tags for tier hints
        tier_keywords = {
            0: ["identity", "core", "values", "personality", "self"],
            1: ["current", "active", "session", "project", "goal"],
            2: ["pattern", "learned", "frequent", "useful", "template"],
            3: ["old", "historical", "dormant", "specific", "reference"]
        }
        
        for tag in memory.tags:
            for tier, keywords in tier_keywords.items():
                if any(kw in tag.lower() for kw in keywords):
                    return tier
        
        # Default: based on specificity (content length is a proxy)
        content_length = len(memory.content)
        if content_length < 100:
            return 1  # Short → Context
        elif content_length < 500:
            return 2  # Medium → Frequent
        else:
            return 3  # Long → Archive


def generate_mcp_context(memories: List[MCPMemory], max_tokens: int = 4000) -> str:
    """
    Generate a context string from memories, respecting token limits.
    Priority: Personality → Context → Frequent → Archive
    """
    context_parts = []
    current_tokens = 0
    
    # Sort by tier (0 first) then by elevation_score
    sorted_memories = sorted(memories, key=lambda m: (m.tier, -m.elevation_score))
    
    for memory in sorted_memories:
        memory_text = f"[{TIER_NAMES[memory.tier].upper()}] {memory.key}: {memory.content}"
        memory_tokens = len(memory_text.split()) * 1.3  # Rough token estimate
        
        if current_tokens + memory_tokens > max_tokens:
            break
        
        context_parts.append(memory_text)
        current_tokens += memory_tokens
    
    return "\n\n".join(context_parts)


def generate_system_prompt(personality: PersonalityProfile, memories: List[MCPMemory], 
                           include_archive: bool = False) -> str:
    """Generate a complete system prompt from MCP components."""
    sections = [
        "## Identity",
        personality.to_mcp_context(),
        "",
        "## Active Memory",
        generate_mcp_context(memories),
    ]
    
    if include_archive:
        archive_memories = [m for m in memories if m.tier == 3]
        if archive_memories:
            sections.extend([
                "",
                "## Archived Reference",
                generate_mcp_context(archive_memories)
            ])
    
    return "\n".join(sections)
