#!/usr/bin/env python3
"""
Example script demonstrating how to use build_property_index.py

This example shows:
1. How to create sample certificate data
2. How to use the property index builder programmatically
3. How to query the resulting property index
"""

import json
from datetime import datetime
from opensearchpy import OpenSearch

from build_property_index import (
    extract_address,
    extract_latest_epc,
    extract_epc_summary,
    build_property_document
)


def example_extract_address():
    """Example: Extract address from a certificate."""
    print("\n=== Example: Extract Address ===")

    cert = {
        'ADDRESS1': '12 Rosevale Gardens',
        'ADDRESS2': 'Piddington',
        'ADDRESS3': 'High Wycombe',
        'POSTCODE': 'HP13 3HH',
        'location': {'lat': 51.501, 'lon': -0.141}
    }

    address = extract_address(cert)
    print(json.dumps(address, indent=2))


def example_extract_latest_epc():
    """Example: Extract latest EPC information."""
    print("\n=== Example: Extract Latest EPC ===")

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
        'PHOTO_SUPPLY': 25.0,
        'SOLAR_WATER_HEATING_FLAG': 'N',
        'HEATING_COST_CURRENT': 800.0,
        'HOT_WATER_COST_CURRENT': 350.0,
        'LIGHTING_COST_CURRENT': 200.0
    }

    latest_epc = extract_latest_epc(cert)
    print(json.dumps(latest_epc, indent=2, default=str))


def example_build_property_document():
    """Example: Build a complete property document."""
    print("\n=== Example: Build Property Document ===")

    # Multiple certificates for the same property (sorted newest first)
    certificates = [
        {
            'LMK_KEY': 'newest123',
            'ADDRESS1': '12 Rosevale Gardens',
            'ADDRESS2': 'Piddington',
            'ADDRESS3': 'High Wycombe',
            'POSTCODE': 'HP13 3HH',
            'CURRENT_ENERGY_RATING': 'B',
            'CURRENT_ENERGY_EFFICIENCY': 85,
            'INSPECTION_DATE': '2024-09-10',
            'LODGEMENT_DATE': '2024-09-15',
            'PROPERTY_TYPE': 'House',
            'BUILT_FORM': 'Semi-Detached',
            'MAINHEAT_DESCRIPTION': 'Air Source Heat Pump',
            'WALLS_DESCRIPTION': 'Cavity filled',
            'PHOTO_SUPPLY': 25.0,
            'HEATING_COST_CURRENT': 800.0,
            'HOT_WATER_COST_CURRENT': 350.0,
            'LIGHTING_COST_CURRENT': 200.0,
            'location': {'lat': 51.501, 'lon': -0.141}
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

    property_doc = build_property_document('123456789', certificates)
    print(json.dumps(property_doc, indent=2, default=str))


def example_query_properties():
    """Example: Query the properties index."""
    print("\n=== Example: Query Properties Index ===")

    # This example assumes OpenSearch is running and properties index exists
    # Uncomment to run against a real OpenSearch instance

    """
    client = OpenSearch(
        ['http://localhost:9200'],
        http_auth=('admin', 'admin'),
        use_ssl=False
    )

    # Query 1: Find properties with high energy ratings
    query = {
        'query': {
            'term': {'latest_epc.rating.keyword': 'A'}
        },
        'size': 10
    }

    result = client.search(index='domestic-2023-properties', body=query)
    print(f"Found {result['hits']['total']['value']} properties with rating A")

    # Query 2: Find properties with solar panels
    query = {
        'query': {
            'term': {'latest_epc.solar_panels': True}
        },
        'size': 10
    }

    result = client.search(index='domestic-2023-properties', body=query)
    print(f"Found {result['hits']['total']['value']} properties with solar panels")

    # Query 3: Find properties near a location
    query = {
        'query': {
            'bool': {
                'filter': {
                    'geo_distance': {
                        'distance': '5km',
                        'location': {'lat': 51.5, 'lon': -0.1}
                    }
                }
            }
        },
        'size': 10
    }

    result = client.search(index='domestic-2023-properties', body=query)
    print(f"Found {result['hits']['total']['value']} properties within 5km")
    """

    print("Query examples (commented out - uncomment to run against OpenSearch):")
    print("1. Find properties with rating A")
    print("2. Find properties with solar panels")
    print("3. Find properties near a location (geo search)")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Property Index Builder - Usage Examples")
    print("=" * 60)

    example_extract_address()
    example_extract_latest_epc()
    example_build_property_document()
    example_query_properties()

    print("\n" + "=" * 60)
    print("For more information, see BUILD_PROPERTY_INDEX_README.md")
    print("=" * 60)


if __name__ == '__main__':
    main()
