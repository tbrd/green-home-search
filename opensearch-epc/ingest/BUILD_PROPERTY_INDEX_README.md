# Build Property Index from Certificates

This script builds a comprehensive property index from the EPC certificates index in OpenSearch. Each property document represents a unique property (identified by UPRN) and includes:

- **Address information** - Structured address with postcode and optional geo-coordinates
- **Latest EPC** - Detailed information from the most recent EPC certificate
- **Historical EPCs** - Array of all EPC certificates for the property
- **Metadata** - Estimated running costs, creation timestamp, and optional market data

## Property Document Structure

```json
{
  "uprn": "123456789",
  "address": {
    "address": "12 Rosevale Gardens, Piddington, High Wycombe, HP13 3HH",
    "address1": "12 Rosevale Gardens",
    "address2": "Piddington",
    "address3": "High Wycombe",
    "postcode": "HP13 3HH",
    "lat": 51.501,
    "long": -0.141
  },
  "location": {
    "lat": 51.501,
    "lon": -0.141
  },
  "latest_epc": {
    "LMK_KEY": "4938aef",
    "rating": "B",
    "score": 85,
    "inspection_date": "2024-09-10",
    "lodgement_date": "2024-09-15",
    "property_type": "House",
    "built_form": "Semi-Detached",
    "construction_age_band": "1983-1990",
    "total_floor_area": 125.5,
    "heating_type": "Air Source Heat Pump",
    "solar_panels": true,
    "solar_water_heating": false,
    "wall_insulation": "Cavity filled",
    "roof_description": "Insulated to modern standards",
    "windows_description": "Double glazed",
    "main_fuel": "Electricity",
    "wind_turbine_count": 0,
    "co2_emissions_current": 1.5,
    "energy_consumption_current": 250.0,
    "heating_cost_current": 800.0,
    "hot_water_cost_current": 350.0,
    "lighting_cost_current": 200.0
  },
  "epcs": [
    {
      "LMK_KEY": "4938aef",
      "rating": "B",
      "score": 85,
      "inspection_date": "2024-09-10",
      "lodgement_date": "2024-09-15"
    },
    {
      "LMK_KEY": "ab928437e",
      "rating": "D",
      "score": 60,
      "inspection_date": "2015-04-02",
      "lodgement_date": "2015-04-10"
    }
  ],
  "estimated_running_cost": 1350,
  "created_at": "2025-10-21T12:00:00Z"
}
```

## Requirements

- Python 3.9+
- `opensearch-py` package (install with pip)
- A running OpenSearch instance
- An existing certificates index (created by `ingest_domestic_2023.py`)

## Installation

Install dependencies inside a virtual environment:

**Bash/Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install opensearch-py
```

**PowerShell/Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install opensearch-py
```

## Usage

### Basic Usage

**Bash/Linux/macOS:**
```bash
# Set environment variables
export OPENSEARCH_URL='http://localhost:9200'
export OPENSEARCH_USER='admin'
export OPENSEARCH_PASS='admin'

# Run the script
python build_property_index.py
```

**PowerShell/Windows:**
```powershell
# Set environment variables
$env:OPENSEARCH_URL='http://localhost:9200'
$env:OPENSEARCH_USER='admin'
$env:OPENSEARCH_PASS='admin'

# Run the script
python build_property_index.py
```

### With Command Line Arguments

**Bash/Linux/macOS:**
```bash
python build_property_index.py \
  --opensearch-url http://localhost:9200 \
  --user admin \
  --password admin \
  --cert-index certificates \
  --prop-index properties \
  --batch-size 500
```

**PowerShell/Windows:**
```powershell
python build_property_index.py `
  --opensearch-url http://localhost:9200 `
  --user admin `
  --password admin `
  --cert-index certificates `
  --prop-index properties `
  --batch-size 500
```

### Command Line Options

- `--opensearch-url` - OpenSearch endpoint URL (default: $OPENSEARCH_URL or http://localhost:9200)
- `--user` - OpenSearch username (default: $OPENSEARCH_USER)
- `--password` - OpenSearch password (default: $OPENSEARCH_PASS)
- `--cert-index` - Name of the certificates index (default: domestic-2023-certificates)
- `--prop-index` - Name of the properties index to create (default: domestic-2023-properties)
- `--batch-size` - Batch size for bulk indexing (default: 500)

## How It Works

1. **Creates Property Index** - Creates a new properties index with optimized mapping for property searches
2. **Fetches All UPRNs** - Uses composite aggregation to page through all unique UPRNs in the certificates index
3. **Fetches Certificates** - For each UPRN, fetches all EPC certificates sorted by date (newest first)
4. **Builds Property Document** - Extracts and structures data into the property document format
5. **Bulk Indexes** - Efficiently bulk indexes all property documents

## Key Features

### Address Extraction
- Combines ADDRESS1, ADDRESS2, ADDRESS3, and POSTCODE into a full address string
- Extracts geo-coordinates from the location field if available
- Supports both dict `{lat, lon}` and string `"lat,lon"` location formats

### Latest EPC Enrichment
- Extracts comprehensive data from the most recent certificate
- Detects solar panels (PHOTO_SUPPLY > 0)
- Detects solar water heating (SOLAR_WATER_HEATING_FLAG = 'Y')
- Includes energy costs, ratings, and property characteristics

### Historical EPC Array
- Includes all historical certificates for the property
- Sorted by lodgement date (newest first)
- Contains key fields: LMK_KEY, rating, score, inspection_date, lodgement_date

### Estimated Running Cost
- Automatically calculates total from heating, hot water, and lighting costs
- Rounded to nearest integer for consistency

## Index Mapping

The script creates a properties index with the following mapping:

- **uprn** - Keyword field for unique property identification
- **address** - Object with structured address fields (text + keyword)
- **location** - geo_point for spatial queries
- **latest_epc** - Object with detailed EPC fields
- **epcs** - Nested array for historical certificates
- **last_sale** - Object for sale price and date (optional, for future use)
- **market_info** - Object for property valuation data (optional, for future use)
- **estimated_running_cost** - Integer for total annual energy costs
- **created_at** - Date timestamp for document creation

## Testing

Run the test suite:

**Bash/Linux/macOS:**
```bash
# Run all tests
python -m pytest test_build_property_index.py -v

# Run specific test class
python -m pytest test_build_property_index.py::TestPropertyMapping -v

# Run with coverage
python -m pytest test_build_property_index.py --cov=build_property_index --cov-report=term-missing
```

**PowerShell/Windows:**
```powershell
# Run all tests
python -m pytest test_build_property_index.py -v

# Run specific test class
python -m pytest test_build_property_index.py::TestPropertyMapping -v

# Run with coverage
python -m pytest test_build_property_index.py --cov=build_property_index --cov-report=term-missing
```

## Performance Considerations

- **Batch Size** - Default 500 provides good balance between memory and speed
- **Composite Aggregation** - Pages through UPRNs in batches of 1000
- **Bulk Indexing** - Uses OpenSearch bulk API for efficient indexing
- **Index Recreation** - Deletes and recreates the properties index if it already exists

For large datasets (millions of properties), consider:
- Temporarily setting `number_of_replicas: 0` during indexing
- Temporarily setting `refresh_interval: -1` during indexing
- Restoring these settings after indexing completes

## Workflow

1. First, ingest certificates using `ingest_domestic_2023.py`:
   
   **Bash/Linux/macOS:**
   ```bash
   python ingest_domestic_2023.py --csv certificates.csv --schema schema.json
   ```
   
   **PowerShell/Windows:**
   ```powershell
   python ingest_domestic_2023.py --csv certificates.csv --schema schema.json
   ```

2. Then, build the properties index:
   
   **Bash/Linux/macOS:**
   ```bash
   python build_property_index.py
   ```
   
   **PowerShell/Windows:**
   ```powershell
   python build_property_index.py
   ```

3. Query the properties index for specific properties or search by criteria:
   
   **Bash/Linux/macOS:**
   ```bash
   # Example: Find properties with high energy ratings
   curl -X POST "localhost:9200/domestic-2023-properties/_search" \
     -H 'Content-Type: application/json' \
     -d '{
       "query": {
         "term": {"latest_epc.rating": "A"}
       }
     }'
   ```
   
   **PowerShell/Windows:**
   ```powershell
   # Example: Find properties with high energy ratings
   Invoke-RestMethod -Uri "http://localhost:9200/domestic-2023-properties/_search" `
     -Method Post `
     -ContentType "application/json" `
     -Body '{
       "query": {
         "term": {"latest_epc.rating": "A"}
       }
     }'
   ```

## Future Enhancements

The property document structure includes optional fields for future enhancements:

- **last_sale** - Property sale history from Land Registry data
- **market_info** - Property valuations from external sources (Zoopla, Rightmove, etc.)
- **Additional metadata** - Planning applications, flood risk, local amenities

These fields can be populated by extending the script or through separate enrichment processes.
