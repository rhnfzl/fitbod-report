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

def convert_units(value, unit_type, to_metric=True):
    """Convert between metric and imperial units.
    
    Args:
        value: Numeric value to convert
        unit_type: Type of unit ('weight' or 'distance')
        to_metric: If True, convert to metric; if False, convert to imperial
        
    Returns:
        tuple: (converted_value, unit_string)
    """
    conversions = {
        'weight': (2.20462, 'kg', 'lbs'),  # kg to lbs
        'distance': (0.621371, 'km', 'miles')  # km to miles
    }
    factor, metric_unit, imperial_unit = conversions[unit_type]
    
    if to_metric:
        return value / factor, metric_unit
    return value * factor, imperial_unit 