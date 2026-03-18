"""
RITUAL LLM Provider Discovery
Discovers and manages LLM provider connections
"""

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class LLMProvider:
    """Represents an LLM provider connection."""

    def __init__(self, provider_id: str, name: str, url: str, enabled: bool = True):
        self.id = provider_id
        self.name = name
        self.url = url
        self.enabled = enabled
        self.status = "unknown"

    def check_connection(self) -> bool:
        """Check if the provider is accessible."""
        try:
            response = requests.get(f"{self.url}/models", timeout=5)
            if response.status_code == 200:
                self.status = "connected"
                return True
        except Exception as e:
            logger.debug(f"Connection check failed for {self.name}: {e}")

        self.status = "disconnected"
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "status": self.status,
            "enabled": self.enabled
        }


def discover_llm_providers(config) -> List[LLMProvider]:
    """Discover available LLM providers from configuration."""
    providers = []
    llm_config = config.get("llm_providers", {})

    for provider_id, provider_data in llm_config.items():
        provider = LLMProvider(
            provider_id=provider_id,
            name=provider_data.get("name", provider_id),
            url=provider_data.get("url", ""),
            enabled=provider_data.get("enabled", True)
        )
        providers.append(provider)

    return providers


def check_provider_connection(provider: LLMProvider) -> bool:
    """Check if a specific provider is connected."""
    if not provider.enabled:
        return False
    return provider.check_connection()


def get_provider_models(provider: LLMProvider) -> List[str]:
    """Get available models from a provider."""
    try:
        response = requests.get(f"{provider.url}/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return [model.get("id", "") for model in data["data"]]
            elif "models" in data:
                return [model.get("id", "") for model in data["models"]]
    except Exception as e:
        logger.error(f"Error getting models from {provider.name}: {e}")

    return []
