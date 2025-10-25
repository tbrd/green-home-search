Ingest domestic-2023 into OpenSearch

This folder contains:

- `certificates.csv` — the raw EPC certificates CSV (downloaded from the source)
- `schema.json` — CSVW schema describing the CSV columns
- `ingest_domestic_2023.py` — a Python script to create mappings and bulk ingest into OpenSearch
- `build_property_index.py` — a Python script to build a comprehensive property index from certificates
- `create_listings_index.py` — create versioned listings index and filtered aliases
- `listings-v1.mapping.json` — listings index mapping
- `generate_dummy_listings.py` — generate realistic dummy listings from the properties index
- `ingest_listings.py` — skeleton to enrich and upsert listing docs from external feed

Requirements
- Python 3.9+
- `opensearch-py` Python package (install with pip)

Install dependencies (recommended inside a venv):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install opensearch-py
```

Example usage

```powershell
# Set environment variables or pass args to the script
$env:OPENSEARCH_URL='http://localhost:9200'
$env:OPENSEARCH_USER='admin'
$env:OPENSEARCH_PASS='admin'
python ingest.py --csv ./data/domestic/certificates.csv --schema ./data/domestic/schema.json --opensearch-url http://localhost:9200 --user admin --password admin --build-properties
```

Building the Property Index (Recommended)

For a richer, more comprehensive property index, use the new `build_property_index.py` script:

```bash
# Step 1: Ingest certificates
python ingest_domestic_2023.py --csv certificates.csv --schema schema.json

# Step 2: Build property index with full details
python build_property_index.py
```

This creates a `domestic-2023-properties` index where each document represents a unique property with:
- Complete address information
- Latest EPC certificate with detailed fields
- Historical EPC certificates array
- Estimated running costs
- Solar panel and renewable energy detection

See [BUILD_PROPERTY_INDEX_README.md](BUILD_PROPERTY_INDEX_README.md) for full documentation.

Notes & recommendations

- `ingest_domestic_2023.py` creates a `domestic-2023-certificates` index with every certificate row.
- `build_property_index.py` (NEW) creates a richer `domestic-2023-properties` index with one document per property containing latest EPC, historical EPCs array, and additional metadata.
- For faster bulk imports temporarily set `number_of_replicas` to 0 and `refresh_interval` to `-1` on the target index, then restore them after the bulk load.
- If you have a postcode->lat/lon lookup CSV, pass `--postcode-lookup path/to/postcodes.csv` to populate a `location` geo_point from postcodes.
- The mapping is inferred from `schema.json` and includes a `location` geo_point. You may want to refine mappings for numeric/date fields after inspecting sample documents.


Listings (NEW)
---------------

We store property sales/rental listings in a dedicated index, linked to the properties index via `property_id` (UPRN). Only a small subset of property fields (fuel type, EPC rating/score, solar flags, running costs, location) are denormalized onto the listing for fast queries.

Create the listings index and aliases:

```powershell
# Uses OPENSEARCH_URL/USER/PASS env vars if set
python .\create_listings_index.py --index listings-v1 --active-alias listings-active --all-alias listings-all --force
```

Generate dummy listings from properties (recommended for testing):

```powershell
# Generate listings for 1% of properties (default)
python .\generate_dummy_listings.py --properties-index properties --listings-index listings-v1 --percentage 1.0

# Generate more listings (e.g., 5% of properties)
python .\generate_dummy_listings.py --properties-index properties --listings-index listings-v1 --percentage 5.0
```

Or populate listings from a real feed (skeleton demo):

```powershell
python .\ingest_listings.py --properties-index properties --listings-index listings-v1
```

Index/aliases:
- `listings-v1` — concrete index (versioned)
- `listings-active` — filtered alias (is_active=true) for default searches
- `listings-all` — alias including active and expired for history

Search examples (HTTP):

```json
POST listings-active/_search
{
	"size": 20,
	"query": {
		"bool": {
			"filter": [
				{ "geo_distance": { "distance": "10km", "location": { "lat": 51.5074, "lon": -0.1278 } } },
				{ "range": { "bedrooms": { "gte": 3 } } },
				{ "terms": { "main_fuel": ["mains_gas", "electricity"] } },
				{ "term": { "solar_panels": true } },
				{ "range": { "running_cost_monthly": { "lte": 200 } } }
			]
		}
	},
	"sort": [ { "price": "asc" }, { "listed_at": "desc" } ]
}
```

Collapse multiple active listings for the same property (show one row per property):

```json
POST listings-active/_search
{
	"size": 20,
	"query": { "match_all": {} },
	"collapse": {
		"field": "property_id",
		"inner_hits": { "name": "all_listings_for_property", "size": 5, "sort": [ { "price": "asc" } ] }
	},
	"sort": [ { "price": "asc" } ]
}
```

Retention & scale:
- Keep expired listings in the same index with `is_active=false`; search via `listings-active` alias.
- Purge expired records older than ~90 days using delete-by-query on `expires_at`.
- Start with 1–3 primary shards; if volume grows, create `listings-v2` with more shards and reindex, then move the aliases.

Analytics:
- Common aggregations (counts by EPC band, main fuel, solar flags; avg price by EPC band; cost distributions) work directly on the listings index because EPC attributes are denormalized onto listings.
- For property-only analytics, use the `properties` index. If you ever need complex cross-entity aggregations that can’t be denormalized, consider transforms or parent-child in a dedicated analytics index.
