Ingest domestic-2023 into OpenSearch

This folder contains:

- `certificates.csv` — the raw EPC certificates CSV (downloaded from the source)
- `schema.json` — CSVW schema describing the CSV columns
- `ingest_domestic_2023.py` — a Python script to create mappings and bulk ingest into OpenSearch
- `build_property_index.py` — a Python script to build a comprehensive property index from certificates (NEW)

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
