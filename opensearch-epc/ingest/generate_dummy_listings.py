#!/usr/bin/env python3
"""
Generate dummy sales listings from the properties index.

This script queries the properties index, randomly selects properties to list for sale,
and generates realistic listing data with prices, bedrooms, and other details.

Usage:
  python generate_dummy_listings.py \
    --opensearch-url http://localhost:9200 \
    --properties-index properties \
    --listings-index listings-v1 \
    --percentage 1.0

Environment variables (optional):
  OPENSEARCH_URL, OPENSEARCH_USER, OPENSEARCH_PASS
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from opensearchpy import OpenSearch, helpers


def estimate_price_from_property(prop: Dict[str, Any]) -> int:
    """
    Generate a realistic property price based on property characteristics.
    
    Args:
        prop: Property document with EPC and address data
        
    Returns:
        Estimated price in GBP
    """
    # Base price varies by property type and region
    base_prices = {
        'House': 350000,
        'Flat': 250000,
        'Maisonette': 275000,
        'Bungalow': 320000,
        'Park home': 150000,
    }
    
    latest_epc = prop.get('latest_epc', {})
    property_type = latest_epc.get('property_type', 'House')
    
    # Get base price for property type
    base_price = base_prices.get(property_type, 300000)
    
    # Adjust for floor area (if available)
    floor_area = latest_epc.get('total_floor_area')
    if floor_area:
        try:
            area_float = float(floor_area)
            if area_float > 0:
                # Rough price per sqm: £2,500-3,500 depending on type
                price_per_sqm = 3000 if property_type == 'House' else 3500
                base_price = int(area_float * price_per_sqm)
        except (ValueError, TypeError):
            pass
    
    # Adjust for EPC rating (better rating = higher value)
    epc_rating = latest_epc.get('rating', 'D')
    rating_multipliers = {
        'A': 1.15,
        'B': 1.10,
        'C': 1.05,
        'D': 1.0,
        'E': 0.95,
        'F': 0.90,
        'G': 0.85,
    }
    base_price = int(base_price * rating_multipliers.get(epc_rating, 1.0))
    
    # Add some randomness (±10%)
    variation = random.uniform(0.9, 1.1)
    price = int(base_price * variation)
    
    # Round to nearest £1,000
    price = round(price / 1000) * 1000
    
    return max(price, 50000)  # Minimum price


def estimate_bedrooms(prop: Dict[str, Any]) -> int:
    """
    Estimate number of bedrooms based on property characteristics.
    
    Args:
        prop: Property document
        
    Returns:
        Number of bedrooms (1-5)
    """
    latest_epc = prop.get('latest_epc', {})
    floor_area = latest_epc.get('total_floor_area')
    
    # Estimate based on floor area
    if floor_area:
        try:
            area_float = float(floor_area)
            if area_float < 50:
                return 1
            elif area_float < 70:
                return 2
            elif area_float < 100:
                return 3
            elif area_float < 150:
                return 4
            else:
                return 5
        except (ValueError, TypeError):
            pass
    
    # Default: random between 2-4
    return random.randint(2, 4)


def generate_listing_from_property(prop: Dict[str, Any], source: str = "dummy_gen") -> Optional[Dict[str, Any]]:
    """
    Generate a realistic listing document from a property.
    
    Args:
        prop: Property document from properties index
        source: Listing source identifier
        
    Returns:
        Listing document ready for indexing, or None if UPRN is missing
    """
    uprn = prop.get('uprn')
    if not uprn:
        return None
    
    latest_epc = prop.get('latest_epc', {})
    address = prop.get('address', {})
    
    # Generate listing times
    # List properties as if they were listed in the last 30 days
    days_ago = random.randint(0, 30)
    listed_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    
    # Listings expire after 90 days
    expires_at = listed_at + timedelta(days=90)
    
    # Most listings are active, but some might have expired
    is_active = (datetime.now(timezone.utc) < expires_at)
    
    # Generate price and bedrooms
    price = estimate_price_from_property(prop)
    bedrooms = estimate_bedrooms(prop)
    
    # Build address line
    address_parts = [
        address.get('address1', ''),
        address.get('address2', ''),
        address.get('address3', ''),
    ]
    address_line = ', '.join([p for p in address_parts if p])
    if not address_line:
        address_line = address.get('address', 'Unknown Address')
    
    postcode = address.get('postcode', '')
    
    # Create listing document
    listing = {
        'listing_id': f'{source}:{uprn}',
        'property_id': uprn,
        'source': source,
        'external_id': uprn,
        'status': 'active' if is_active else 'expired',
        'is_active': is_active,
        'listed_at': listed_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'price': price,
        'currency': 'GBP',
        'bedrooms': bedrooms,
        'address_line': address_line,
        'postcode': postcode,
    }
    
    # Add location if available
    if prop.get('location'):
        listing['location'] = prop['location']
    elif address.get('lat') and address.get('long'):
        listing['location'] = {
            'lat': address['lat'],
            'lon': address['long']
        }
    
    # Enrich with EPC data
    if latest_epc.get('main_fuel'):
        listing['main_fuel'] = latest_epc['main_fuel']
    
    if latest_epc.get('solar_panels') is not None:
        listing['solar_panels'] = latest_epc['solar_panels']
    
    if latest_epc.get('solar_water_heating') is not None:
        listing['solar_water_heating'] = latest_epc['solar_water_heating']
    
    if latest_epc.get('rating'):
        listing['epc_rating'] = latest_epc['rating']
    
    if latest_epc.get('score'):
        listing['epc_score'] = latest_epc['score']
    
    # Add running costs if available
    estimated_cost = prop.get('estimated_running_cost')
    if estimated_cost:
        try:
            annual_cost = float(estimated_cost)
            listing['running_cost_annual'] = annual_cost
            listing['running_cost_monthly'] = round(annual_cost / 12.0, 2)
        except (ValueError, TypeError):
            pass
    
    return listing


def sample_properties_for_listings(
    client: OpenSearch,
    properties_index: str,
    percentage: float = 1.0,
    batch_size: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Sample properties from the index to create listings for.
    
    Args:
        client: OpenSearch client
        properties_index: Name of the properties index
        percentage: Percentage of properties to list (0-100)
        batch_size: Number of documents to fetch per scroll request
        
    Returns:
        List of sampled property documents
    """
    print(f'Sampling {percentage}% of properties from {properties_index}...')
    
    # Get total count
    count_response = client.count(index=properties_index)
    total_properties = count_response['count']
    print(f'Total properties in index: {total_properties:,}')
    
    # Calculate target number of listings
    target_listings = int(total_properties * (percentage / 100.0))
    print(f'Target number of listings: {target_listings:,}')
    
    if target_listings == 0:
        print('No listings to generate (percentage too low or no properties)')
        return []
    
    # Calculate sampling ratio
    # We'll use a random number generator to decide if each property should be a listing
    sampling_ratio = percentage / 100.0
    
    sampled_properties = []
    
    # Use scroll API to iterate through all properties
    query = {
        'query': {'match_all': {}},
        'size': batch_size,
    }
    
    response = client.search(index=properties_index, body=query, scroll='5m')
    scroll_id = response['_scroll_id']
    hits = response['hits']['hits']
    
    processed = 0
    while hits:
        for hit in hits:
            # Randomly decide if this property should be listed
            if random.random() < sampling_ratio:
                sampled_properties.append(hit['_source'])
            
            processed += 1
            
            # Stop if we've reached our target
            if len(sampled_properties) >= target_listings:
                break
        
        if len(sampled_properties) >= target_listings:
            break
        
        if processed % 10000 == 0:
            print(f'  Processed {processed:,} properties, selected {len(sampled_properties):,} for listing...')
        
        # Get next batch
        response = client.scroll(scroll_id=scroll_id, scroll='5m')
        scroll_id = response['_scroll_id']
        hits = response['hits']['hits']
    
    # Clean up scroll
    try:
        client.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass
    
    print(f'Selected {len(sampled_properties):,} properties for listing')
    return sampled_properties


def generate_and_index_listings(
    client: OpenSearch,
    properties_index: str,
    listings_index: str,
    percentage: float = 1.0,
    source: str = "dummy_gen",
    batch_size: int = 500,
) -> int:
    """
    Generate dummy listings and index them.
    
    Args:
        client: OpenSearch client
        properties_index: Name of the properties index
        listings_index: Name of the listings index
        percentage: Percentage of properties to list
        source: Source identifier for listings
        batch_size: Batch size for bulk indexing
        
    Returns:
        Total number of listings created
    """
    # Sample properties
    sampled_properties = sample_properties_for_listings(
        client, properties_index, percentage
    )
    
    if not sampled_properties:
        return 0
    
    print(f'Generating listings and indexing into {listings_index}...')
    
    # Generate listings and bulk index
    actions = []
    total_indexed = 0
    
    for prop in sampled_properties:
        listing = generate_listing_from_property(prop, source)
        if listing:
            action = {
                '_op_type': 'index',
                '_index': listings_index,
                '_id': listing['listing_id'],
                '_source': listing,
            }
            actions.append(action)
            
            # Bulk index when batch is full
            if len(actions) >= batch_size:
                helpers.bulk(client, actions)
                total_indexed += len(actions)
                print(f'  Indexed {total_indexed:,} listings...')
                actions = []
    
    # Index remaining listings
    if actions:
        helpers.bulk(client, actions)
        total_indexed += len(actions)
        print(f'  Indexed {total_indexed:,} listings...')
    
    print(f'Successfully indexed {total_indexed:,} listings')
    return total_indexed


def main():
    parser = argparse.ArgumentParser(
        description='Generate dummy sales listings from properties index'
    )
    parser.add_argument(
        '--opensearch-url',
        default=os.environ.get('OPENSEARCH_URL', 'http://localhost:9200'),
        help='OpenSearch endpoint URL'
    )
    parser.add_argument(
        '--user',
        default=os.environ.get('OPENSEARCH_USER'),
        help='OpenSearch username'
    )
    parser.add_argument(
        '--password',
        default=os.environ.get('OPENSEARCH_PASS'),
        help='OpenSearch password'
    )
    parser.add_argument(
        '--properties-index',
        default=os.environ.get('PROPERTIES_INDEX', 'properties'),
        help='Name of the properties index to read from'
    )
    parser.add_argument(
        '--listings-index',
        default=os.environ.get('LISTINGS_INDEX', 'listings-v1'),
        help='Name of the listings index to write to'
    )
    parser.add_argument(
        '--percentage',
        type=float,
        default=1.0,
        help='Percentage of properties to list (default: 1.0)'
    )
    parser.add_argument(
        '--source',
        default='dummy_gen',
        help='Source identifier for generated listings'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Batch size for bulk indexing'
    )
    
    args = parser.parse_args()
    
    # Validate percentage
    if args.percentage < 0 or args.percentage > 100:
        print('Error: percentage must be between 0 and 100')
        return 1
    
    # Create OpenSearch client
    client = OpenSearch(
        [args.opensearch_url],
        http_auth=(args.user, args.password) if args.user else None,
        use_ssl=args.opensearch_url.startswith('https'),
        verify_certs=False,
        ssl_show_warn=False,
    )
    
    # Check if indices exist
    if not client.indices.exists(index=args.properties_index):
        print(f'Error: Properties index "{args.properties_index}" does not exist.')
        return 1
    
    if not client.indices.exists(index=args.listings_index):
        print(f'Error: Listings index "{args.listings_index}" does not exist.')
        print('Create it first using: python create_listings_index.py')
        return 1
    
    # Generate and index listings
    try:
        total = generate_and_index_listings(
            client,
            args.properties_index,
            args.listings_index,
            percentage=args.percentage,
            source=args.source,
            batch_size=args.batch_size,
        )
        
        print(f'\n✓ Successfully generated {total:,} dummy listings')
        print(f'  Source: {args.source}')
        print(f'  Percentage: {args.percentage}%')
        
        return 0
    except Exception as e:
        print(f'Error generating listings: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
