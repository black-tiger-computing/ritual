"""
RITUAL LLM Discovery Tests
"""

import pytest
from unittest.mock import Mock, patch
from app.config import Config
from app.llm_discovery import (
    LLMProvider,
    discover_llm_providers,
    check_provider_connection,
    get_provider_models
)


class TestLLMProvider:
    """Test LLMProvider class."""

    def test_provider_creation(self):
        """Test creating a provider."""
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        
        assert provider.id == "lm-studio"
        assert provider.name == "LM Studio"
        assert provider.url == "http://localhost:1234"
        assert provider.enabled is True
        assert provider.status == "unknown"

    def test_provider_to_dict(self):
        """Test converting provider to dictionary."""
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        provider.status = "connected"
        
        result = provider.to_dict()
        
        assert result["id"] == "lm-studio"
        assert result["name"] == "LM Studio"
        assert result["url"] == "http://localhost:1234"
        assert result["enabled"] is True
        assert result["status"] == "connected"

    @patch('app.llm_discovery.requests.get')
    def test_check_connection_success(self, mock_get):
        """Test successful connection check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        result = provider.check_connection()
        
        assert result is True
        assert provider.status == "connected"
        mock_get.assert_called_once_with("http://localhost:1234/models", timeout=5)

    @patch('app.llm_discovery.requests.get')
    def test_check_connection_failure(self, mock_get):
        """Test failed connection check."""
        mock_get.side_effect = Exception("Connection refused")
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        result = provider.check_connection()
        
        assert result is False
        assert provider.status == "disconnected"

    @patch('app.llm_discovery.requests.get')
    def test_check_connection_non_200(self, mock_get):
        """Test connection check with non-200 status."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        result = provider.check_connection()
        
        assert result is False
        assert provider.status == "disconnected"


class TestDiscoverProviders:
    """Test provider discovery."""

    def test_discover_no_configured(self):
        """Test discovering with no configured providers."""
        config = Config()
        config.set("providers.enabled", [])
        
        providers = discover_llm_providers(config)
        
        # Should return default providers even without config
        assert len(providers) > 0

    def test_discover_default_providers(self):
        """Test discovering default providers."""
        config = Config()
        
        providers = discover_llm_providers(config)
        
        provider_ids = [p.id for p in providers]
        
        # Should have at least lm-studio and msty
        assert "lm-studio" in provider_ids or "msty" in provider_ids


class TestProviderModels:
    """Test getting provider models."""

    @patch('app.llm_discovery.requests.get')
    def test_get_models_success(self, mock_get):
        """Test getting models from a provider."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "model-1", "name": "Model 1"},
                {"id": "model-2", "name": "Model 2"}
            ]
        }
        mock_get.return_value = mock_response
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        models = get_provider_models(provider)
        
        assert len(models) == 2
        assert "model-1" in models
        assert "model-2" in models

    @patch('app.llm_discovery.requests.get')
    def test_get_models_failure(self, mock_get):
        """Test getting models when provider is unavailable."""
        mock_get.side_effect = Exception("Connection failed")
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        models = get_provider_models(provider)
        
        assert models == []


class TestCheckProviderConnection:
    """Test check_provider_connection function."""

    @patch('app.llm_discovery.requests.get')
    def test_check_provider_connection_enabled(self, mock_get):
        """Test checking connection for enabled provider."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", True)
        check_provider_connection(provider)
        
        assert provider.status == "connected"

    @patch('app.llm_discovery.requests.get')
    def test_check_provider_connection_disabled(self, mock_get):
        """Test checking connection for disabled provider."""
        provider = LLMProvider("lm-studio", "LM Studio", "http://localhost:1234", False)
        check_provider_connection(provider)
        
        # Should not attempt connection for disabled providers
        mock_get.assert_not_called()
        assert provider.status == "unknown"
