# Data Processing Module Documentation

## Overview

The data processing module handles CSV file reading, data validation, and transformation of workout data. It ensures data consistency and proper formatting for report generation.

## Modules

### validator.py

Validates the structure and content of input data.

#### Functions

`validate_data_structure(data, is_dataframe=False)`
- **Purpose**: Validates if the data has all required columns
- **Arguments**:
  - `data`: DataFrame or list of data
  - `is_dataframe`: Boolean indicating if data is a pandas DataFrame
- **Returns**: Tuple (is_valid, missing_columns)
- **Required Columns**:
  ```python
  {
      'Date', 'Exercise', 'Reps', 'Weight(kg)', 
      'Duration(s)', 'Distance(m)', 'Incline', 
      'Resistance', 'isWarmup', 'Note', 'multiplier'
  }
  ```

### processor.py

Handles data reading and processing.

#### Functions

`read_csv(filename)`
- **Purpose**: Reads and validates CSV file
- **Arguments**: 
  - `filename`: Path to CSV file
- **Returns**: Tuple (headers, data)
- **Validation**:
  - Checks for empty rows
  - Validates row length
  - Reports problematic rows

`process_data(headers, data)`
- **Purpose**: Converts raw data into structured format
- **Arguments**:
  - `headers`: List of column headers
  - `data`: List of data rows
- **Returns**: List of processed records
- **Processing**:
  - Validates row structure
  - Creates dictionary records
  - Handles missing data

`process_data_from_df(df)`
- **Purpose**: Processes pandas DataFrame
- **Arguments**:
  - `df`: pandas DataFrame
- **Returns**: List of processed records
- **Data Transformations**:
  - Converts boolean to string
  - Formats dates
  - Handles numeric types
  - Fills missing values

## Data Flow

1. **Input Validation**:
   ```
   CSV/DataFrame → validate_data_structure() → Validation Result
   ```

2. **Data Processing**:
   ```
   Raw Data → process_data_from_df() → Structured Records
   ```

3. **Type Conversions**:
   - Dates: UTC timezone
   - Numbers: Float/Integer
   - Booleans: Lowercase strings

## Error Handling

The module implements several error checks:

1. **Structure Validation**:
   - Missing columns
   - Invalid data types
   - Empty rows

2. **Data Validation**:
   - Row length mismatches
   - Missing values
   - Invalid formats

3. **Type Conversion**:
   - Date parsing errors
   - Numeric conversion errors
   - Boolean conversion issues

## Best Practices

1. **Data Preparation**:
   - Ensure CSV is properly exported
   - Check for complete columns
   - Validate date formats

2. **Error Handling**:
   - Check validation results
   - Handle missing data appropriately
   - Log processing errors

3. **Performance**:
   - Use DataFrame for large datasets
   - Handle memory efficiently
   - Clean up temporary data 