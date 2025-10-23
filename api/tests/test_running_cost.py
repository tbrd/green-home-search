"""
Tests for the running cost calculation module.
"""

import pytest
from pathlib import Path
import sys

# Ensure api root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from running_cost import calculate_running_cost, EPC_RATING_COSTS


class TestCalculateRunningCost:
    """Test suite for calculate_running_cost function."""
    
    def test_rating_a_returns_50(self):
        """Test that EPC rating A returns £50."""
        epc_doc = {"current-energy-rating": "A"}
        assert calculate_running_cost(epc_doc) == 50
    
    def test_rating_b_returns_75(self):
        """Test that EPC rating B returns £75."""
        epc_doc = {"current-energy-rating": "B"}
        assert calculate_running_cost(epc_doc) == 75
    
    def test_rating_c_returns_100(self):
        """Test that EPC rating C returns £100."""
        epc_doc = {"current-energy-rating": "C"}
        assert calculate_running_cost(epc_doc) == 100
    
    def test_rating_d_returns_125(self):
        """Test that EPC rating D returns £125."""
        epc_doc = {"current-energy-rating": "D"}
        assert calculate_running_cost(epc_doc) == 125
    
    def test_rating_e_returns_150(self):
        """Test that EPC rating E returns £150."""
        epc_doc = {"current-energy-rating": "E"}
        assert calculate_running_cost(epc_doc) == 150
    
    def test_rating_f_returns_175(self):
        """Test that EPC rating F returns £175."""
        epc_doc = {"current-energy-rating": "F"}
        assert calculate_running_cost(epc_doc) == 175
    
    def test_rating_g_returns_200(self):
        """Test that EPC rating G returns £200."""
        epc_doc = {"current-energy-rating": "G"}
        assert calculate_running_cost(epc_doc) == 200
    
    def test_uppercase_field_name(self):
        """Test that CURRENT_ENERGY_RATING field name works."""
        epc_doc = {"CURRENT_ENERGY_RATING": "B"}
        assert calculate_running_cost(epc_doc) == 75
    
    def test_lowercase_rating_value(self):
        """Test that lowercase rating values work."""
        epc_doc = {"current-energy-rating": "c"}
        assert calculate_running_cost(epc_doc) == 100
    
    def test_rating_with_whitespace(self):
        """Test that ratings with whitespace are handled."""
        epc_doc = {"current-energy-rating": " D "}
        assert calculate_running_cost(epc_doc) == 125
    
    def test_invalid_rating_returns_none(self):
        """Test that invalid rating returns None."""
        epc_doc = {"current-energy-rating": "Z"}
        assert calculate_running_cost(epc_doc) is None
    
    def test_missing_rating_field_returns_none(self):
        """Test that missing rating field returns None."""
        epc_doc = {"some-other-field": "value"}
        assert calculate_running_cost(epc_doc) is None
    
    def test_empty_document_returns_none(self):
        """Test that empty document returns None."""
        assert calculate_running_cost({}) is None
    
    def test_none_document_returns_none(self):
        """Test that None document returns None."""
        assert calculate_running_cost(None) is None
    
    def test_all_ratings_defined(self):
        """Test that all expected ratings A-G are defined in the mapping."""
        expected_ratings = ["A", "B", "C", "D", "E", "F", "G"]
        for rating in expected_ratings:
            assert rating in EPC_RATING_COSTS, f"Rating {rating} not defined"
            assert EPC_RATING_COSTS[rating] > 0, f"Rating {rating} has invalid cost"
    
    def test_costs_increase_with_worse_rating(self):
        """Test that costs increase as ratings get worse (A to G)."""
        ratings = ["A", "B", "C", "D", "E", "F", "G"]
        costs = [EPC_RATING_COSTS[r] for r in ratings]
        assert costs == sorted(costs), "Costs should increase from A to G"
