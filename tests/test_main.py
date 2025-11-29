"""Tests for main API endpoints"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns service info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Simpleton LLM Service"
    assert "version" in data
    assert "docs" in data
    assert "health" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ollama_status" in data
    assert "version" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint returns prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
