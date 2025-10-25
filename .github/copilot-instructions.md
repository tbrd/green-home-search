# Green Home Search - AI Coding Assistant Instructions

## Project Overview

This is a three-tier energy efficiency search platform for UK domestic properties using EPC (Energy Performance Certificate) data:

- **`opensearch-epc/`** - Data ingestion pipeline for EPC CSV data into OpenSearch cluster
- **`api/`** - FastAPI backend that queries OpenSearch and proxies to external EPC APIs
- **`web/`** - React/TypeScript frontend with Vite dev server and TanStack Query

## Architecture Patterns

### Data Flow
1. Raw EPC CSV data → `opensearch-epc/domestic-2023/ingest_domestic_2023.py` → OpenSearch indices
2. Frontend search → Vite proxy (`/api/*`) → FastAPI backend → OpenSearch query
3. Optional external EPC API fallback via environment variables (`EPC_API_KEY`, `EPC_API_URL`)

### Key Integration Points
- **Vite Proxy**: `web/vite.config.ts` proxies `/api/*` to `http://127.0.0.1:8000` (FastAPI)
- **OpenSearch Client**: `api/main.py` connects to local cluster with configurable auth
- **CORS**: API allows `localhost:5173` (Vite dev) and `localhost:3000` origins
- **Environment Config**: Each tier uses `.env` files (not committed) for secrets

## Development Workflows

### Starting the Stack
```powershell
# 1. Start OpenSearch cluster
cd opensearch-epc; docker-compose up -d

# 2. Ingest EPC data (one-time setup)
cd domestic-2023
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install opensearch-py
python ingest_domestic_2023.py --csv certificates.csv --schema schema.json

# 3. Start API server
cd ../../api
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 4. Start frontend dev server
cd ../web
npm install; npm run dev  # Runs on :5173 with API proxy
```

### Testing Patterns
- **API Tests**: `api/tests/test_search_api.py` uses FastAPI TestClient, expects specific response structure with `query`, `total`, `results`, `took` fields
- **Frontend**: No tests yet - add React Testing Library for components
- **Integration**: OpenSearch tests in `opensearch-epc/domestic-2023/test_integration_ingest.py`

## Code Conventions

### API Response Format
```python
# Standard search response structure (api/main.py)
{
    "query": str,
    "total": int,
    "results": [Result],
    "took": int,
    "offset": int,
    "limit": int,
    "index_used": str
}
```

### Frontend Query Interface
```typescript
// Consistent with backend filters (web/src/queries/searchQuery.ts)
interface SearchQuery {
    location: string;
    energyRating?: string;  // A-G ratings
}

// Results allow flexible EPC fields with lat/lng variants
interface Result {
    uprn: string;
    address: string;
    current_energy_rating?: string;
    lat?: number; lng?: number;  // OR latitude/longitude
    [key: string]: any;  // Permissive for EPC field variations
}
```

### OpenSearch Index Strategy
- **`domestic-2023-certificates`** - Raw certificate documents (one per certificate)
- **`domestic-2023-properties`** - Aggregated by UPRN (latest certificate per property)
- **Schema-driven mapping** - `schema.json` (CSVW format) auto-generates field types
- **Geo-point support** - Optional postcode→lat/lon enrichment for location searches

## Environment Configuration

### Required Environment Variables
```powershell
# API (optional - falls back to local OpenSearch)
$env:OPENSEARCH_URL = 'http://localhost:9200'
$env:OPENSEARCH_USER = 'admin'
$env:OPENSEARCH_PASS = 'admin'
$env:CERTIFICATES_INDEX = 'domestic-2023-certificates'

# External EPC API integration (optional)
$env:EPC_API_KEY = 'your-api-key'
$env:EPC_API_URL = 'https://api.epc.gov.uk/search'

# Frontend build-time config
VITE_API_BASE=/api  # Proxy target for API calls
```

## Common Development Tasks

### Adding New Search Filters
1. **Backend**: Add query parameter to `/search` endpoint in `api/main.py`
2. **OpenSearch**: Update query builder to include filter clause
3. **Frontend**: Extend `SearchQuery` interface and `LocationSearch.tsx` form
4. **Types**: Update `Result` interface if response fields change

### Data Pipeline Changes
1. **Schema**: Modify `opensearch-epc/domestic-2023/schema.json` for new CSV columns
2. **Mapping**: Regenerate index mapping with `ingest_domestic_2023.py --build-properties`
3. **API**: Update result field handling if new data types added

### Performance Debugging
- **API**: Check `/health` endpoint for OpenSearch cluster status and index counts
- **Frontend**: Debug panel in search results shows request URL and raw API response
- **OpenSearch**: Use `opensearch-dashboards` on `:5601` for query analysis

## External Dependencies

- **UK EPC Register API** - Optional external data source with rate limiting
- **OpenSearch 2.x** - Local cluster via Docker Compose, requires Java heap tuning
- **TanStack Query** - Frontend data fetching with caching, expects specific response shapes
