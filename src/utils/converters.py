"""Utility functions for unit conversion and time formatting."""

def seconds_to_time(seconds):
    """Convert seconds to human-readable time format.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        str: Formatted time string (e.g., "1h 30m 45s")
    """
    try:
        seconds = float(seconds)
        if seconds < 0:
            seconds = 0
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid seconds value: {seconds}, Error: {e}")
        return "0h 0m 0s"

def round_to_gym_weight(weight_lbs):
    """Round weight in pounds to common gym increments.
    
    Args:
        weight_lbs (float): Weight in pounds
        
    Returns:
        float: Weight rounded to nearest common gym increment
    """
    if weight_lbs < 5:
        # Round to nearest 1 lb for very light weights
        return round(weight_lbs)
    elif weight_lbs < 15:
        # Round to nearest 2.5 lbs for light weights
        return round(weight_lbs * 2) / 2
    else:
        # Round to nearest 5 lbs for heavier weights
        return round(weight_lbs / 5) * 5

def convert_units(value, unit_type, to_metric=True):
    """Convert between metric and imperial units.
    
    Args:
        value (float): Value to convert
        unit_type (str): Type of unit ('weight' or 'distance')
        to_metric (bool): Convert to metric if True, to imperial if False
        
    Returns:
        tuple: (converted value, unit string)
    """
    if unit_type == 'weight':
        if to_metric:
            # Imperial to metric
            return value * 0.453592, 'kg'
        else:
            # Metric to imperial - apply gym rounding
            lbs = value * 2.20462
            return round_to_gym_weight(lbs), 'lbs'
    elif unit_type == 'distance':
        if to_metric:
            # Miles to kilometers
            return value * 1.60934, 'km'
        else:
            # Kilometers to miles
            return value * 0.621371, 'miles'
    return value, '' 