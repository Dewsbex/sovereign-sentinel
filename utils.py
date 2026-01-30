"""
Utility functions for Sovereign Sentinel v31.2
Provides decimal truncation and formatting helpers.
"""

import math

def truncate_decimal(value, places=2):
    """
    Truncates a float to specified decimal places (does not round).
    
    Args:
        value: The number to truncate
        places: Number of decimal places to keep (default: 2)
    
    Returns:
        Truncated float value
    
    Examples:
        >>> truncate_decimal(12.3456, 2)
        12.34
        >>> truncate_decimal(12.999, 2)
        12.99
    """
    if value is None:
        return 0.0
    
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        
        # Truncate by multiplying, flooring, then dividing
        multiplier = 10 ** places
        return math.floor(f * multiplier) / multiplier
    except (ValueError, TypeError):
        return 0.0


def format_gbp_truncate(value, places=2):
    """
    Formats a value as GBP with truncation (not rounding).
    
    Args:
        value: The monetary value to format
        places: Number of decimal places (default: 2)
    
    Returns:
        Formatted string like "£1,234.56"
    
    Examples:
        >>> format_gbp_truncate(1234.567)
        '£1,234.56'
        >>> format_gbp_truncate(-1234.999)
        '£-1,234.99'
    """
    truncated = truncate_decimal(value, places)
    return f"£{truncated:,.{places}f}"


def format_pct_truncate(value, places=2):
    """
    Formats a value as a percentage with truncation (not rounding).
    
    Args:
        value: The percentage value (e.g., 0.1234 for 12.34%)
        places: Number of decimal places (default: 2)
    
    Returns:
        Formatted string like "12.34%"
    
    Examples:
        >>> format_pct_truncate(0.12345)
        '12.34%'
        >>> format_pct_truncate(-0.05678)
        '-5.67%'
    """
    pct_value = value * 100
    truncated = truncate_decimal(pct_value, places)
    return f"{truncated:.{places}f}%"
