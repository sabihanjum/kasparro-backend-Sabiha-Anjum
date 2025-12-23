"""Integration tests for API endpoints."""
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


def test_smoke_test_full_flow(client):
    """Test full flow: health, data ingestion, retrieval."""
    # 1. Check health
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["db_connected"] in [True, False]
    
    # 2. Check stats
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_records_processed" in stats
    assert "runs" in stats
    assert isinstance(stats["runs"], list)
    
    # 3. Retrieve data
    response = client.get("/data")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data


def test_error_handling_invalid_limit(client):
    """Test error handling for invalid input."""
    response = client.get("/data?limit=200")  # exceeds max
    assert response.status_code == 422


def test_data_retrieval_with_source_filter(client):
    """Test data retrieval with source filtering."""
    response = client.get("/data?source=test")
    assert response.status_code == 200
    assert "data" in response.json()
