"""
RITUAL Storage Manager
Handles data persistence for MCM files and API keys
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages storage for MCM files and encrypted API keys."""

    def __init__(self, config):
        self.config = config
        self.data_dir = Path(config.get("storage.data_dir", ".ritual"))
        self.mcm_dir = self.data_dir / "mcm-files"
        self.sigils_file = self.data_dir / "sigils.json"
        self._encryption_key: Optional[bytes] = None

        # Initialize directories
        self._init_storage()

        # Setup encryption if enabled
        if config.get("storage.encryption_enabled", True):
            self._setup_encryption()

    def _init_storage(self) -> None:
        """Initialize storage directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.mcm_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage initialized at {self.data_dir}")

    def _setup_encryption(self) -> None:
        """Setup Fernet encryption."""
        key_file = self.data_dir / ".key"
        if key_file.exists():
            with open(key_file, "rb") as f:
                self._encryption_key = f.read()
        else:
            self._encryption_key = Fernet.generate_key()
            key_file.write_bytes(self._encryption_key)
            # Set restrictive permissions (owner read/write only)
            os.chmod(key_file, 0o600)
            logger.info("Generated new encryption key")

        self._cipher = Fernet(self._encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt data using Fernet."""
        if not self._cipher:
            return data
        return self._cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        if not self._cipher:
            return encrypted_data
        return self._cipher.decrypt(encrypted_data.encode()).decode()

    # MCM Files Management
    def get_mcm_files(self) -> List[Dict[str, Any]]:
        """Get all MCM files."""
        files = []
        for file_path in self.mcm_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    files.append(json.load(f))
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        return sorted(files, key=lambda x: x.get("updated_at", ""), reverse=True)

    def get_mcm_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific MCM file by ID."""
        file_path = self.mcm_dir / f"{file_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return None

    def create_mcm_file(self, name: str, content: str) -> Dict[str, Any]:
        """Create a new MCM file."""
        file_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat() + "Z"

        mcm_file = {
            "id": file_id,
            "name": name,
            "content": content,
            "created_at": now,
            "updated_at": now
        }

        file_path = self.mcm_dir / f"{file_id}.json"
        with open(file_path, "w") as f:
            json.dump(mcm_file, f, indent=2)

        logger.info(f"Created MCM file: {file_id}")
        return mcm_file

    def update_mcm_file(self, file_id: str, name: str, content: str) -> Optional[Dict[str, Any]]:
        """Update an existing MCM file."""
        mcm_file = self.get_mcm_file(file_id)
        if not mcm_file:
            return None

        mcm_file["name"] = name
        mcm_file["content"] = content
        mcm_file["updated_at"] = datetime.utcnow().isoformat() + "Z"

        file_path = self.mcm_dir / f"{file_id}.json"
        with open(file_path, "w") as f:
            json.dump(mcm_file, f, indent=2)

        logger.info(f"Updated MCM file: {file_id}")
        return mcm_file

    def delete_mcm_file(self, file_id: str) -> bool:
        """Delete an MCM file."""
        file_path = self.mcm_dir / f"{file_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted MCM file: {file_id}")
            return True
        return False

    # Sigils (API Keys) Management
    def get_sigils(self) -> List[Dict[str, Any]]:
        """Get all stored API keys (without decrypted values)."""
        if not self.sigils_file.exists():
            return []

        with open(self.sigils_file, "r") as f:
            sigils = json.load(f)

        # Don't return actual API keys
        for sigil in sigils:
            if "api_key" in sigil:
                del sigil["api_key"]

        return sigils

    def get_sigil(self, sigil_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific sigil (API key)."""
        sigils = self.get_sigils()
        for sigil in sigils:
            if sigil.get("id") == sigil_id:
                return sigil
        return None

    def get_sigil_with_key(self, sigil_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific sigil with the decrypted API key."""
        if not self.sigils_file.exists():
            return None

        with open(self.sigils_file, "r") as f:
            sigils = json.load(f)

        for sigil in sigils:
            if sigil.get("id") == sigil_id:
                if "encrypted_key" in sigil:
                    sigil["api_key"] = self.decrypt(sigil["encrypted_key"])
                return sigil
        return None

    def create_sigil(self, name: str, provider: str, api_key: str) -> Dict[str, Any]:
        """Create a new sigil (API key)."""
        sigil_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat() + "Z"

        encrypted_key = self.encrypt(api_key) if self._cipher else api_key

        sigil = {
            "id": sigil_id,
            "name": name,
            "provider": provider,
            "encrypted_key": encrypted_key,
            "created_at": now
        }

        sigils = []
        if self.sigils_file.exists():
            with open(self.sigils_file, "r") as f:
                sigils = json.load(f)

        sigils.append(sigil)

        with open(self.sigils_file, "w") as f:
            json.dump(sigils, f, indent=2)

        logger.info(f"Created sigil: {sigil_id}")

        # Return without the key
        result = sigil.copy()
        del result["encrypted_key"]
        return result

    def delete_sigil(self, sigil_id: str) -> bool:
        """Delete a sigil (API key)."""
        if not self.sigils_file.exists():
            return False

        with open(self.sigils_file, "r") as f:
            sigils = json.load(f)

        original_count = len(sigils)
        sigils = [s for s in sigils if s.get("id") != sigil_id]

        if len(sigils) < original_count:
            with open(self.sigils_file, "w") as f:
                json.dump(sigils, f, indent=2)
            logger.info(f"Deleted sigil: {sigil_id}")
            return True
        return False
