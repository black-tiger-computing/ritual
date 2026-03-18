"""
RITUAL Configuration Management
Load and manage application configuration
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": False,
        "title": "RITUAL",
        "version": "1.0.0"
    },
    "llm_providers": {
        "lm_studio": {
            "name": "LM Studio",
            "url": "http://localhost:1234",
            "enabled": True,
            "timeout": 10
        },
        "msty": {
            "name": "MSTY",
            "url": "http://localhost:9729",
            "enabled": True,
            "timeout": 10
        }
    },
    "storage": {
        "data_dir": ".ritual",
        "mcm_dir": "mcm-files",
        "encryption_enabled": True
    },
    "ui": {
        "theme": "hermetic",
        "accent_color": "#9b59b6",
        "animation_enabled": True
    }
}


class Config:
    """Configuration manager for RITUAL."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self.load()

    def _get_default_config_path(self) -> Path:
        """Get default config file path."""
        # Look for config in various locations
        possible_paths = [
            Path("config/default-config.json"),
            Path(__file__).parent.parent.parent.parent / "config" / "default-config.json",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return possible_paths[0]

    def load(self) -> None:
        """Load configuration from file or use defaults."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self._config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self._config = DEFAULT_CONFIG.copy()
                logger.warning(f"Config file not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._config = DEFAULT_CONFIG.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration (convenience function)."""
    return Config(config_path)
