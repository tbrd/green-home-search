from pathlib import Path
import sys
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
