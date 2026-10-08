"""
Unit tests for application health endpoints.
"""

from fastapi.testclient import TestClient


def test_root_health(client: TestClient):
    """Test /health root endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_live(client: TestClient):
    """Test /health/live liveness probe returns alive."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_api_v1_health(client: TestClient):
    """Test /api/v1/health returns detailed health response."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert "database" in data


def test_health_ready(client: TestClient):
    """Test /health/ready readiness probe returns ready."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_openapi_schema_generation(client: TestClient):
    """Test that OpenAPI schema is properly generated and includes core domain routers."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Career Platform API"
    assert "paths" in data

    # Verify health path exists
    assert "/api/v1/health" in data["paths"]


def test_api_docs_redirect(client: TestClient):
    """Test /api/docs redirects to /docs in development mode."""
    response = client.get("/api/docs", follow_redirects=False)
    assert response.status_code in (307, 302, 200)
