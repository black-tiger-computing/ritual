"""
RITUAL API Routes Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.server import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns OK status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


class TestMCMFilesEndpoints:
    """Test MCM file endpoints."""

    def test_get_mcm_files_empty(self, client):
        """Test getting MCM files when none exist."""
        response = client.get("/api/mcm-files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_get_mcm_file_not_found(self, client):
        """Test getting a non-existent MCM file."""
        response = client.get("/api/mcm-files/nonexistent-id")
        assert response.status_code == 404

    def test_create_mcm_file(self, client):
        """Test creating a new MCM file."""
        response = client.post(
            "/api/mcm-files",
            json={"name": "Test Context", "content": "Test content"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Context"
        assert data["content"] == "Test content"
        assert "id" in data
        assert "created_at" in data

    def test_create_mcm_file_invalid_name(self, client):
        """Test creating MCM file with invalid name."""
        response = client.post(
            "/api/mcm-files",
            json={"name": "", "content": "Test content"}
        )
        assert response.status_code == 422

    def test_create_mcm_file_name_too_long(self, client):
        """Test creating MCM file with name exceeding max length."""
        long_name = "x" * 300
        response = client.post(
            "/api/mcm-files",
            json={"name": long_name, "content": "Test content"}
        )
        assert response.status_code == 422


class TestSigilEndpoints:
    """Test Sigil (API key) endpoints."""

    def test_get_sigils_empty(self, client):
        """Test getting sigils when none exist."""
        response = client.get("/api/sigils")
        assert response.status_code == 200
        data = response.json()
        assert "sigils" in data
        assert isinstance(data["sigils"], list)

    def test_create_sigil(self, client):
        """Test creating a new sigil."""
        response = client.post(
            "/api/sigils",
            json={
                "name": "Test Key",
                "provider": "lm-studio",
                "api_key": "test-api-key-123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Key"
        assert data["provider"] == "lm-studio"
        assert "id" in data

    def test_create_sigil_invalid_provider(self, client):
        """Test creating sigil with invalid provider."""
        response = client.post(
            "/api/sigils",
            json={
                "name": "Test Key",
                "provider": "invalid-provider",
                "api_key": "test-key"
            }
        )
        assert response.status_code == 422

    def test_create_sigil_empty_api_key(self, client):
        """Test creating sigil with empty API key."""
        response = client.post(
            "/api/sigils",
            json={
                "name": "Test Key",
                "provider": "lm-studio",
                "api_key": ""
            }
        )
        assert response.status_code == 422


class TestProvidersEndpoints:
    """Test LLM provider endpoints."""

    def test_get_providers(self, client):
        """Test getting providers list."""
        response = client.get("/api/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
