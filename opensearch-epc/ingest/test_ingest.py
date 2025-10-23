#!/usr/bin/env python3
"""
Tests for ingest_domestic_2023.py

This test suite covers:
- Schema loading and parsing
- Type conversion functions
- Mapping generation
- CSV data parsing
- Index operations (mocked)
"""

import pytest
import unittest.mock
import tempfile
import json
import csv
import os
from datetime import datetime
from pathlib import Path

# Import the functions we want to test
from ingest_domestic_2023 import (
    load_schema,
    csvw_type_to_es,
    build_mapping_from_schema,
    parse_value,
    ingest_certificates,
    main
)


class TestSchemaLoading:
    """Test schema loading and parsing functionality."""
    
    def test_load_schema_valid(self):
        """Test loading a valid schema file."""
        schema_data = {
            "tables": [{
                "tableSchema": {
                    "columns": [
                        {"name": "LMK_KEY", "datatype": "string"},
                        {"name": "ADDRESS", "datatype": "string"},
                        {"name": "INSPECTION_DATE", "datatype": "date"},
                        {"name": "TOTAL_FLOOR_AREA", "datatype": "decimal"}
                    ],
                    "primaryKey": "LMK_KEY"
                }
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            schema_path = f.name
        
        try:
            schema = load_schema(schema_path)
            assert 'columns' in schema
            assert 'primaryKey' in schema
            assert schema['primaryKey'] == 'LMK_KEY'
            assert 'LMK_KEY' in schema['columns']
            assert schema['columns']['LMK_KEY'] == 'string'
            assert schema['columns']['TOTAL_FLOOR_AREA'] == 'decimal'
        finally:
            os.unlink(schema_path)
    
    def test_load_schema_no_tables(self):
        """Test schema file with no tables raises SystemExit."""
        schema_data = {"tables": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            schema_path = f.name
        
        try:
            with pytest.raises(SystemExit):
                load_schema(schema_path)
        finally:
            os.unlink(schema_path)


class TestTypeConversion:
    """Test CSVW to OpenSearch type conversion."""
    
    def test_csvw_type_to_es_string(self):
        """Test string type conversion."""
        result = csvw_type_to_es('string')
        expected = {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}}
        assert result == expected
    
    def test_csvw_type_to_es_integer(self):
        """Test integer type conversion."""
        assert csvw_type_to_es('integer') == {'type': 'long'}
        assert csvw_type_to_es('int') == {'type': 'long'}
    
    def test_csvw_type_to_es_float(self):
        """Test float type conversion."""
        assert csvw_type_to_es('float') == {'type': 'double'}
        assert csvw_type_to_es('double') == {'type': 'double'}
        assert csvw_type_to_es('decimal') == {'type': 'double'}
    
    def test_csvw_type_to_es_date(self):
        """Test date type conversion."""
        result = csvw_type_to_es('date')
        assert result['type'] == 'date'
        assert 'format' in result
    
    def test_csvw_type_to_es_dict_format(self):
        """Test type conversion with dict format."""
        dtype = {'base': 'integer'}
        assert csvw_type_to_es(dtype) == {'type': 'long'}
        
        dtype = {'datatype': 'float'}
        assert csvw_type_to_es(dtype) == {'type': 'double'}


class TestMappingGeneration:
    """Test OpenSearch mapping generation."""
    
    def test_build_mapping_from_schema(self):
        """Test building OpenSearch mapping from schema."""
        schema = {
            'columns': {
                'LMK_KEY': 'string',
                'TOTAL_FLOOR_AREA': 'decimal',
                'INSPECTION_DATE': 'date'
            },
            'primaryKey': 'LMK_KEY'
        }
        
        mapping = build_mapping_from_schema(schema)
        
        # Check structure
        assert 'mappings' in mapping
        assert 'properties' in mapping['mappings']
        props = mapping['mappings']['properties']
        
        # Check specific fields
        assert 'LMK_KEY' in props
        assert 'TOTAL_FLOOR_AREA' in props
        assert 'INSPECTION_DATE' in props
        assert 'location' in props  # Should be added automatically
        
        # Check types
        assert props['LMK_KEY']['type'] == 'text'
        assert props['TOTAL_FLOOR_AREA']['type'] == 'double'
        assert props['INSPECTION_DATE']['type'] == 'date'
        assert props['location']['type'] == 'geo_point'


class TestValueParsing:
    """Test CSV value parsing and type conversion."""
    
    def test_parse_value_string(self):
        """Test parsing string values."""
        assert parse_value('hello', 'string') == 'hello'
        assert parse_value('', 'string') is None
        assert parse_value(None, 'string') is None
    
    def test_parse_value_integer(self):
        """Test parsing integer values."""
        assert parse_value('123', 'integer') == 123
        assert parse_value('0', 'int') == 0
        assert parse_value('', 'integer') is None
        # Invalid integer should return original string
        assert parse_value('not_a_number', 'integer') == 'not_a_number'
    
    def test_parse_value_float(self):
        """Test parsing float values."""
        assert parse_value('123.45', 'float') == 123.45
        assert parse_value('0.0', 'double') == 0.0
        assert parse_value('', 'decimal') is None
        # Invalid float should return original string
        assert parse_value('not_a_number', 'float') == 'not_a_number'
    
    def test_parse_value_date(self):
        """Test parsing date values."""
        # Test various date formats
        result = parse_value('2023-01-15', 'date')
        assert isinstance(result, str)
        assert '2023-01-15' in result
        
        result = parse_value('2023-01-15 10:30:00', 'datetime')
        assert isinstance(result, str)
        assert '2023-01-15' in result and '10:30:00' in result
        
        assert parse_value('', 'date') is None
        # Invalid date should return original string
        assert parse_value('invalid_date', 'date') == 'invalid_date'
    
    def test_parse_value_dict_dtype(self):
        """Test parsing with dict-format datatype."""
        dtype = {'base': 'integer'}
        assert parse_value('456', dtype) == 456
        
        dtype = {'datatype': 'float'}
        assert parse_value('123.45', dtype) == 123.45


class TestIngestCertificates:
    """Test the main ingestion function."""
    
    @unittest.mock.patch('ingest_domestic_2023.helpers')
    @unittest.mock.patch('builtins.open')
    def test_ingest_certificates_basic(self, mock_open, mock_helpers):
        """Test basic certificate ingestion."""
        # Mock OpenSearch client
        mock_client = unittest.mock.MagicMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {'acknowledged': True}
        
        # Mock CSV data
        csv_data = [
            {'LMK_KEY': '123', 'ADDRESS': '123 Test St', 'TOTAL_FLOOR_AREA': '100.5'},
            {'LMK_KEY': '456', 'ADDRESS': '456 Demo Ave', 'TOTAL_FLOOR_AREA': '75.0'}
        ]
        
        # Mock csv.DictReader
        mock_reader = unittest.mock.MagicMock()
        mock_reader.__iter__ = unittest.mock.MagicMock(return_value=iter(csv_data))
        
        with unittest.mock.patch('csv.DictReader', return_value=mock_reader):
            schema = {
                'columns': {
                    'LMK_KEY': 'string',
                    'ADDRESS': 'string',
                    'TOTAL_FLOOR_AREA': 'decimal'
                },
                'primaryKey': 'LMK_KEY'
            }
            
            ingest_certificates(mock_client, 'test.csv', schema, 'test-index', batch_size=1)
            
            # Verify index creation
            mock_client.indices.exists.assert_called_once_with(index='test-index')
            mock_client.indices.create.assert_called_once()
            
            # Verify bulk operations were called
            assert mock_helpers.bulk.call_count >= 1
    
    @unittest.mock.patch('ingest_domestic_2023.helpers')
    @unittest.mock.patch('builtins.open')
    def test_ingest_certificates_existing_index(self, mock_open, mock_helpers):
        """Test ingestion when index already exists."""
        # Mock OpenSearch client with existing index
        mock_client = unittest.mock.MagicMock()
        mock_client.indices.exists.return_value = True
        
        # Mock empty CSV
        mock_reader = unittest.mock.MagicMock()
        mock_reader.__iter__ = unittest.mock.MagicMock(return_value=iter([]))
        
        with unittest.mock.patch('csv.DictReader', return_value=mock_reader):
            schema = {'columns': {}, 'primaryKey': None}
            
            ingest_certificates(mock_client, 'test.csv', schema, 'existing-index')
            
            # Verify index creation was not called
            mock_client.indices.exists.assert_called_once_with(index='existing-index')
            mock_client.indices.create.assert_not_called()


class TestMainFunction:
    """Test the main function and argument parsing."""
    
    @unittest.mock.patch('ingest_domestic_2023.ingest_certificates')
    @unittest.mock.patch('ingest_domestic_2023.build_properties_index_from_certificates')
    @unittest.mock.patch('ingest_domestic_2023.OpenSearch')
    @unittest.mock.patch('ingest_domestic_2023.load_schema')
    @unittest.mock.patch('os.path.exists')
    def test_main_basic_args(self, mock_exists, mock_load_schema, mock_opensearch, 
                           mock_build_props, mock_ingest):
        """Test main function with basic arguments."""
        mock_exists.return_value = True
        mock_load_schema.return_value = {'columns': {}, 'primaryKey': None}
        mock_client = unittest.mock.MagicMock()
        mock_opensearch.return_value = mock_client
        
        # Test basic run without properties index
        main(['--csv', 'test.csv', '--schema', 'test.json'])
        
        mock_load_schema.assert_called_once()
        mock_opensearch.assert_called_once()
        mock_ingest.assert_called_once()
        mock_build_props.assert_not_called()
    
    @unittest.mock.patch('ingest_domestic_2023.ingest_certificates')
    @unittest.mock.patch('ingest_domestic_2023.build_properties_index_from_certificates')
    @unittest.mock.patch('ingest_domestic_2023.OpenSearch')
    @unittest.mock.patch('ingest_domestic_2023.load_schema')
    @unittest.mock.patch('os.path.exists')
    def test_main_with_properties(self, mock_exists, mock_load_schema, mock_opensearch,
                                mock_build_props, mock_ingest):
        """Test main function with properties index building."""
        mock_exists.return_value = True
        mock_load_schema.return_value = {'columns': {}, 'primaryKey': None}
        mock_client = unittest.mock.MagicMock()
        mock_opensearch.return_value = mock_client
        
        # Test with properties index building
        main(['--csv', 'test.csv', '--schema', 'test.json', '--build-properties'])
        
        mock_ingest.assert_called_once()
        mock_build_props.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])