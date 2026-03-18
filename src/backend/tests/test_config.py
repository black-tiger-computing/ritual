"""
RITUAL Configuration Tests
"""

import pytest
from pathlib import Path
from app.config import Config, DEFAULT_CONFIG, load_config


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.get("server.port") == 8000
        assert config.get("server.host") == "0.0.0.0"

    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        config = Config()
        assert config.get("server.title") == "RITUAL"

    def test_get_with_default(self):
        """Test getting value with default."""
        config = Config()
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_value(self):
        """Test setting configuration value."""
        config = Config()
        config.set("test.key", "test_value")
        assert config.get("test.key") == "test_value"


def test_load_config():
    """Test loading configuration."""
    config = load_config()
    assert config is not None
    assert isinstance(config, Config)
