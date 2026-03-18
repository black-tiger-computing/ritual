"""
RITUAL Storage Tests
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from app.config import Config
from app.storage import StorageManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config(temp_dir):
    """Create a test configuration."""
    config = Config()
    config.set("storage.data_dir", str(temp_dir))
    config.set("storage.encryption_enabled", False)
    return config


@pytest.fixture
def storage(config):
    """Create a storage manager with test config."""
    return StorageManager(config)


class TestStorageInitialization:
    """Test storage initialization."""

    def test_directories_created(self, storage, temp_dir):
        """Test that storage directories are created."""
        assert (temp_dir / "mcm-files").exists()
        assert (temp_dir / "mcm-files").is_dir()

    def test_data_dir_created(self, storage, temp_dir):
        """Test that data directory is created."""
        assert temp_dir.exists()


class TestMCMFiles:
    """Test MCM file operations."""

    def test_get_mcm_files_empty(self, storage):
        """Test getting MCM files when none exist."""
        files = storage.get_mcm_files()
        assert files == []

    def test_create_mcm_file(self, storage):
        """Test creating a new MCM file."""
        file = storage.create_mcm_file("Test Context", "Test content")
        
        assert file["name"] == "Test Context"
        assert file["content"] == "Test content"
        assert "id" in file
        assert "created_at" in file
        assert "updated_at" in file

    def test_get_mcm_file(self, storage):
        """Test getting a specific MCM file."""
        created = storage.create_mcm_file("Test Context", "Test content")
        
        retrieved = storage.get_mcm_file(created["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["name"] == "Test Context"

    def test_get_mcm_file_not_found(self, storage):
        """Test getting a non-existent MCM file."""
        result = storage.get_mcm_file("nonexistent-id")
        assert result is None

    def test_update_mcm_file(self, storage):
        """Test updating an MCM file."""
        created = storage.create_mcm_file("Original", "Original content")
        
        updated = storage.update_mcm_file(
            created["id"],
            "Updated",
            "Updated content"
        )
        
        assert updated["name"] == "Updated"
        assert updated["content"] == "Updated content"

    def test_update_mcm_file_not_found(self, storage):
        """Test updating a non-existent MCM file."""
        result = storage.update_mcm_file("nonexistent", "Name", "Content")
        assert result is None

    def test_delete_mcm_file(self, storage):
        """Test deleting an MCM file."""
        created = storage.create_mcm_file("Test", "Content")
        
        result = storage.delete_mcm_file(created["id"])
        
        assert result is True
        assert storage.get_mcm_file(created["id"]) is None

    def test_delete_mcm_file_not_found(self, storage):
        """Test deleting a non-existent MCM file."""
        result = storage.delete_mcm_file("nonexistent")
        assert result is False


class TestSigils:
    """Test Sigil (API key) operations."""

    def test_get_sigils_empty(self, storage):
        """Test getting sigils when none exist."""
        sigils = storage.get_sigils()
        assert sigils == []

    def test_create_sigil(self, storage):
        """Test creating a new sigil."""
        sigil = storage.create_sigil(
            "Test Key",
            "lm-studio",
            "test-api-key"
        )
        
        assert sigil["name"] == "Test Key"
        assert sigil["provider"] == "lm-studio"
        assert "id" in sigil

    def test_get_sigil(self, storage):
        """Test getting a specific sigil."""
        created = storage.create_sigil("Test", "lm-studio", "key123")
        
        retrieved = storage.get_sigil(created["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["name"] == "Test"

    def test_get_sigil_not_found(self, storage):
        """Test getting a non-existent sigil."""
        result = storage.get_sigil("nonexistent")
        assert result is None

    def test_delete_sigil(self, storage):
        """Test deleting a sigil."""
        created = storage.create_sigil("Test", "lm-studio", "key")
        
        result = storage.delete_sigil(created["id"])
        
        assert result is True
        assert storage.get_sigil(created["id"]) is None


class TestEncryption:
    """Test encryption functionality."""

    def test_encryption_enabled(self, temp_dir):
        """Test that encryption is properly enabled."""
        config = Config()
        config.set("storage.data_dir", str(temp_dir))
        config.set("storage.encryption_enabled", True)
        
        storage = StorageManager(config)
        
        # Check that key file was created
        key_file = temp_dir / ".key"
        assert key_file.exists()

    def test_encrypt_decrypt(self, temp_dir):
        """Test encryption and decryption."""
        config = Config()
        config.set("storage.data_dir", str(temp_dir))
        config.set("storage.encryption_enabled", True)
        
        storage = StorageManager(config)
        
        original = "secret-api-key"
        encrypted = storage.encrypt(original)
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
