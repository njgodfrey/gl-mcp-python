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
    assert "providers" in data
    assert "sessions" in data


def test_root() -> None:
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gl-mcp-python"
    assert data["docs"] == "/docs"


def test_mcp_initialize() -> None:
    """Test MCP initialization request."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert data["result"]["serverInfo"]["name"] == "gl-mcp-python"
    assert "mcp-session-id" in response.headers


def test_mcp_list_tools() -> None:
    """Test MCP tools/list request."""
    # First initialize to get session
    init_response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        },
    )
    session_id = init_response.headers.get("mcp-session-id")

    # List tools
    response = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
