"""
Running cost calculation based on EPC rating.

This module provides a simple placeholder algorithm that estimates
monthly running costs based solely on the EPC (Energy Performance Certificate) rating.
"""

from typing import Dict, Any, Optional


# Mapping of EPC ratings to monthly running costs in GBP
EPC_RATING_COSTS = {
    "A": 50,
    "B": 75,
    "C": 100,
    "D": 125,
    "E": 150,
    "F": 175,
    "G": 200,
}


def calculate_running_cost(epc_document: Dict[str, Any]) -> Optional[float]:
    """
    Calculate monthly running cost based on EPC rating.
    
    Args:
        epc_document: A dictionary containing EPC data. Expected to have a
                     'current-energy-rating' or 'CURRENT_ENERGY_RATING' field
                     with a value from 'A' to 'G'.
    
    Returns:
        Monthly running cost in GBP, or None if the rating is not found or invalid.
    
    Examples:
        >>> calculate_running_cost({"current-energy-rating": "A"})
        50
        >>> calculate_running_cost({"CURRENT_ENERGY_RATING": "C"})
        100
        >>> calculate_running_cost({"current-energy-rating": "invalid"})
        None
    """
    if not epc_document:
        return None
    
    # Try both possible field names (hyphenated for API, uppercase for raw data)
    rating = epc_document.get("current-energy-rating") or epc_document.get("CURRENT_ENERGY_RATING")
    
    if not rating:
        return None
    
    # Normalize to uppercase and strip whitespace
    rating = str(rating).upper().strip()
    
    # Return the cost for the rating, or None if not found
    return EPC_RATING_COSTS.get(rating)
