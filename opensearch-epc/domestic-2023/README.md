Ingest domestic-2023 into OpenSearch

This folder contains:

- `certificates.csv` — the raw EPC certificates CSV (downloaded from the source)
- `schema.json` — CSVW schema describing the CSV columns
- `ingest_domestic_2023.py` — a Python script to create mappings and bulk ingest into OpenSearch

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
python ingest_domestic_2023.py --csv certificates.csv --schema schema.json --opensearch-url http://localhost:9200 --user admin --password admin --build-properties
```

Notes & recommendations

- The script creates two indices by default: `domestic-2023-certificates` (every certificate row) and `domestic-2023-properties` (one document per property containing the latest certificate by UPRN).
- For faster bulk imports temporarily set `number_of_replicas` to 0 and `refresh_interval` to `-1` on the target index, then restore them after the bulk load.
- If you have a postcode->lat/lon lookup CSV, pass `--postcode-lookup path/to/postcodes.csv` to populate a `location` geo_point from postcodes.
- The mapping is inferred from `schema.json` and includes a `location` geo_point. You may want to refine mappings for numeric/date fields after inspecting sample documents.

If you want me to tune mappings for specific queries (geo+filters on energy rating, construction age, wind turbines, fuel type), paste a small sample (5-10) rows and I will provide a recommended mapping optimized for those queries.
