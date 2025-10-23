from pathlib import Path
import sys
import pytest

# ensure api root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import search, get_running_cost


def test_search_returns_results():
    # Call the async search() function directly to avoid TestClient/httpx compatibility issues
    results = asyncio.run(search(None, address='High Wycombe'))
    assert isinstance(results, list)
    assert len(results) >= 1
    first = results[0]
    assert hasattr(first, 'id') and hasattr(first, 'name') and hasattr(first, 'lat') and hasattr(first, 'lng')


def test_running_cost_with_valid_rating():
    """Test running cost endpoint with valid EPC rating."""
    epc_doc = {"current-energy-rating": "C"}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 100}


def test_running_cost_with_different_rating():
    """Test running cost endpoint with different valid rating."""
    epc_doc = {"current-energy-rating": "A"}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 50}


def test_running_cost_with_uppercase_field():
    """Test running cost endpoint with uppercase field name."""
    epc_doc = {"CURRENT_ENERGY_RATING": "E"}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 150}


def test_running_cost_with_invalid_rating():
    """Test running cost endpoint with invalid rating."""
    epc_doc = {"current-energy-rating": "Z"}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": None}
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_search_returns_results(client):
    """Test that search endpoint returns properly structured results."""
    response = client.get("/search?address=High Wycombe&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "query" in data
    assert "total" in data
    assert "results" in data
    assert "took" in data
    assert "offset" in data
    assert "limit" in data
    assert "index_used" in data
    
    # Check query matches input
    assert data["query"] == "High Wycombe"
    assert data["limit"] == 5
    assert data["offset"] == 0
    
    # Check results structure if any results returned
    if data["total"] > 0:
        assert len(data["results"]) >= 1
        first_result = data["results"][0]
        
        # Check required fields are present
        assert "id" in first_result
        assert "address" in first_result
        assert "current_energy_rating" in first_result
        assert "property_type" in first_result
        assert "score" in first_result
        
        # Check that score is a number
        assert isinstance(first_result["score"], (int, float))


def test_search_with_filters(client):
    """Test search with energy rating and property type filters."""
    response = client.get("/search?address=London&energy_rating=C&property_type=House&limit=3")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "results" in data
    assert data["limit"] == 3
    
    # If results exist, check they match filters
    for result in data["results"]:
        if result.get("current_energy_rating"):
            assert result["current_energy_rating"] == "C"
        if result.get("property_type"):
            assert result["property_type"] == "House"


def test_search_with_efficiency_range(client):
    """Test search with energy efficiency range filter."""
    response = client.get("/search?address=Manchester&min_efficiency=60&max_efficiency=80&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "results" in data
    
    # If results exist, check efficiency is within range
    for result in data["results"]:
        if result.get("current_energy_efficiency") is not None:
            efficiency = result["current_energy_efficiency"]
            assert 60 <= efficiency <= 80


def test_search_pagination(client):
    """Test search pagination works correctly."""
    # Get first page
    response1 = client.get("/search?address=London&limit=2&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Get second page
    response2 = client.get("/search?address=London&limit=2&offset=2")
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Both should have same total but different offsets
    assert data1["total"] == data2["total"]
    assert data1["offset"] == 0
    assert data2["offset"] == 2
    
    # Results should be different (if enough results exist)
    if data1["total"] > 2 and len(data1["results"]) > 0 and len(data2["results"]) > 0:
        assert data1["results"][0]["id"] != data2["results"][0]["id"]


def test_search_invalid_parameters(client):
    """Test search with invalid parameters returns appropriate errors."""
    # Test missing address parameter
    response = client.get("/search")
    assert response.status_code == 422
    
    # Test invalid limit
    response = client.get("/search?address=test&limit=0")
    assert response.status_code == 422
    
    response = client.get("/search?address=test&limit=101")
    assert response.status_code == 422
    
    # Test invalid offset
    response = client.get("/search?address=test&offset=-1")
    assert response.status_code == 422


def test_health_endpoint(client):
    """Test health endpoint returns proper status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "opensearch" in data
    assert "indices" in data
