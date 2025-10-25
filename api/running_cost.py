"""
Running cost calculation based on EPC rating.

This module provides a simple placeholder algorithm that estimates
monthly running costs based solely on the EPC (Energy Performance Certificate) rating.
"""

from typing import Dict, Any, Optional

def calculate_running_cost(epc_document: Dict[str, Any]) -> Optional[float]:
    """
    Calculate monthly running cost from EPC
    
    Args:
        epc_document: A dictionary containing EPC data. Expected to have 
                     "HOT_WATER_COST_CURRENT" and "HEATING_COST_CURRENT" fields
    
    Returns:
        Monthly running cost in GBP, or None if the rating is not found or invalid.
    
    """
    if not epc_document:
        return None
    
    # todo: calculate based on actual cost data
    # We could use ENERGY_CONSUMPTION_CURRENT is in kWh/m2 - possibly per annum
    # Also need to consider energy prices, and the energy source (electricity/gas/oil/etc)
    
    # Try both possible field names (hyphenated for API, uppercase for raw data)
    hot_water_cost = epc_document.get("HOT_WATER_COST_CURRENT") 
    heating_cost = epc_document.get("HEATING_COST_CURRENT")

    # Return the cost for the rating, or None if not found
    return hot_water_cost + heating_cost if hot_water_cost is not None and heating_cost is not None else None
