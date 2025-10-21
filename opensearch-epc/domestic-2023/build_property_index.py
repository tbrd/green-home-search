#!/usr/bin/env python3
"""
Build a property index from the certificates index in OpenSearch.

This script creates a properties index where each document represents a unique property
(identified by UPRN) with:
- Address information
- Latest EPC certificate details
- Historical EPC certificates array
- Additional property metadata

Usage:
    python build_property_index.py --opensearch-url http://localhost:9200 --user admin --password admin

Environment variables:
    OPENSEARCH_URL - OpenSearch endpoint URL
    OPENSEARCH_USER - OpenSearch username
    OPENSEARCH_PASS - OpenSearch password
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from opensearchpy import OpenSearch, helpers


def create_property_mapping() -> Dict[str, Any]:
    """
    Create the OpenSearch mapping for the properties index.
    
    Returns:
        Mapping configuration for the properties index
    """
    return {
        'mappings': {
            'properties': {
                'uprn': {'type': 'keyword'},
                'address': {
                    'properties': {
                        'address': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'address1': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'address2': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'address3': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'postcode': {'type': 'keyword'},
                        'lat': {'type': 'float'},
                        'long': {'type': 'float'}
                    }
                },
                'location': {'type': 'geo_point'},
                'latest_epc': {
                    'properties': {
                        'LMK_KEY': {'type': 'keyword'},
                        'rating': {'type': 'keyword'},
                        'score': {'type': 'integer'},
                        'inspection_date': {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd'},
                        'lodgement_date': {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd'},
                        'property_type': {'type': 'keyword'},
                        'built_form': {'type': 'keyword'},
                        'construction_age_band': {'type': 'keyword'},
                        'total_floor_area': {'type': 'float'},
                        'heating_type': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'solar_panels': {'type': 'boolean'},
                        'solar_water_heating': {'type': 'boolean'},
                        'wall_insulation': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'roof_description': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'windows_description': {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}},
                        'main_fuel': {'type': 'keyword'},
                        'wind_turbine_count': {'type': 'integer'},
                        'co2_emissions_current': {'type': 'float'},
                        'energy_consumption_current': {'type': 'float'},
                        'heating_cost_current': {'type': 'float'},
                        'hot_water_cost_current': {'type': 'float'},
                        'lighting_cost_current': {'type': 'float'}
                    }
                },
                'epcs': {
                    'type': 'nested',
                    'properties': {
                        'LMK_KEY': {'type': 'keyword'},
                        'rating': {'type': 'keyword'},
                        'score': {'type': 'integer'},
                        'inspection_date': {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd'},
                        'lodgement_date': {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd'}
                    }
                },
                'last_sale': {
                    'properties': {
                        'price': {'type': 'integer'},
                        'date': {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd'}
                    }
                },
                'market_info': {
                    'properties': {
                        'estimated_value': {'type': 'integer'},
                        'avg_local_price': {'type': 'integer'},
                        'valuation_source': {'type': 'keyword'}
                    }
                },
                'estimated_running_cost': {'type': 'integer'},
                'created_at': {'type': 'date'}
            }
        }
    }


def extract_address(cert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract address information from a certificate.
    
    Args:
        cert: Certificate document from OpenSearch
        
    Returns:
        Address object with structured fields
    """
    address = {
        'address1': cert.get('ADDRESS1', ''),
        'address2': cert.get('ADDRESS2', ''),
        'address3': cert.get('ADDRESS3', ''),
        'postcode': cert.get('POSTCODE', '')
    }
    
    # Build full address from components
    parts = [address['address1'], address['address2'], address['address3'], address['postcode']]
    address['address'] = ', '.join([p for p in parts if p])
    
    # Extract location if available
    if 'location' in cert and cert['location']:
        loc = cert['location']
        if isinstance(loc, dict):
            address['lat'] = loc.get('lat')
            address['long'] = loc.get('lon')
        elif isinstance(loc, str):
            # Handle "lat,lon" string format
            try:
                parts = loc.split(',')
                if len(parts) == 2:
                    address['lat'] = float(parts[0])
                    address['long'] = float(parts[1])
            except (ValueError, AttributeError):
                pass
    
    return address


def extract_latest_epc(cert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract latest EPC information from the most recent certificate.
    
    Args:
        cert: Certificate document from OpenSearch
        
    Returns:
        Latest EPC object with key fields
    """
    latest_epc = {
        'LMK_KEY': cert.get('LMK_KEY'),
        'rating': cert.get('CURRENT_ENERGY_RATING'),
        'score': cert.get('CURRENT_ENERGY_EFFICIENCY'),
        'inspection_date': cert.get('INSPECTION_DATE'),
        'lodgement_date': cert.get('LODGEMENT_DATE'),
        'property_type': cert.get('PROPERTY_TYPE'),
        'built_form': cert.get('BUILT_FORM'),
        'construction_age_band': cert.get('CONSTRUCTION_AGE_BAND'),
        'total_floor_area': cert.get('TOTAL_FLOOR_AREA'),
        'heating_type': cert.get('MAINHEAT_DESCRIPTION'),
        'wall_insulation': cert.get('WALLS_DESCRIPTION'),
        'roof_description': cert.get('ROOF_DESCRIPTION'),
        'windows_description': cert.get('WINDOWS_DESCRIPTION'),
        'main_fuel': cert.get('MAIN_FUEL'),
        'wind_turbine_count': cert.get('WIND_TURBINE_COUNT', 0),
        'co2_emissions_current': cert.get('CO2_EMISSIONS_CURRENT'),
        'energy_consumption_current': cert.get('ENERGY_CONSUMPTION_CURRENT'),
        'heating_cost_current': cert.get('HEATING_COST_CURRENT'),
        'hot_water_cost_current': cert.get('HOT_WATER_COST_CURRENT'),
        'lighting_cost_current': cert.get('LIGHTING_COST_CURRENT')
    }
    
    # Check for solar panels (PHOTO_SUPPLY > 0)
    photo_supply = cert.get('PHOTO_SUPPLY', 0)
    latest_epc['solar_panels'] = bool(photo_supply and float(photo_supply) > 0)
    
    # Check for solar water heating
    solar_water = cert.get('SOLAR_WATER_HEATING_FLAG', '')
    latest_epc['solar_water_heating'] = solar_water.upper() in ('Y', 'YES', 'TRUE')
    
    return latest_epc


def extract_epc_summary(cert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary EPC information for the historical epcs array.
    
    Args:
        cert: Certificate document from OpenSearch
        
    Returns:
        EPC summary object with key fields
    """
    return {
        'LMK_KEY': cert.get('LMK_KEY'),
        'rating': cert.get('CURRENT_ENERGY_RATING'),
        'score': cert.get('CURRENT_ENERGY_EFFICIENCY'),
        'inspection_date': cert.get('INSPECTION_DATE'),
        'lodgement_date': cert.get('LODGEMENT_DATE')
    }


def build_property_document(uprn: str, certificates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a property document from a list of certificates for the same UPRN.
    
    Args:
        uprn: The property UPRN
        certificates: List of certificate documents, should be sorted by date (newest first)
        
    Returns:
        Property document ready for indexing
    """
    if not certificates:
        return None
    
    # Use the latest (first) certificate for main details
    latest_cert = certificates[0]
    
    property_doc = {
        'uprn': uprn,
        'address': extract_address(latest_cert),
        'latest_epc': extract_latest_epc(latest_cert),
        'epcs': [extract_epc_summary(cert) for cert in certificates],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Add location geo_point if available
    if 'location' in latest_cert and latest_cert['location']:
        property_doc['location'] = latest_cert['location']
    
    # Calculate estimated running cost from current costs
    running_costs = [
        latest_cert.get('HEATING_COST_CURRENT', 0) or 0,
        latest_cert.get('HOT_WATER_COST_CURRENT', 0) or 0,
        latest_cert.get('LIGHTING_COST_CURRENT', 0) or 0
    ]
    try:
        total_cost = sum(float(c) for c in running_costs if c)
        if total_cost > 0:
            property_doc['estimated_running_cost'] = int(total_cost)
    except (ValueError, TypeError):
        pass
    
    return property_doc


def fetch_all_certificates_by_uprn(client: OpenSearch, cert_index: str, uprn: str) -> List[Dict[str, Any]]:
    """
    Fetch all certificates for a given UPRN, sorted by lodgement date descending.
    
    Args:
        client: OpenSearch client
        cert_index: Name of the certificates index
        uprn: The UPRN to fetch certificates for
        
    Returns:
        List of certificate documents sorted by date (newest first)
    """
    # Determine date field to use for sorting
    date_fields = ['LODGEMENT_DATETIME', 'LODGEMENT_DATE', 'INSPECTION_DATE']
    
    body = {
        'query': {
            'term': {'UPRN.keyword': uprn}
        },
        'sort': [{date_fields[0]: {'order': 'desc', 'missing': '_last'}}],
        'size': 100  # Max 100 certificates per property (should be more than enough)
    }
    
    result = client.search(index=cert_index, body=body)
    return [hit['_source'] for hit in result['hits']['hits']]


def build_properties_index(
    client: OpenSearch,
    cert_index: str,
    prop_index: str,
    batch_size: int = 500
) -> int:
    """
    Build the properties index from the certificates index.
    
    Args:
        client: OpenSearch client
        cert_index: Name of the certificates index
        prop_index: Name of the properties index to create
        batch_size: Number of properties to index in each batch
        
    Returns:
        Total number of properties indexed
    """
    print(f'Building properties index: {prop_index}')
    
    # Create the properties index with proper mapping
    if client.indices.exists(index=prop_index):
        print(f'Warning: Properties index {prop_index} already exists. Deleting and recreating...')
        client.indices.delete(index=prop_index)
    
    mapping = create_property_mapping()
    client.indices.create(index=prop_index, body=mapping)
    print(f'Created properties index: {prop_index}')
    
    # Use composite aggregation to page through all UPRNs
    comp_source = [{'uprn': {'terms': {'field': 'UPRN.keyword'}}}]
    after_key = None
    total_props = 0
    
    while True:
        body = {
            'size': 0,
            'aggs': {
                'by_uprn': {
                    'composite': {
                        'size': 1000,
                        'sources': comp_source,
                        **({'after': after_key} if after_key else {})
                    }
                }
            }
        }
        
        res = client.search(index=cert_index, body=body)
        buckets = res['aggregations']['by_uprn']['buckets']
        
        if not buckets:
            break
        
        # Process each UPRN
        actions = []
        for bucket in buckets:
            uprn = bucket['key']['uprn']
            
            # Fetch all certificates for this UPRN
            certificates = fetch_all_certificates_by_uprn(client, cert_index, uprn)
            
            if certificates:
                # Build property document
                prop_doc = build_property_document(uprn, certificates)
                
                if prop_doc:
                    action = {
                        '_index': prop_index,
                        '_id': str(uprn),
                        '_source': prop_doc
                    }
                    actions.append(action)
        
        # Bulk index properties
        if actions:
            helpers.bulk(client, actions)
            total_props += len(actions)
            print(f'Indexed {total_props} properties...')
        
        # Check for more pages
        after_key = res['aggregations']['by_uprn'].get('after_key')
        if not after_key:
            break
    
    print(f'Properties index build complete: {total_props} documents')
    return total_props


def main(argv=None):
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Build a property index from the certificates index in OpenSearch'
    )
    parser.add_argument(
        '--opensearch-url',
        default=os.environ.get('OPENSEARCH_URL', 'http://localhost:9200'),
        help='OpenSearch endpoint URL (default: $OPENSEARCH_URL or http://localhost:9200)'
    )
    parser.add_argument(
        '--user',
        default=os.environ.get('OPENSEARCH_USER'),
        help='OpenSearch username (default: $OPENSEARCH_USER)'
    )
    parser.add_argument(
        '--password',
        default=os.environ.get('OPENSEARCH_PASS'),
        help='OpenSearch password (default: $OPENSEARCH_PASS)'
    )
    parser.add_argument(
        '--cert-index',
        default='domestic-2023-certificates',
        help='Name of the certificates index (default: domestic-2023-certificates)'
    )
    parser.add_argument(
        '--prop-index',
        default='domestic-2023-properties',
        help='Name of the properties index to create (default: domestic-2023-properties)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Batch size for bulk indexing (default: 500)'
    )
    
    args = parser.parse_args(argv)
    
    # Create OpenSearch client
    client = OpenSearch(
        [args.opensearch_url],
        http_auth=(args.user, args.password) if args.user else None,
        use_ssl=args.opensearch_url.startswith('https'),
        verify_certs=False,  # Disable for local dev; enable in production
        ssl_show_warn=False
    )
    
    # Check if certificates index exists
    if not client.indices.exists(index=args.cert_index):
        print(f'Error: Certificates index "{args.cert_index}" does not exist.')
        print('Please run ingest_domestic_2023.py first to create the certificates index.')
        return 1
    
    # Build the properties index
    try:
        build_properties_index(
            client,
            args.cert_index,
            args.prop_index,
            batch_size=args.batch_size
        )
        return 0
    except Exception as e:
        print(f'Error building properties index: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
