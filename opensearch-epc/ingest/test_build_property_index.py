#!/usr/bin/env python3
"""
Tests for build_property_index.py

This test suite covers:
- Property mapping generation
- Address extraction from certificates
- Latest EPC extraction
- EPC summary extraction for historical array
- Property document building
- Integration with OpenSearch (mocked)
"""

import pytest
import unittest.mock
from datetime import datetime
from typing import Dict, Any

from build_property_index import (
    create_property_mapping,
    extract_address,
    extract_latest_epc,
    extract_epc_summary,
    build_property_document,
    fetch_all_certificates_by_uprn,
    build_properties_index,
    main
)


class TestPropertyMapping:
    """Test property index mapping generation."""

    def test_create_property_mapping(self):
        """Test creating the property index mapping."""
        mapping = create_property_mapping()

        # Check structure
        assert 'mappings' in mapping
        assert 'properties' in mapping['mappings']
        props = mapping['mappings']['properties']

        # Check key fields exist
        assert 'uprn' in props
        assert 'address' in props
        assert 'latest_epc' in props
        assert 'epcs' in props
        assert 'location' in props
        assert 'last_sale' in props
        assert 'market_info' in props
        assert 'estimated_running_cost' in props
        assert 'created_at' in props

        # Check types
        assert props['uprn']['type'] == 'keyword'
        assert props['location']['type'] == 'geo_point'
        assert props['epcs']['type'] == 'nested'
        assert props['estimated_running_cost']['type'] == 'integer'
        assert props['created_at']['type'] == 'date'

        # Check address subfields
        address_props = props['address']['properties']
        assert 'address' in address_props
        assert 'address1' in address_props
        assert 'address2' in address_props
        assert 'address3' in address_props
        assert 'postcode' in address_props
        assert 'lat' in address_props
        assert 'long' in address_props

        # Check latest_epc subfields
        latest_epc_props = props['latest_epc']['properties']
        assert 'LMK_KEY' in latest_epc_props
        assert 'rating' in latest_epc_props
        assert 'score' in latest_epc_props
        assert 'inspection_date' in latest_epc_props
        assert 'solar_panels' in latest_epc_props
        assert 'wall_insulation' in latest_epc_props


class TestAddressExtraction:
    """Test address extraction from certificates."""

    def test_extract_address_complete(self):
        """Test extracting a complete address."""
        cert = {
            'ADDRESS1': '12 Rosevale Gardens',
            'ADDRESS2': 'Piddington',
            'ADDRESS3': 'High Wycombe',
            'POSTCODE': 'HP13 3HH'
        }

        address = extract_address(cert)

        assert address['address1'] == '12 Rosevale Gardens'
        assert address['address2'] == 'Piddington'
        assert address['address3'] == 'High Wycombe'
        assert address['postcode'] == 'HP13 3HH'
        assert address['address'] == '12 Rosevale Gardens, Piddington, High Wycombe, HP13 3HH'

    def test_extract_address_partial(self):
        """Test extracting a partial address (missing some fields)."""
        cert = {
            'ADDRESS1': '123 Main Street',
            'ADDRESS2': '',
            'ADDRESS3': 'London',
            'POSTCODE': 'SW1A 1AA'
        }

        address = extract_address(cert)

        assert address['address1'] == '123 Main Street'
        assert address['address2'] == ''
        assert address['address3'] == 'London'
        assert address['postcode'] == 'SW1A 1AA'
        # Empty address2 should be excluded from full address
        assert address['address'] == '123 Main Street, London, SW1A 1AA'

    def test_extract_address_with_location_dict(self):
        """Test extracting address with location as dict."""
        cert = {
            'ADDRESS1': '123 Test St',
            'POSTCODE': 'AB12 3CD',
            'location': {'lat': 51.501, 'lon': -0.141}
        }

        address = extract_address(cert)

        assert address['lat'] == 51.501
        assert address['long'] == -0.141

    def test_extract_address_with_location_string(self):
        """Test extracting address with location as string."""
        cert = {
            'ADDRESS1': '123 Test St',
            'POSTCODE': 'AB12 3CD',
            'location': '51.501,-0.141'
        }

        address = extract_address(cert)

        assert address['lat'] == 51.501
        assert address['long'] == -0.141

    def test_extract_address_no_location(self):
        """Test extracting address without location."""
        cert = {
            'ADDRESS1': '123 Test St',
            'POSTCODE': 'AB12 3CD'
        }

        address = extract_address(cert)

        assert 'lat' not in address or address.get('lat') is None
        assert 'long' not in address or address.get('long') is None


class TestLatestEPCExtraction:
    """Test latest EPC extraction from certificates."""

    def test_extract_latest_epc_complete(self):
        """Test extracting complete latest EPC data."""
        cert = {
            'LMK_KEY': '4938aef',
            'CURRENT_ENERGY_RATING': 'B',
            'CURRENT_ENERGY_EFFICIENCY': 85,
            'INSPECTION_DATE': '2024-09-10',
            'LODGEMENT_DATE': '2024-09-15',
            'PROPERTY_TYPE': 'House',
            'BUILT_FORM': 'Semi-Detached',
            'CONSTRUCTION_AGE_BAND': '1983-1990',
            'TOTAL_FLOOR_AREA': 125.5,
            'MAINHEAT_DESCRIPTION': 'Air Source Heat Pump',
            'WALLS_DESCRIPTION': 'Cavity filled',
            'ROOF_DESCRIPTION': 'Insulated to modern standards',
            'WINDOWS_DESCRIPTION': 'Double glazed',
            'MAIN_FUEL': 'Electricity',
            'WIND_TURBINE_COUNT': 0,
            'CO2_EMISSIONS_CURRENT': 1.5,
            'ENERGY_CONSUMPTION_CURRENT': 250.0,
            'HEATING_COST_CURRENT': 800.0,
            'HOT_WATER_COST_CURRENT': 350.0,
            'LIGHTING_COST_CURRENT': 200.0,
            'PHOTO_SUPPLY': 25.0,
            'SOLAR_WATER_HEATING_FLAG': 'N'
        }

        latest_epc = extract_latest_epc(cert)

        assert latest_epc['LMK_KEY'] == '4938aef'
        assert latest_epc['rating'] == 'B'
        assert latest_epc['score'] == 85
        assert latest_epc['inspection_date'] == '2024-09-10'
        assert latest_epc['lodgement_date'] == '2024-09-15'
        assert latest_epc['property_type'] == 'House'
        assert latest_epc['built_form'] == 'Semi-Detached'
        assert latest_epc['construction_age_band'] == '1983-1990'
        assert latest_epc['total_floor_area'] == 125.5
        assert latest_epc['heating_type'] == 'Air Source Heat Pump'
        assert latest_epc['solar_panels'] is True  # PHOTO_SUPPLY > 0
        assert latest_epc['solar_water_heating'] is False
        assert latest_epc['wall_insulation'] == 'Cavity filled'

    def test_extract_latest_epc_solar_panels_detection(self):
        """Test solar panel detection logic."""
        # Test with solar panels
        cert_with_solar = {'PHOTO_SUPPLY': 30}
        epc = extract_latest_epc(cert_with_solar)
        assert epc['solar_panels'] is True

        # Test without solar panels
        cert_no_solar = {'PHOTO_SUPPLY': 0}
        epc = extract_latest_epc(cert_no_solar)
        assert epc['solar_panels'] is False

        # Test with missing PHOTO_SUPPLY
        cert_missing = {}
        epc = extract_latest_epc(cert_missing)
        assert epc['solar_panels'] is False

    def test_extract_latest_epc_solar_water_heating_detection(self):
        """Test solar water heating detection logic."""
        # Test various positive values
        for value in ['Y', 'YES', 'yes', 'y', 'True', 'TRUE']:
            cert = {'SOLAR_WATER_HEATING_FLAG': value}
            epc = extract_latest_epc(cert)
            assert epc['solar_water_heating'] is True

        # Test negative values
        for value in ['N', 'NO', 'no', 'False', '']:
            cert = {'SOLAR_WATER_HEATING_FLAG': value}
            epc = extract_latest_epc(cert)
            assert epc['solar_water_heating'] is False


class TestEPCSummaryExtraction:
    """Test EPC summary extraction for historical array."""

    def test_extract_epc_summary(self):
        """Test extracting EPC summary with key fields."""
        cert = {
            'LMK_KEY': 'ab928437e',
            'CURRENT_ENERGY_RATING': 'D',
            'CURRENT_ENERGY_EFFICIENCY': 60,
            'INSPECTION_DATE': '2015-04-02',
            'LODGEMENT_DATE': '2015-04-10',
            # Other fields should be ignored
            'PROPERTY_TYPE': 'House',
            'WALLS_DESCRIPTION': 'Cavity insulation'
        }

        summary = extract_epc_summary(cert)

        # Should only include key fields
        assert summary['LMK_KEY'] == 'ab928437e'
        assert summary['rating'] == 'D'
        assert summary['score'] == 60
        assert summary['inspection_date'] == '2015-04-02'
        assert summary['lodgement_date'] == '2015-04-10'

        # Should not include detailed fields
        assert 'property_type' not in summary
        assert 'walls_description' not in summary


class TestPropertyDocumentBuilding:
    """Test building complete property documents."""

    def test_build_property_document_single_cert(self):
        """Test building a property document with a single certificate."""
        uprn = '123456789'
        cert = {
            'LMK_KEY': '4938aef',
            'ADDRESS1': '12 Rosevale Gardens',
            'ADDRESS2': 'Piddington',
            'ADDRESS3': 'High Wycombe',
            'POSTCODE': 'HP13 3HH',
            'CURRENT_ENERGY_RATING': 'B',
            'CURRENT_ENERGY_EFFICIENCY': 85,
            'INSPECTION_DATE': '2024-09-10',
            'LODGEMENT_DATE': '2024-09-15',
            'PROPERTY_TYPE': 'House',
            'HEATING_COST_CURRENT': 800.0,
            'HOT_WATER_COST_CURRENT': 350.0,
            'LIGHTING_COST_CURRENT': 200.0
        }

        prop_doc = build_property_document(uprn, [cert])

        # Check basic structure
        assert prop_doc['uprn'] == uprn
        assert 'address' in prop_doc
        assert 'latest_epc' in prop_doc
        assert 'epcs' in prop_doc
        assert 'created_at' in prop_doc

        # Check address
        assert prop_doc['address']['address1'] == '12 Rosevale Gardens'
        assert prop_doc['address']['postcode'] == 'HP13 3HH'

        # Check latest_epc
        assert prop_doc['latest_epc']['LMK_KEY'] == '4938aef'
        assert prop_doc['latest_epc']['rating'] == 'B'
        assert prop_doc['latest_epc']['score'] == 85

        # Check epcs array
        assert len(prop_doc['epcs']) == 1
        assert prop_doc['epcs'][0]['LMK_KEY'] == '4938aef'

        # Check estimated running cost
        assert 'estimated_running_cost' in prop_doc
        assert prop_doc['estimated_running_cost'] == 1350  # 800 + 350 + 200

    def test_build_property_document_multiple_certs(self):
        """Test building a property document with multiple certificates."""
        uprn = '123456789'
        certs = [
            {
                'LMK_KEY': 'newest123',
                'ADDRESS1': '12 Test St',
                'POSTCODE': 'AB12 3CD',
                'CURRENT_ENERGY_RATING': 'B',
                'CURRENT_ENERGY_EFFICIENCY': 85,
                'INSPECTION_DATE': '2024-09-10',
                'LODGEMENT_DATE': '2024-09-15'
            },
            {
                'LMK_KEY': 'middle456',
                'CURRENT_ENERGY_RATING': 'C',
                'CURRENT_ENERGY_EFFICIENCY': 72,
                'INSPECTION_DATE': '2019-08-01',
                'LODGEMENT_DATE': '2019-08-05'
            },
            {
                'LMK_KEY': 'oldest789',
                'CURRENT_ENERGY_RATING': 'D',
                'CURRENT_ENERGY_EFFICIENCY': 60,
                'INSPECTION_DATE': '2015-04-02',
                'LODGEMENT_DATE': '2015-04-10'
            }
        ]

        prop_doc = build_property_document(uprn, certs)

        # Latest EPC should be from first (newest) certificate
        assert prop_doc['latest_epc']['LMK_KEY'] == 'newest123'
        assert prop_doc['latest_epc']['rating'] == 'B'

        # EPCs array should contain all certificates
        assert len(prop_doc['epcs']) == 3
        assert prop_doc['epcs'][0]['LMK_KEY'] == 'newest123'
        assert prop_doc['epcs'][1]['LMK_KEY'] == 'middle456'
        assert prop_doc['epcs'][2]['LMK_KEY'] == 'oldest789'

    def test_build_property_document_empty_certs(self):
        """Test building property document with empty certificates list."""
        prop_doc = build_property_document('12345', [])
        assert prop_doc is None

    def test_build_property_document_with_location(self):
        """Test building property document with geo location."""
        cert = {
            'LMK_KEY': 'test123',
            'ADDRESS1': '123 Test St',
            'POSTCODE': 'AB12 3CD',
            'CURRENT_ENERGY_RATING': 'C',
            'CURRENT_ENERGY_EFFICIENCY': 70,
            'location': {'lat': 51.5, 'lon': -0.1}
        }

        prop_doc = build_property_document('12345', [cert])

        assert 'location' in prop_doc
        assert prop_doc['location'] == {'lat': 51.5, 'lon': -0.1}


class TestFetchCertificates:
    """Test fetching certificates from OpenSearch."""

    def test_fetch_all_certificates_by_uprn(self):
        """Test fetching all certificates for a UPRN."""
        mock_client = unittest.mock.Mock()

        # Mock search response
        mock_response = {
            'hits': {
                'hits': [
                    {'_source': {'LMK_KEY': 'cert1', 'LODGEMENT_DATE': '2024-01-01'}},
                    {'_source': {'LMK_KEY': 'cert2', 'LODGEMENT_DATE': '2023-01-01'}}
                ]
            }
        }
        mock_client.search.return_value = mock_response

        certs = fetch_all_certificates_by_uprn(mock_client, 'test-index', '12345')

        # Check search was called with correct parameters
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert call_args[1]['index'] == 'test-index'
        assert call_args[1]['body']['query']['term']['UPRN.keyword'] == '12345'

        # Check returned certificates
        assert len(certs) == 2
        assert certs[0]['LMK_KEY'] == 'cert1'
        assert certs[1]['LMK_KEY'] == 'cert2'


class TestBuildPropertiesIndex:
    """Test the main properties index building function."""

    @unittest.mock.patch('build_property_index.fetch_all_certificates_by_uprn')
    @unittest.mock.patch('build_property_index.helpers')
    def test_build_properties_index(self, mock_helpers, mock_fetch):
        """Test building the properties index."""
        mock_client = unittest.mock.Mock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {'acknowledged': True}

        # Mock composite aggregation response
        mock_search_response = {
            'aggregations': {
                'by_uprn': {
                    'buckets': [
                        {'key': {'uprn': '12345'}},
                        {'key': {'uprn': '67890'}}
                    ],
                    'after_key': None  # No more pages
                }
            }
        }
        mock_client.search.return_value = mock_search_response

        # Mock fetching certificates
        mock_fetch.side_effect = [
            [{'LMK_KEY': 'cert1', 'ADDRESS1': 'Test St', 'CURRENT_ENERGY_RATING': 'B',
              'CURRENT_ENERGY_EFFICIENCY': 85}],
            [{'LMK_KEY': 'cert2', 'ADDRESS1': 'Demo Ave', 'CURRENT_ENERGY_RATING': 'C',
              'CURRENT_ENERGY_EFFICIENCY': 70}]
        ]

        total = build_properties_index(mock_client, 'test-certs', 'test-props', batch_size=10)

        # Verify index creation
        mock_client.indices.create.assert_called_once()

        # Verify bulk indexing was called
        assert mock_helpers.bulk.call_count >= 1

        # Verify total count
        assert total == 2

    @unittest.mock.patch('build_property_index.fetch_all_certificates_by_uprn')
    @unittest.mock.patch('build_property_index.helpers')
    def test_build_properties_index_recreates_existing(self, mock_helpers, mock_fetch):
        """Test that existing index is deleted and recreated."""
        mock_client = unittest.mock.Mock()
        mock_client.indices.exists.return_value = True
        mock_client.indices.delete.return_value = {'acknowledged': True}
        mock_client.indices.create.return_value = {'acknowledged': True}

        # Mock empty results
        mock_client.search.return_value = {
            'aggregations': {'by_uprn': {'buckets': [], 'after_key': None}}
        }

        build_properties_index(mock_client, 'test-certs', 'test-props')

        # Verify deletion and recreation
        mock_client.indices.delete.assert_called_once_with(index='test-props')
        mock_client.indices.create.assert_called_once()


class TestMainFunction:
    """Test the main function and CLI."""

    @unittest.mock.patch('build_property_index.build_properties_index')
    @unittest.mock.patch('build_property_index.OpenSearch')
    def test_main_basic(self, mock_opensearch, mock_build):
        """Test main function with basic arguments."""
        mock_client = unittest.mock.Mock()
        mock_client.indices.exists.return_value = True
        mock_opensearch.return_value = mock_client
        mock_build.return_value = 100

        result = main(['--opensearch-url', 'http://localhost:9200'])

        assert result == 0
        mock_build.assert_called_once()

    @unittest.mock.patch('build_property_index.OpenSearch')
    def test_main_missing_cert_index(self, mock_opensearch):
        """Test main function when certificates index doesn't exist."""
        mock_client = unittest.mock.Mock()
        mock_client.indices.exists.return_value = False
        mock_opensearch.return_value = mock_client

        result = main(['--opensearch-url', 'http://localhost:9200'])

        assert result == 1  # Should fail

    @unittest.mock.patch('build_property_index.build_properties_index')
    @unittest.mock.patch('build_property_index.OpenSearch')
    def test_main_custom_indices(self, mock_opensearch, mock_build):
        """Test main function with custom index names."""
        mock_client = unittest.mock.Mock()
        mock_client.indices.exists.return_value = True
        mock_opensearch.return_value = mock_client
        mock_build.return_value = 50

        result = main([
            '--cert-index', 'custom-certs',
            '--prop-index', 'custom-props'
        ])

        assert result == 0
        # Check that custom index names were used
        call_args = mock_build.call_args[0]
        assert call_args[1] == 'custom-certs'
        assert call_args[2] == 'custom-props'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
