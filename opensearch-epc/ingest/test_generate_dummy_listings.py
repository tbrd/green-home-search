#!/usr/bin/env python3
"""
Tests for generate_dummy_listings.py

This test suite covers:
- Price estimation from property characteristics
- Bedroom estimation
- Listing generation from property documents
- Sampling logic
"""

import pytest
from datetime import datetime, timezone

from generate_dummy_listings import (
    estimate_price_from_property,
    estimate_bedrooms,
    generate_listing_from_property,
)


class TestPriceEstimation:
    """Test price estimation from property characteristics."""
    
    def test_estimate_price_house(self):
        """Test price estimation for a house."""
        prop = {
            'uprn': '12345',
            'latest_epc': {
                'property_type': 'House',
                'total_floor_area': 100.0,
                'rating': 'C',
            }
        }
        
        price = estimate_price_from_property(prop)
        
        # Should be around 100 sqm * £3000 * 1.05 (C rating) = £315,000
        # With ±10% variation: £283,500 - £346,500
        assert 250000 <= price <= 400000
        assert price % 1000 == 0  # Should be rounded to nearest £1000
    
    def test_estimate_price_flat(self):
        """Test price estimation for a flat."""
        prop = {
            'uprn': '12346',
            'latest_epc': {
                'property_type': 'Flat',
                'total_floor_area': 60.0,
                'rating': 'B',
            }
        }
        
        price = estimate_price_from_property(prop)
        
        # Should be around 60 sqm * £3500 * 1.10 (B rating) = £231,000
        # With ±10% variation: £207,900 - £254,100
        assert 150000 <= price <= 300000
        assert price % 1000 == 0
    
    def test_estimate_price_low_epc_rating(self):
        """Test that lower EPC ratings result in lower prices."""
        prop_high = {
            'uprn': '12347',
            'latest_epc': {
                'property_type': 'House',
                'total_floor_area': 100.0,
                'rating': 'A',
            }
        }
        
        prop_low = {
            'uprn': '12348',
            'latest_epc': {
                'property_type': 'House',
                'total_floor_area': 100.0,
                'rating': 'G',
            }
        }
        
        # Generate multiple samples to account for randomness
        high_prices = [estimate_price_from_property(prop_high) for _ in range(10)]
        low_prices = [estimate_price_from_property(prop_low) for _ in range(10)]
        
        # Average price for A-rated should be higher than G-rated
        assert sum(high_prices) / len(high_prices) > sum(low_prices) / len(low_prices)
    
    def test_estimate_price_minimum(self):
        """Test that price never goes below minimum."""
        prop = {
            'uprn': '12349',
            'latest_epc': {
                'property_type': 'Park home',
                'total_floor_area': 20.0,  # Very small
                'rating': 'G',  # Worst rating
            }
        }
        
        price = estimate_price_from_property(prop)
        assert price >= 50000  # Minimum price


class TestBedroomEstimation:
    """Test bedroom estimation from property characteristics."""
    
    def test_estimate_bedrooms_small(self):
        """Test bedroom estimation for small properties."""
        prop = {
            'latest_epc': {
                'total_floor_area': 40.0
            }
        }
        
        bedrooms = estimate_bedrooms(prop)
        assert bedrooms == 1
    
    def test_estimate_bedrooms_medium(self):
        """Test bedroom estimation for medium properties."""
        prop = {
            'latest_epc': {
                'total_floor_area': 80.0
            }
        }
        
        bedrooms = estimate_bedrooms(prop)
        assert bedrooms == 3
    
    def test_estimate_bedrooms_large(self):
        """Test bedroom estimation for large properties."""
        prop = {
            'latest_epc': {
                'total_floor_area': 200.0
            }
        }
        
        bedrooms = estimate_bedrooms(prop)
        assert bedrooms == 5
    
    def test_estimate_bedrooms_no_floor_area(self):
        """Test bedroom estimation when floor area is missing."""
        prop = {
            'latest_epc': {}
        }
        
        bedrooms = estimate_bedrooms(prop)
        assert 1 <= bedrooms <= 5


class TestListingGeneration:
    """Test listing generation from property documents."""
    
    def test_generate_listing_complete_property(self):
        """Test generating a listing from a complete property document."""
        prop = {
            'uprn': 'UPRN-TEST-123',
            'address': {
                'address1': '1 Test Street',
                'address2': 'Test Town',
                'address3': 'Test City',
                'postcode': 'TE1 1ST',
                'lat': 51.5074,
                'long': -0.1278,
            },
            'latest_epc': {
                'property_type': 'House',
                'total_floor_area': 100.0,
                'rating': 'C',
                'score': 72,
                'main_fuel': 'mains gas',
                'solar_panels': True,
                'solar_water_heating': False,
            },
            'estimated_running_cost': 1200,
            'location': {
                'lat': 51.5074,
                'lon': -0.1278,
            }
        }
        
        listing = generate_listing_from_property(prop, source='test')
        
        # Check required fields
        assert listing['listing_id'] == 'test:UPRN-TEST-123'
        assert listing['property_id'] == 'UPRN-TEST-123'
        assert listing['source'] == 'test'
        assert listing['currency'] == 'GBP'
        
        # Check address
        assert 'Test Street' in listing['address_line']
        assert listing['postcode'] == 'TE1 1ST'
        
        # Check location
        assert listing['location']['lat'] == 51.5074
        assert listing['location']['lon'] == -0.1278
        
        # Check price and bedrooms
        assert listing['price'] > 0
        assert listing['price'] % 1000 == 0
        assert listing['bedrooms'] >= 1
        
        # Check EPC enrichment
        assert listing['epc_rating'] == 'C'
        assert listing['epc_score'] == 72
        assert listing['main_fuel'] == 'mains gas'
        assert listing['solar_panels'] is True
        assert listing['solar_water_heating'] is False
        
        # Check running costs
        assert listing['running_cost_annual'] == 1200.0
        assert listing['running_cost_monthly'] == 100.0
        
        # Check timestamps
        assert 'listed_at' in listing
        assert 'expires_at' in listing
        assert listing['status'] in ['active', 'expired']
        assert isinstance(listing['is_active'], bool)
    
    def test_generate_listing_minimal_property(self):
        """Test generating a listing from a minimal property document."""
        prop = {
            'uprn': 'UPRN-MIN-456',
            'address': {
                'address': '2 Minimal Road',
                'postcode': 'MI2 2AL',
            },
            'latest_epc': {}
        }
        
        listing = generate_listing_from_property(prop, source='test')
        
        # Should still generate basic listing
        assert listing['listing_id'] == 'test:UPRN-MIN-456'
        assert listing['property_id'] == 'UPRN-MIN-456'
        assert listing['price'] > 0
        assert listing['bedrooms'] >= 1
        assert listing['postcode'] == 'MI2 2AL'
    
    def test_generate_listing_no_uprn(self):
        """Test that listing generation fails without UPRN."""
        prop = {
            'address': {
                'address': '3 No UPRN Lane'
            },
            'latest_epc': {}
        }
        
        listing = generate_listing_from_property(prop)
        
        # Should return None if no UPRN
        assert listing is None
    
    def test_listing_timestamps_format(self):
        """Test that timestamps are in ISO format."""
        prop = {
            'uprn': 'UPRN-TIME-789',
            'address': {},
            'latest_epc': {}
        }
        
        listing = generate_listing_from_property(prop)
        
        # Should parse as valid ISO datetime
        listed_at = datetime.fromisoformat(listing['listed_at'].replace('Z', '+00:00'))
        expires_at = datetime.fromisoformat(listing['expires_at'].replace('Z', '+00:00'))
        
        assert isinstance(listed_at, datetime)
        assert isinstance(expires_at, datetime)
        assert expires_at > listed_at


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
