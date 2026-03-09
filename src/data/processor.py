"""Data processing utilities for Fitbod workout data."""

import csv
from datetime import UTC, datetime

import pandas as pd


def read_csv(filename):
    """Read CSV file and return headers and data.

    Args:
        filename: Path to CSV file

    Returns:
        tuple: (headers, data)
    """
    data = []
    with open(filename) as file:
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

    def normalize_date(date_val):
        """Normalize date to naive UTC datetime (avoids string round-trip)."""
        if pd.isna(date_val):
            return None
        if isinstance(date_val, pd.Timestamp):
            if date_val.tzinfo is not None:
                date_val = date_val.tz_convert("UTC").tz_localize(None)
            return date_val.to_pydatetime()
        if isinstance(date_val, datetime):
            if date_val.tzinfo is not None:
                date_val = date_val.astimezone(UTC).replace(tzinfo=None)
            return date_val
        # String fallback for CLI path
        if "+" in str(date_val):
            date_val = str(date_val).split("+")[0].strip()
        return date_val

    # Compute transformed columns as individual Series (no full df.copy())
    transformed = {
        "isWarmup": df["isWarmup"].fillna(False).astype(str).str.lower(),
        "Date": df["Date"].apply(normalize_date),
    }

    for col, default in {"Reps": 0, "Weight(kg)": 0.0, "Distance(m)": 0.0, "Duration(s)": 0.0}.items():
        series = pd.to_numeric(df[col], errors="coerce").fillna(default)
        if col == "Reps":
            series = series.astype(int)
        transformed[col] = series

    # Apply multiplier first, then round to nearest 0.5kg
    if "multiplier" in df.columns:
        transformed["Weight(kg)"] = transformed["Weight(kg)"] * pd.to_numeric(df["multiplier"], errors="coerce").fillna(1.0)
    transformed["Weight(kg)"] = (transformed["Weight(kg)"] * 2).round() / 2

    # Build result - unmodified columns reference original data (pandas CoW)
    return pd.DataFrame({col: transformed.get(col, df[col]) for col in df.columns}).to_dict("records")
