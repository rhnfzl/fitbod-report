"""Data validation utilities for Fitbod workout data."""

def validate_data_structure(data, is_dataframe=False):
    """Validate if the data has the required columns.
    
    Args:
        data: DataFrame or list of data
        is_dataframe: Boolean indicating if data is a pandas DataFrame
        
    Returns:
        tuple: (is_valid, missing_columns)
    """
    required_columns = {
        'Date', 'Exercise', 'Reps', 'Weight(kg)', 'Duration(s)', 
        'Distance(m)', 'Incline', 'Resistance', 'isWarmup', 'Note', 'multiplier'
    }
    
    if is_dataframe:
        missing_columns = required_columns - set(data.columns)
        return len(missing_columns) == 0, missing_columns
    else:
        if isinstance(data, (list, tuple)) and len(data) > 0:
            headers = set(data[0])
            missing_columns = required_columns - headers
            return len(missing_columns) == 0, missing_columns
        return False, required_columns 