from pathlib import Path
import sys
import asyncio

# ensure api root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import search


def test_search_returns_results():
    # Call the async search() function directly to avoid TestClient/httpx compatibility issues
    results = asyncio.run(search(None, address='High Wycombe'))
    assert isinstance(results, list)
    assert len(results) >= 1
    first = results[0]
    assert hasattr(first, 'id') and hasattr(first, 'name') and hasattr(first, 'lat') and hasattr(first, 'lng')
