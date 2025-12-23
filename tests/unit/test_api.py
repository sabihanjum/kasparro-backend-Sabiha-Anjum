"""Unit tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.database import get_db


@pytest.fixture
def client(db_session):
    """Create test client."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


def test_health_endpoint_db_connected(client):
    """Test health endpoint when database is connected."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "db_connected" in data
    assert "etl_last_run" in data


def test_get_data_pagination(client):
    """Test GET /data pagination."""
    response = client.get("/data?limit=10&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "total_count" in data
    assert "limit" in data
    assert "offset" in data
    assert "api_latency_ms" in data
    assert "data" in data


def test_get_data_filtering(client):
    """Test GET /data with source filtering."""
    response = client.get("/data?source=test_source")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)


def test_get_data_invalid_pagination(client):
    """Test GET /data with invalid pagination."""
    response = client.get("/data?limit=101&offset=-1")
    
    # Should fail validation
    assert response.status_code == 422


def test_stats_endpoint(client):
    """Test GET /stats endpoint."""
    response = client.get("/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_records_processed" in data
    assert "total_records_inserted" in data
    assert "total_records_failed" in data
    assert "runs" in data
    assert isinstance(data["runs"], list)
