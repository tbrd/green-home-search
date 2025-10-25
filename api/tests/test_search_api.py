from pathlib import Path
import sys
import pytest
import asyncio

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
    """Test running cost endpoint with valid cost data."""
    epc_doc = {"HEATING_COST_CURRENT": 80, "HOT_WATER_COST_CURRENT": 20}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 100}


def test_running_cost_with_different_rating():
    """Test running cost endpoint with different valid costs."""
    epc_doc = {"HEATING_COST_CURRENT": 30, "HOT_WATER_COST_CURRENT": 20}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 50}


def test_running_cost_with_uppercase_field():
    """Test running cost endpoint with uppercase field names."""
    epc_doc = {"HEATING_COST_CURRENT": 120, "HOT_WATER_COST_CURRENT": 30}
    result = asyncio.run(get_running_cost(epc_doc))
    assert result == {"running_cost": 150}


def test_running_cost_with_invalid_rating():
    """Test running cost endpoint with missing cost data."""
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
        assert "running_cost" in first_result
        
        # Check that score is a number
        assert isinstance(first_result["score"], (int, float))
        
        # Check that running_cost is either a number or None
        assert first_result["running_cost"] is None or isinstance(first_result["running_cost"], (int, float))


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


def test_search_includes_running_cost(client):
    """Test that search results include running cost calculations."""
    response = client.get("/search?address=High Wycombe&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have results
    if data["total"] > 0 and len(data["results"]) > 0:
        for result in data["results"]:
            # Every result should have a running_cost field
            assert "running_cost" in result
            
            # If the result has heating and hot water cost data, running_cost should be calculated
            if result.get("heating_cost_current") is not None and result.get("hot_water_cost_current") is not None:
                assert result["running_cost"] is not None
                assert isinstance(result["running_cost"], (int, float))
                # Running cost should be the sum of heating and hot water costs
                expected_cost = result["heating_cost_current"] + result["hot_water_cost_current"]
                assert result["running_cost"] == expected_cost
            else:
                # If cost data is missing, running_cost should be None
                assert result["running_cost"] is None


def test_listings_search_with_price_filter(client):
    """Test listings search with price range filter."""
    response = client.get("/listings/search?q=London&min_price=100000&max_price=500000&size=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "results" in data
    assert "total" in data
    
    # If results exist, check they match price filters
    for result in data["results"]:
        if result.get("price") is not None:
            price = result["price"]
            assert 100000 <= price <= 500000, f"Price {price} outside range [100000, 500000]"


def test_listings_search_with_min_price_only(client):
    """Test listings search with only minimum price filter."""
    response = client.get("/listings/search?q=London&min_price=250000&size=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "results" in data
    
    # If results exist, check they meet minimum price
    for result in data["results"]:
        if result.get("price") is not None:
            assert result["price"] >= 250000


def test_listings_search_with_max_price_only(client):
    """Test listings search with only maximum price filter."""
    response = client.get("/listings/search?q=London&max_price=300000&size=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert "results" in data
    
    # If results exist, check they meet maximum price
    for result in data["results"]:
        if result.get("price") is not None:
            assert result["price"] <= 300000
