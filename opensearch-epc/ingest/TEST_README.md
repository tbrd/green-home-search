# Test Suite for ingest_domestic_2023.py

This directory contains comprehensive tests for the EPC (Energy Performance Certificate) data ingestion script.

## Test Files

### `test_ingest_domestic_2023.py`
Unit tests covering individual functions and components:

- **TestSchemaLoading**: Tests for loading and parsing CSVW schema files
- **TestTypeConversion**: Tests for converting CSVW data types to OpenSearch field types
- **TestMappingGeneration**: Tests for generating OpenSearch index mappings
- **TestValueParsing**: Tests for parsing CSV values with type conversion
- **TestIngestCertificates**: Tests for the certificate ingestion workflow (mocked)
- **TestMainFunction**: Tests for command-line argument parsing and main workflow

### `test_integration_ingest.py`
Integration tests that test the complete workflow:

- **test_integration_full_workflow**: Creates sample schema and CSV files, tests the complete ingestion process with realistic data
- **test_integration_with_properties_index**: Tests the workflow including properties index building

## Running Tests

### Run all tests
```powershell
C:/code/green-home-search/api/.venv/Scripts/python.exe -m pytest . -v
```

### Run only unit tests
```powershell
C:/code/green-home-search/api/.venv/Scripts/python.exe -m pytest test_ingest_domestic_2023.py -v
```

### Run only integration tests
```powershell
C:/code/green-home-search/api/.venv/Scripts/python.exe test_integration_ingest.py
```

### Run with coverage (if pytest-cov is installed)
```powershell
C:/code/green-home-search/api/.venv/Scripts/python.exe -m pytest . --cov=ingest_domestic_2023 --cov-report=html
```

## Test Coverage

The test suite covers:

✅ **Schema Loading**: Validates schema file parsing and error handling  
✅ **Type Conversion**: Tests CSVW to OpenSearch type mapping  
✅ **Value Parsing**: Tests CSV value parsing with various data types  
✅ **Index Operations**: Tests OpenSearch index creation and management (mocked)  
✅ **Data Ingestion**: Tests bulk indexing operations (mocked)  
✅ **Command Line Interface**: Tests argument parsing and main workflow  
✅ **Integration**: End-to-end testing with realistic sample data  
✅ **Error Handling**: Tests error conditions and edge cases  

## Mocking Strategy

The tests use Python's `unittest.mock` to mock external dependencies:

- **OpenSearch client**: All OpenSearch operations are mocked to avoid requiring a running OpenSearch instance
- **File I/O**: CSV and JSON file operations use temporary files for isolation
- **Network operations**: No actual network calls are made during testing

## Sample Data

The integration tests use realistic sample EPC data including:

- Multiple property types (House, Flat)
- Various energy efficiency ratings
- Complete address information
- Energy consumption and cost data
- All required EPC certificate fields

## Test Isolation

Each test is isolated and independent:

- Temporary files are created and cleaned up automatically
- No shared state between tests
- Mocked dependencies are reset between tests
- Tests can be run in any order

## Adding New Tests

When adding new functionality to `ingest_domestic_2023.py`, add corresponding tests:

1. **Unit tests** in `test_ingest_domestic_2023.py` for individual functions
2. **Integration tests** in `test_integration_ingest.py` for end-to-end workflows
3. Follow the existing patterns for mocking and test structure
4. Use descriptive test names and docstrings