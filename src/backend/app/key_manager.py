"""
RITUAL Key Management System
Secure storage and retrieval of API keys for various LLM providers
"""

import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class KeyType(Enum):
    """Types of keys that can be managed."""
    PROVIDER_API = "provider_api"      # LM Studio, MSTY, OpenAI, Anthropic, etc.
    MODEL_ACCESS = "model_access"      # Model-specific access keys
    USER_SESSION = "user_session"       # User session tokens
    WEBHOOK = "webhook"                # Webhook secrets
    ENCRYPTION = "encryption"          # Encryption keys


class KeyProvider(Enum):
    """Supported key providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    AI21 = "ai21"
    TOGETHER = "together"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
    GROQ = "groq"
    PERPLEXITY = "perplexity"
    OLLAMA_CLOUD = "ollama_cloud"
    LOCAL = "local"  # For local models (no key needed)
    LM_STUDIO = "lm_studio"
    MSTY = "msty"


class KeyMetadata:
    """Metadata for a stored key."""
    
    def __init__(
        self,
        key_id: str,
        name: str,
        provider: str,
        key_type: str,
        created_at: str,
        expires_at: Optional[str] = None,
        last_used: Optional[str] = None,
        usage_count: int = 0,
        is_active: bool = True,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ):
        self.key_id = key_id
        self.name = name
        self.provider = provider
        self.key_type = key_type
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_used = last_used
        self.usage_count = usage_count
        self.is_active = is_active
        self.labels = labels or {}
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "name": self.name,
            "provider": self.provider,
            "key_type": self.key_type,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "labels": self.labels,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyMetadata":
        return cls(**data)
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at.replace("Z", "+00:00")) < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired


class KeyManager:
    """
    Secure key management system with encryption and access controls.
    """
    
    # Master key derivation
    MASTER_KEY_ENV = "RITUAL_MASTER_KEY"
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.keys_dir = data_dir / "keys"
        self.metadata_file = self.keys_dir / "metadata.json"
        self._cipher: Optional[Fernet] = None
        self._keys: Dict[str, KeyMetadata] = {}
        
        self._init_storage()
        self._setup_encryption()
        self._load_keys()
    
    def _init_storage(self) -> None:
        """Initialize key storage directory."""
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions
        try:
            os.chmod(self.keys_dir, 0o700)
        except Exception:
            pass
        
        logger.info(f"Key storage initialized at {self.keys_dir}")
    
    def _setup_encryption(self) -> None:
        """Setup Fernet encryption for keys."""
        key_file = self.keys_dir / ".master.key"
        
        # Check for master key in environment
        master_key = os.environ.get(self.MASTER_KEY_ENV)
        
        if master_key:
            # Use provided master key (must be valid Fernet key)
            try:
                self._cipher = Fernet(master_key.encode())
            except Exception:
                logger.warning("Invalid master key format, generating new key")
                master_key = None
        
        if not master_key:
            if key_file.exists():
                with open(key_file, "rb") as f:
                    self._cipher = Fernet(f.read())
            else:
                # Generate new master key
                master_key = Fernet.generate_key()
                key_file.write_bytes(master_key)
                os.chmod(key_file, 0o600)
                self._cipher = Fernet(master_key)
                logger.info("Generated new master encryption key")
    
    def _load_keys(self) -> None:
        """Load key metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    self._keys = {k: KeyMetadata.from_dict(v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._keys)} key metadata entries")
            except Exception as e:
                logger.error(f"Error loading key metadata: {e}")
                self._keys = {}
        else:
            self._keys = {}
    
    def _save_keys(self) -> None:
        """Save key metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump({k: v.to_dict() for k, v in self._keys.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving key metadata: {e}")
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        if not self._cipher:
            return value
        return self._cipher.encrypt(value.encode()).decode()
    def _decrypt_value(self, encrypted: str) -> str:
        """Decrypt a sensitive value."""
        if not self._cipher:
            return encrypted
        return self._cipher.decrypt(encrypted.encode()).decode()
    
    def _get_key_file(self, key_id: str) -> Path:
        """Get the file path for a key's encrypted value."""
        return self.keys_dir / f"{key_id}.key"
    
    # Key Operations
    
    def store_key(
        self,
        name: str,
        provider: str,
        key_type: str,
        value: str,
        expires_in_days: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> KeyMetadata:
        """
        Store a new key securely.
        
        Args:
            name: Human-readable name for the key
            provider: The provider (openai, anthropic, etc.)
            key_type: Type of key (provider_api, model_access, etc.)
            value: The actual key value to store
            expires_in_days: Optional expiration in days
            labels: Optional key-value labels
            description: Optional description
        
        Returns:
            KeyMetadata for the stored key
        """
        key_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow()
        
        metadata = KeyMetadata(
            key_id=key_id,
            name=name,
            provider=provider,
            key_type=key_type,
            created_at=now.isoformat() + "Z",
            expires_at=(now + timedelta(days=expires_in_days)).isoformat() + "Z" if expires_in_days else None,
            labels=labels or {},
            description=description
        )
        
        # Encrypt and store the key value
        encrypted_value = self._encrypt_value(value)
        key_file = self._get_key_file(key_id)
        key_file.write_text(encrypted_value)
        os.chmod(key_file, 0o600)
        
        # Store metadata
        self._keys[key_id] = metadata
        self._save_keys()
        
        logger.info(f"Stored key: {name} ({key_id}) for {provider}")
        return metadata
    
    def get_key(self, key_id: str) -> Optional[str]:
        """
        Retrieve a key value by ID.
        Updates last_used timestamp.
        """
        metadata = self._keys.get(key_id)
        if not metadata:
            return None
        
        if not metadata.is_valid:
            logger.warning(f"Attempted to use invalid/expired key: {key_id}")
            return None
        
        key_file = self._get_key_file(key_id)
        if not key_file.exists():
            logger.error(f"Key file missing for: {key_id}")
            return None
        
        # Update usage stats
        metadata.last_used = datetime.utcnow().isoformat() + "Z"
        metadata.usage_count += 1
        self._save_keys()
        
        # Decrypt and return
        encrypted = key_file.read_text()
        return self._decrypt_value(encrypted)
    
    def get_key_metadata(self, key_id: str) -> Optional[KeyMetadata]:
        """Get key metadata without retrieving the value."""
        return self._keys.get(key_id)
    
    def list_keys(
        self,
        provider: Optional[str] = None,
        key_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[KeyMetadata]:
        """
        List keys with optional filters.
        Does not return actual key values.
        """
        results = list(self._keys.values())
        
        if provider:
            results = [k for k in results if k.provider == provider]
        if key_type:
            results = [k for k in results if k.key_type == key_type]
        if not include_inactive:
            results = [k for k in results if k.is_valid]
        
        return sorted(results, key=lambda k: k.created_at, reverse=True)
    
    def update_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[KeyMetadata]:
        """Update key metadata."""
        metadata = self._keys.get(key_id)
        if not metadata:
            return None
        
        if name is not None:
            metadata.name = name
        if labels is not None:
            metadata.labels = labels
        if description is not None:
            metadata.description = description
        if is_active is not None:
            metadata.is_active = is_active
        
        self._save_keys()
        return metadata
    
    def rotate_key(self, key_id: str, new_value: Optional[str] = None) -> Optional[KeyMetadata]:
        """
        Rotate a key with a new value.
        If new_value is None, generates a secure random key.
        """
        metadata = self._keys.get(key_id)
        if not metadata:
            return None
        
        if new_value is None:
            # Generate a secure random key (suitable for webhooks)
            if metadata.key_type == KeyType.WEBHOOK.value:
                new_value = secrets.token_urlsafe(32)
            else:
                logger.error("Cannot auto-generate API keys")
                return None
        
        # Store new encrypted value
        encrypted = self._encrypt_value(new_value)
        self._get_key_file(key_id).write_text(encrypted)
        
        # Reset usage stats
        metadata.last_used = None
        metadata.usage_count = 0
        self._save_keys()
        
        logger.info(f"Rotated key: {key_id}")
        return metadata
    
    def delete_key(self, key_id: str) -> bool:
        """Delete a key and its encrypted value."""
        if key_id not in self._keys:
            return False
        
        # Remove encrypted file
        key_file = self._get_key_file(key_id)
        if key_file.exists():
            key_file.unlink()
        
        # Remove metadata
        del self._keys[key_id]
        self._save_keys()
        
        logger.info(f"Deleted key: {key_id}")
        return True
    
    def get_provider_key(self, provider: str) -> Optional[str]:
        """
        Get the active key for a specific provider.
        Useful for quick lookups.
        """
        keys = self.list_keys(provider=provider, include_inactive=False)
        if keys:
            return self.get_key(keys[0].key_id)
        return None
    
    # Utility Methods
    
    def get_stats(self) -> Dict[str, Any]:
        """Get key management statistics."""
        total = len(self._keys)
        active = len([k for k in self._keys.values() if k.is_valid])
        expired = len([k for k in self._keys.values() if k.is_expired])
        inactive = len([k for k in self._keys.values() if not k.is_active])
        
        by_provider = {}
        for key in self._keys.values():
            by_provider[key.provider] = by_provider.get(key.provider, 0) + 1
        
        return {
            "total": total,
            "active": active,
            "expired": expired,
            "inactive": inactive,
            "by_provider": by_provider
        }
    
    def cleanup_expired(self) -> int:
        """Remove expired keys and return count of removed keys."""
        expired_ids = [
            key_id for key_id, meta in self._keys.items()
            if meta.is_expired
        ]
        
        for key_id in expired_ids:
            self.delete_key(key_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired keys")
        
        return len(expired_ids)
    
    def export_keys(self, format: str = "metadata") -> Dict[str, Any]:
        """
        Export key information.
        Never exports actual key values.
        """
        if format == "metadata":
            return {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "count": len(self._keys),
                "keys": [k.to_dict() for k in self._keys.values()]
            }
        elif format == "summary":
            return {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "stats": self.get_stats()
            }
        else:
            return {"error": f"Unknown format: {format}"}
