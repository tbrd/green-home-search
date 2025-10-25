#!/usr/bin/env python3
"""
Integration test for ingest_domestic_2023.py

This test creates sample CSV and schema files to test the complete ingestion workflow
with a mock OpenSearch client.
"""

import json
import csv
import tempfile
import os
import unittest.mock
from pathlib import Path

from ingest_domestic_2023 import main


def test_integration_full_workflow():
    """Test the complete workflow with sample data files."""

    # Create sample schema
    schema_data = {
        "tables": [{
            "url": "certificates.csv",
            "tableSchema": {
                "columns": [
                    {"name": "LMK_KEY", "datatype": "string"},
                    {"name": "ADDRESS1", "datatype": "string"},
                    {"name": "ADDRESS2", "datatype": "string"},
                    {"name": "ADDRESS3", "datatype": "string"},
                    {"name": "POSTCODE", "datatype": "string"},
                    {"name": "BUILDING_REFERENCE_NUMBER", "datatype": "string"},
                    {"name": "CURRENT_ENERGY_RATING", "datatype": "string"},
                    {"name": "POTENTIAL_ENERGY_RATING", "datatype": "string"},
                    {"name": "CURRENT_ENERGY_EFFICIENCY", "datatype": "integer"},
                    {"name": "POTENTIAL_ENERGY_EFFICIENCY", "datatype": "integer"},
                    {"name": "PROPERTY_TYPE", "datatype": "string"},
                    {"name": "BUILT_FORM", "datatype": "string"},
                    {"name": "INSPECTION_DATE", "datatype": "date"},
                    {"name": "LOCAL_AUTHORITY", "datatype": "string"},
                    {"name": "CONSTITUENCY", "datatype": "string"},
                    {"name": "COUNTY", "datatype": "string"},
                    {"name": "LODGEMENT_DATE", "datatype": "date"},
                    {"name": "TRANSACTION_TYPE", "datatype": "string"},
                    {"name": "ENVIRONMENT_IMPACT_CURRENT", "datatype": "integer"},
                    {"name": "ENVIRONMENT_IMPACT_POTENTIAL", "datatype": "integer"},
                    {"name": "ENERGY_CONSUMPTION_CURRENT", "datatype": "integer"},
                    {"name": "ENERGY_CONSUMPTION_POTENTIAL", "datatype": "integer"},
                    {"name": "CO2_EMISSIONS_CURRENT", "datatype": "decimal"},
                    {"name": "CO2_EMISSIONS_POTENTIAL", "datatype": "decimal"},
                    {"name": "CO2_EMISS_CURR_PER_FLOOR_AREA", "datatype": "decimal"},
                    {"name": "LIGHTING_COST_CURRENT", "datatype": "decimal"},
                    {"name": "LIGHTING_COST_POTENTIAL", "datatype": "decimal"},
                    {"name": "HEATING_COST_CURRENT", "datatype": "decimal"},
                    {"name": "HEATING_COST_POTENTIAL", "datatype": "decimal"},
                    {"name": "HOT_WATER_COST_CURRENT", "datatype": "decimal"},
                    {"name": "HOT_WATER_COST_POTENTIAL", "datatype": "decimal"},
                    {"name": "TOTAL_FLOOR_AREA", "datatype": "decimal"},
                    {"name": "ENERGY_TARIFF", "datatype": "string"},
                    {"name": "MAINS_GAS_FLAG", "datatype": "string"},
                    {"name": "FLOOR_LEVEL", "datatype": "string"},
                    {"name": "FLAT_TOP_STOREY", "datatype": "string"},
                    {"name": "FLAT_STOREY_COUNT", "datatype": "integer"},
                    {"name": "MAIN_HEATING_CONTROLS", "datatype": "integer"},
                    {"name": "MULTI_GLAZE_PROPORTION", "datatype": "integer"},
                    {"name": "GLAZED_TYPE", "datatype": "string"},
                    {"name": "GLAZED_AREA", "datatype": "string"},
                    {"name": "EXTENSION_COUNT", "datatype": "integer"},
                    {"name": "NUMBER_HABITABLE_ROOMS", "datatype": "integer"},
                    {"name": "NUMBER_HEATED_ROOMS", "datatype": "integer"},
                    {"name": "LOW_ENERGY_LIGHTING", "datatype": "integer"},
                    {"name": "NUMBER_OPEN_FIREPLACES", "datatype": "integer"},
                    {"name": "HOTWATER_DESCRIPTION", "datatype": "string"},
                    {"name": "HOT_WATER_ENERGY_EFF", "datatype": "string"},
                    {"name": "HOT_WATER_ENV_EFF", "datatype": "string"},
                    {"name": "FLOOR_DESCRIPTION", "datatype": "string"},
                    {"name": "FLOOR_ENERGY_EFF", "datatype": "string"},
                    {"name": "FLOOR_ENV_EFF", "datatype": "string"},
                    {"name": "WINDOWS_DESCRIPTION", "datatype": "string"},
                    {"name": "WINDOWS_ENERGY_EFF", "datatype": "string"},
                    {"name": "WINDOWS_ENV_EFF", "datatype": "string"},
                    {"name": "WALLS_DESCRIPTION", "datatype": "string"},
                    {"name": "WALLS_ENERGY_EFF", "datatype": "string"},
                    {"name": "WALLS_ENV_EFF", "datatype": "string"},
                    {"name": "SECONDHEAT_DESCRIPTION", "datatype": "string"},
                    {"name": "SHEATING_ENERGY_EFF", "datatype": "string"},
                    {"name": "SHEATING_ENV_EFF", "datatype": "string"},
                    {"name": "ROOF_DESCRIPTION", "datatype": "string"},
                    {"name": "ROOF_ENERGY_EFF", "datatype": "string"},
                    {"name": "ROOF_ENV_EFF", "datatype": "string"},
                    {"name": "MAINHEAT_DESCRIPTION", "datatype": "string"},
                    {"name": "MAINHEAT_ENERGY_EFF", "datatype": "string"},
                    {"name": "MAINHEAT_ENV_EFF", "datatype": "string"},
                    {"name": "MAINHEATCONT_DESCRIPTION", "datatype": "string"},
                    {"name": "MAINHEATC_ENERGY_EFF", "datatype": "string"},
                    {"name": "MAINHEATC_ENV_EFF", "datatype": "string"},
                    {"name": "LIGHTING_DESCRIPTION", "datatype": "string"},
                    {"name": "LIGHTING_ENERGY_EFF", "datatype": "string"},
                    {"name": "LIGHTING_ENV_EFF", "datatype": "string"},
                    {"name": "MAIN_FUEL", "datatype": "string"},
                    {"name": "WIND_TURBINE_COUNT", "datatype": "integer"},
                    {"name": "HEAT_LOSS_CORRIDOR", "datatype": "string"},
                    {"name": "UNHEATED_CORRIDOR_LENGTH", "datatype": "decimal"},
                    {"name": "FLOOR_HEIGHT", "datatype": "decimal"},
                    {"name": "PHOTO_SUPPLY", "datatype": "integer"},
                    {"name": "SOLAR_WATER_HEATING_FLAG", "datatype": "string"},
                    {"name": "MECHANICAL_VENTILATION", "datatype": "string"},
                    {"name": "ADDRESS", "datatype": "string"},
                    {"name": "LOCAL_AUTHORITY_LABEL", "datatype": "string"},
                    {"name": "CONSTITUENCY_LABEL", "datatype": "string"},
                    {"name": "POSTTOWN", "datatype": "string"},
                    {"name": "CONSTRUCTION_AGE_BAND", "datatype": "string"},
                    {"name": "LODGEMENT_DATETIME", "datatype": "datetime"},
                    {"name": "TENURE", "datatype": "string"},
                    {"name": "FIXED_LIGHTING_OUTLETS_COUNT", "datatype": "integer"},
                    {"name": "LOW_ENERGY_FIXED_LIGHT_COUNT", "datatype": "integer"},
                    {"name": "UPRN", "datatype": "string"},
                    {"name": "UPRN_SOURCE", "datatype": "string"}
                ],
                "primaryKey": "LMK_KEY"
            }
        }]
    }

    # Create sample CSV data
    csv_data = [
        {
            "LMK_KEY": "123456789",
            "ADDRESS1": "123 Test Street",
            "ADDRESS2": "",
            "ADDRESS3": "",
            "POSTCODE": "SW1A 1AA",
            "BUILDING_REFERENCE_NUMBER": "12345",
            "CURRENT_ENERGY_RATING": "C",
            "POTENTIAL_ENERGY_RATING": "B",
            "CURRENT_ENERGY_EFFICIENCY": "72",
            "POTENTIAL_ENERGY_EFFICIENCY": "83",
            "PROPERTY_TYPE": "House",
            "BUILT_FORM": "Detached",
            "INSPECTION_DATE": "2023-01-15",
            "LOCAL_AUTHORITY": "E09000033",
            "CONSTITUENCY": "E14000639",
            "COUNTY": "E99999999",
            "LODGEMENT_DATE": "2023-01-20",
            "TRANSACTION_TYPE": "marketed sale",
            "ENVIRONMENT_IMPACT_CURRENT": "70",
            "ENVIRONMENT_IMPACT_POTENTIAL": "80",
            "ENERGY_CONSUMPTION_CURRENT": "250",
            "ENERGY_CONSUMPTION_POTENTIAL": "200",
            "CO2_EMISSIONS_CURRENT": "4.5",
            "CO2_EMISSIONS_POTENTIAL": "3.8",
            "CO2_EMISS_CURR_PER_FLOOR_AREA": "45.0",
            "LIGHTING_COST_CURRENT": "120.0",
            "LIGHTING_COST_POTENTIAL": "95.0",
            "HEATING_COST_CURRENT": "800.0",
            "HEATING_COST_POTENTIAL": "650.0",
            "HOT_WATER_COST_CURRENT": "180.0",
            "HOT_WATER_COST_POTENTIAL": "150.0",
            "TOTAL_FLOOR_AREA": "100.0",
            "ENERGY_TARIFF": "Single",
            "MAINS_GAS_FLAG": "Y",
            "FLOOR_LEVEL": "01",
            "FLAT_TOP_STOREY": "N",
            "FLAT_STOREY_COUNT": "2",
            "MAIN_HEATING_CONTROLS": "2104",
            "MULTI_GLAZE_PROPORTION": "100",
            "GLAZED_TYPE": "double glazing throughout",
            "GLAZED_AREA": "Normal",
            "EXTENSION_COUNT": "0",
            "NUMBER_HABITABLE_ROOMS": "5",
            "NUMBER_HEATED_ROOMS": "5",
            "LOW_ENERGY_LIGHTING": "100",
            "NUMBER_OPEN_FIREPLACES": "0",
            "HOTWATER_DESCRIPTION": "From main system",
            "HOT_WATER_ENERGY_EFF": "Good",
            "HOT_WATER_ENV_EFF": "Good",
            "FLOOR_DESCRIPTION": "Solid, insulated (assumed)",
            "FLOOR_ENERGY_EFF": "Good",
            "FLOOR_ENV_EFF": "Good",
            "WINDOWS_DESCRIPTION": "Fully double glazed",
            "WINDOWS_ENERGY_EFF": "Good",
            "WINDOWS_ENV_EFF": "Good",
            "WALLS_DESCRIPTION": "Cavity wall, as built, insulated (assumed)",
            "WALLS_ENERGY_EFF": "Good",
            "WALLS_ENV_EFF": "Good",
            "SECONDHEAT_DESCRIPTION": "None",
            "SHEATING_ENERGY_EFF": "N/A",
            "SHEATING_ENV_EFF": "N/A",
            "ROOF_DESCRIPTION": "Pitched, 150 mm loft insulation",
            "ROOF_ENERGY_EFF": "Good",
            "ROOF_ENV_EFF": "Good",
            "MAINHEAT_DESCRIPTION": "Boiler and radiators, mains gas",
            "MAINHEAT_ENERGY_EFF": "Good",
            "MAINHEAT_ENV_EFF": "Good",
            "MAINHEATCONT_DESCRIPTION": "Programmer, room thermostat and TRVs",
            "MAINHEATC_ENERGY_EFF": "Good",
            "MAINHEATC_ENV_EFF": "Good",
            "LIGHTING_DESCRIPTION": "100% low energy lighting",
            "LIGHTING_ENERGY_EFF": "Very Good",
            "LIGHTING_ENV_EFF": "Very Good",
            "MAIN_FUEL": "mains gas",
            "WIND_TURBINE_COUNT": "0",
            "HEAT_LOSS_CORRIDOR": "No",
            "UNHEATED_CORRIDOR_LENGTH": "0.0",
            "FLOOR_HEIGHT": "2.45",
            "PHOTO_SUPPLY": "0",
            "SOLAR_WATER_HEATING_FLAG": "N",
            "MECHANICAL_VENTILATION": "natural",
            "ADDRESS": "123 Test Street, London",
            "LOCAL_AUTHORITY_LABEL": "Westminster",
            "CONSTITUENCY_LABEL": "Cities of London and Westminster",
            "POSTTOWN": "LONDON",
            "CONSTRUCTION_AGE_BAND": "1996-2002",
            "LODGEMENT_DATETIME": "2023-01-20 10:30:00",
            "TENURE": "Owner-occupied",
            "FIXED_LIGHTING_OUTLETS_COUNT": "10",
            "LOW_ENERGY_FIXED_LIGHT_COUNT": "10",
            "UPRN": "123456789012",
            "UPRN_SOURCE": "Address matched from ONS UPRN Directory"
        },
        {
            "LMK_KEY": "987654321",
            "ADDRESS1": "456 Demo Avenue",
            "ADDRESS2": "Flat 2",
            "ADDRESS3": "",
            "POSTCODE": "M1 1AA",
            "BUILDING_REFERENCE_NUMBER": "67890",
            "CURRENT_ENERGY_RATING": "D",
            "POTENTIAL_ENERGY_RATING": "C",
            "CURRENT_ENERGY_EFFICIENCY": "55",
            "POTENTIAL_ENERGY_EFFICIENCY": "70",
            "PROPERTY_TYPE": "Flat",
            "BUILT_FORM": "Mid-terrace",
            "INSPECTION_DATE": "2023-02-10",
            "LOCAL_AUTHORITY": "E08000003",
            "CONSTITUENCY": "E14000807",
            "COUNTY": "E99999999",
            "LODGEMENT_DATE": "2023-02-15",
            "TRANSACTION_TYPE": "rental (social)",
            "ENVIRONMENT_IMPACT_CURRENT": "50",
            "ENVIRONMENT_IMPACT_POTENTIAL": "65",
            "ENERGY_CONSUMPTION_CURRENT": "320",
            "ENERGY_CONSUMPTION_POTENTIAL": "250",
            "CO2_EMISSIONS_CURRENT": "5.8",
            "CO2_EMISSIONS_POTENTIAL": "4.2",
            "CO2_EMISS_CURR_PER_FLOOR_AREA": "87.0",
            "LIGHTING_COST_CURRENT": "150.0",
            "LIGHTING_COST_POTENTIAL": "120.0",
            "HEATING_COST_CURRENT": "950.0",
            "HEATING_COST_POTENTIAL": "750.0",
            "HOT_WATER_COST_CURRENT": "220.0",
            "HOT_WATER_COST_POTENTIAL": "180.0",
            "TOTAL_FLOOR_AREA": "67.0",
            "ENERGY_TARIFF": "Single",
            "MAINS_GAS_FLAG": "Y",
            "FLOOR_LEVEL": "02",
            "FLAT_TOP_STOREY": "N",
            "FLAT_STOREY_COUNT": "3",
            "MAIN_HEATING_CONTROLS": "2103",
            "MULTI_GLAZE_PROPORTION": "50",
            "GLAZED_TYPE": "partial double glazing",
            "GLAZED_AREA": "Normal",
            "EXTENSION_COUNT": "0",
            "NUMBER_HABITABLE_ROOMS": "3",
            "NUMBER_HEATED_ROOMS": "3",
            "LOW_ENERGY_LIGHTING": "50",
            "NUMBER_OPEN_FIREPLACES": "0",
            "HOTWATER_DESCRIPTION": "From main system",
            "HOT_WATER_ENERGY_EFF": "Average",
            "HOT_WATER_ENV_EFF": "Average",
            "FLOOR_DESCRIPTION": "Solid, no insulation (assumed)",
            "FLOOR_ENERGY_EFF": "Poor",
            "FLOOR_ENV_EFF": "Poor",
            "WINDOWS_DESCRIPTION": "Partial double glazing",
            "WINDOWS_ENERGY_EFF": "Average",
            "WINDOWS_ENV_EFF": "Average",
            "WALLS_DESCRIPTION": "Cavity wall, as built, no insulation (assumed)",
            "WALLS_ENERGY_EFF": "Poor",
            "WALLS_ENV_EFF": "Poor",
            "SECONDHEAT_DESCRIPTION": "None",
            "SHEATING_ENERGY_EFF": "N/A",
            "SHEATING_ENV_EFF": "N/A",
            "ROOF_DESCRIPTION": "Pitched, no insulation (assumed)",
            "ROOF_ENERGY_EFF": "Very Poor",
            "ROOF_ENV_EFF": "Very Poor",
            "MAINHEAT_DESCRIPTION": "Boiler and radiators, mains gas",
            "MAINHEAT_ENERGY_EFF": "Average",
            "MAINHEAT_ENV_EFF": "Average",
            "MAINHEATCONT_DESCRIPTION": "Programmer and room thermostat",
            "MAINHEATC_ENERGY_EFF": "Average",
            "MAINHEATC_ENV_EFF": "Average",
            "LIGHTING_DESCRIPTION": "50% low energy lighting",
            "LIGHTING_ENERGY_EFF": "Average",
            "LIGHTING_ENV_EFF": "Average",
            "MAIN_FUEL": "mains gas",
            "WIND_TURBINE_COUNT": "0",
            "HEAT_LOSS_CORRIDOR": "No",
            "UNHEATED_CORRIDOR_LENGTH": "0.0",
            "FLOOR_HEIGHT": "2.40",
            "PHOTO_SUPPLY": "0",
            "SOLAR_WATER_HEATING_FLAG": "N",
            "MECHANICAL_VENTILATION": "natural",
            "ADDRESS": "456 Demo Avenue, Flat 2, Manchester",
            "LOCAL_AUTHORITY_LABEL": "Manchester",
            "CONSTITUENCY_LABEL": "Manchester Central",
            "POSTTOWN": "MANCHESTER",
            "CONSTRUCTION_AGE_BAND": "1967-1975",
            "LODGEMENT_DATETIME": "2023-02-15 14:45:00",
            "TENURE": "Rental (social)",
            "FIXED_LIGHTING_OUTLETS_COUNT": "8",
            "LOW_ENERGY_FIXED_LIGHT_COUNT": "4",
            "UPRN": "987654321098",
            "UPRN_SOURCE": "Address matched from ONS UPRN Directory"
        }
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        # Write schema file
        schema_file = Path(temp_dir) / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f, indent=2)

        # Write CSV file
        csv_file = Path(temp_dir) / "certificates.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

        # Mock OpenSearch client and all its methods
        with unittest.mock.patch('ingest_domestic_2023.OpenSearch') as mock_opensearch_class:
            mock_client = unittest.mock.MagicMock()
            mock_opensearch_class.return_value = mock_client

            # Mock indices operations
            mock_client.indices.exists.return_value = False
            mock_client.indices.create.return_value = {'acknowledged': True}

            # Mock bulk operations
            with unittest.mock.patch('ingest_domestic_2023.helpers') as mock_helpers:
                mock_helpers.bulk.return_value = (2, [])  # Success response

                # Test basic ingestion
                args = [
                    '--csv', str(csv_file),
                    '--schema', str(schema_file),
                    '--index-certificates', 'test-certificates',
                    '--batch-size', '1',
                    '--opensearch-url', 'http://localhost:9200',
                    '--user', 'admin',
                    '--password', 'admin'
                ]

                # Run main function
                main(args)

                # Verify OpenSearch client was created with correct parameters
                mock_opensearch_class.assert_called_once_with(
                    ['http://localhost:9200'],
                    http_auth=('admin', 'admin')
                )

                # Verify index creation was attempted
                mock_client.indices.exists.assert_called_with(index='test-certificates')
                mock_client.indices.create.assert_called_once()

                # Verify bulk operations were called (should be called twice due to batch_size=1)
                assert mock_helpers.bulk.call_count >= 2

                # Check that the bulk actions contain the correct data
                call_args_list = mock_helpers.bulk.call_args_list
                for call_args in call_args_list:
                    client, actions = call_args[0]
                    assert client == mock_client
                    assert isinstance(actions, list)
                    assert len(actions) > 0

                    # Check first action structure
                    action = actions[0]
                    assert '_index' in action
                    assert '_source' in action
                    assert '_id' in action  # Should use LMK_KEY as ID
                    assert action['_index'] == 'test-certificates'

                    # Check that data was parsed correctly
                    source = action['_source']
                    assert 'LMK_KEY' in source
                    assert 'CURRENT_ENERGY_EFFICIENCY' in source
                    assert isinstance(source['CURRENT_ENERGY_EFFICIENCY'], int)  # Should be parsed as integer
                    assert 'TOTAL_FLOOR_AREA' in source
                    assert isinstance(source['TOTAL_FLOOR_AREA'], float)  # Should be parsed as float


def test_integration_with_properties_index():
    """Test the complete workflow including properties index building."""

    # Minimal schema for this test
    schema_data = {
        "tables": [{
            "tableSchema": {
                "columns": [
                    {"name": "LMK_KEY", "datatype": "string"},
                    {"name": "UPRN", "datatype": "string"},
                    {"name": "INSPECTION_DATE", "datatype": "date"},
                    {"name": "ADDRESS", "datatype": "string"}
                ],
                "primaryKey": "LMK_KEY"
            }
        }]
    }

    csv_data = [
        {
            "LMK_KEY": "123",
            "UPRN": "1000",
            "INSPECTION_DATE": "2023-01-15",
            "ADDRESS": "123 Test St"
        }
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        schema_file = Path(temp_dir) / "schema.json"
        csv_file = Path(temp_dir) / "certificates.csv"

        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)

        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

        with unittest.mock.patch('ingest_domestic_2023.OpenSearch') as mock_opensearch_class:
            mock_client = unittest.mock.MagicMock()
            mock_opensearch_class.return_value = mock_client
            mock_client.indices.exists.return_value = False
            mock_client.indices.create.return_value = {'acknowledged': True}

            # Mock search for properties index building
            mock_client.search.return_value = {
                'aggregations': {
                    'by_uprn': {
                        'buckets': [],
                        'after_key': None
                    }
                }
            }

            with unittest.mock.patch('ingest_domestic_2023.helpers') as mock_helpers:
                mock_helpers.bulk.return_value = (1, [])

                args = [
                    '--csv', str(csv_file),
                    '--schema', str(schema_file),
                    '--build-properties',  # Enable properties index building
                    '--index-certificates', 'test-certs',
                    '--index-properties', 'test-props'
                ]

                main(args)

                # Verify both indices were created
                assert mock_client.indices.create.call_count == 2  # certificates + properties


if __name__ == '__main__':
    test_integration_full_workflow()
    test_integration_with_properties_index()
    print("All integration tests passed!")
