"""Data processing utilities for Fitbod workout data."""
import csv
from datetime import datetime
import pandas as pd

def read_csv(filename):
    """Read CSV file and return headers and data.
    
    Args:
        filename: Path to CSV file
        
    Returns:
        tuple: (headers, data)
    """
    data = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read the headers
        for row_num, row in enumerate(reader, 1):
            if not any(row):  # Check if row is empty or contains only empty strings
                print(f"Warning: Row {row_num} is empty or contains only empty values")
                continue
            data.append(row)
    return headers, data

def process_data(headers, data):
    """Process raw data into structured format.
    
    Args:
        headers: List of column headers
        data: List of data rows
        
    Returns:
        list: Processed data records
    """
    processed_data = []
    skipped_rows = 0
    for row_num, row in enumerate(data, 1):
        if len(row) != len(headers):
            skipped_rows += 1
            print(f"Warning: Row {row_num} has {len(row)} columns, expected {len(headers)}")
            print(f"Row content: {row}")
            continue
        record = {}
        for i, header in enumerate(headers):
            record[header] = row[i]
        processed_data.append(record)
    if skipped_rows > 0:
        print(f"Skipped {skipped_rows} rows with incorrect number of columns")
    return processed_data

def process_data_from_df(df):
    """Process data from a pandas DataFrame.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        list: Processed data records
    """
    df = df.copy()
    
    # Convert isWarmup to string 'true'/'false'
    df['isWarmup'] = df['isWarmup'].astype(str).str.lower()
    
    # Optimize date processing - handle various formats while maintaining functionality
    def parse_date(date_str):
        if pd.isna(date_str):
            return None
        if isinstance(date_str, (pd.Timestamp, datetime)):
            return date_str.strftime('%Y-%m-%d %H:%M:%S %z')
        # Remove timezone if present to standardize format
        if '+' in str(date_str):
            date_str = str(date_str).split('+')[0].strip()
        return date_str

    df['Date'] = df['Date'].apply(parse_date)
    
    # Optimize numeric conversions using vectorized operations
    numeric_cols = {
        'Reps': 0,
        'Weight(kg)': 0.0,
        'Distance(m)': 0.0,
        'Duration(s)': 0.0
    }
    
    for col, default in numeric_cols.items():
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default)
        if col == 'Reps':
            df[col] = df[col].astype(int)
        elif col == 'Weight(kg)':
            # Keep original weight values and round to nearest 0.5 kg
            df[col] = (df[col] * 2).round() / 2
            # Ensure weight is not modified by any unintended conversion
            df[col] = df[col].astype(float)
    
    # Ensure multiplier is applied correctly to weights if needed
    if 'multiplier' in df.columns:
        df['Weight(kg)'] = df['Weight(kg)'] * pd.to_numeric(df['multiplier'], errors='coerce').fillna(1.0)
    
    return process_data(df.columns.tolist(), df.values.tolist()) 