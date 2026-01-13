"""Tests for health check endpoint."""

from fastapi.testclient import TestClient

from gl_mcp.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gl-mcp-python"
    assert "version" in data


def test_root() -> None:
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gl-mcp-python"
    assert data["docs"] == "/docs"
