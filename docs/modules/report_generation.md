# Report Generation Module Documentation

## Overview

The report generation module handles the creation of workout summaries and reports in both markdown and PDF formats. It processes workout data into weekly summaries and generates human and AI-readable reports.

## Modules

### generator.py

Generates weekly summaries and formatted reports.

#### Functions

`get_available_timezones()`
- **Purpose**: Provides list of supported timezones
- **Returns**: List of common timezone names
- **Available Timezones**:
  ```python
  [
      'UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific',
      'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Australia/Sydney'
  ]
  ```

`summarize_by_week(processed_data, use_metric=True, timezone='UTC')`
- **Purpose**: Generates weekly workout summaries
- **Arguments**:
  - `processed_data`: List of processed workout records
  - `use_metric`: Boolean for metric/imperial units
  - `timezone`: Timezone for date processing
- **Returns**: Dictionary of weekly summaries
- **Summary Structure**:
  ```python
  {
      'week_key': {
          'Duration(s)': float,
          'Distance': float,
          'Reps': int,
          'Volume': float,
          'Distance_by_exercise': dict,
          'Volume_by_exercise': dict,
          'Exercise_details': dict,
          'Workouts': dict
      }
  }
  ```

`generate_markdown_report(summaries, use_metric=True, report_format='summary')`
- **Purpose**: Creates formatted markdown report
- **Arguments**:
  - `summaries`: Dictionary of weekly summaries
  - `use_metric`: Boolean for unit system
  - `report_format`: 'summary' or 'detailed'
- **Returns**: Markdown formatted string
- **Report Sections**:
  - Weekly Overview
  - Exercise Details
  - Progress Metrics
  - Set Progression (detailed only)

## Report Formats

### Summary Report
1. **Weekly Overview**:
   - Total duration, distance, reps
   - Volume calculations
   - Exercise-specific totals

2. **Progress Tracking**:
   - Week-over-week changes
   - Distance and volume progression
   - Exercise distribution

### Detailed Report
1. **Daily Breakdowns**:
   - Time-stamped workouts
   - Set-by-set details
   - Exercise parameters

2. **Exercise Analysis**:
   - Working vs warmup sets
   - Weight progression
   - Volume calculations

## Timezone Handling

The module handles dates in three steps:

1. **Input Processing**:
   ```python
   date_utc = datetime.strptime(entry['Date'], '%Y-%m-%d %H:%M:%S %z')
   ```

2. **Timezone Conversion**:
   ```python
   local_date = date_utc.astimezone(tz)
   ```

3. **Week Calculation**:
   ```python
   week_start = local_date - timedelta(days=local_date.weekday())
   week_end = week_start + timedelta(days=6)
   ```

## Metrics Calculation

### Volume Metrics
- **Total Volume**: `weight * reps`
- **Exercise Volume**: Sum of set volumes
- **Weekly Volume**: Sum of exercise volumes

### Progress Metrics
- **Distance Change**: `((current - previous) / previous) * 100`
- **Volume Change**: `((current - previous) / previous) * 100`

## Best Practices

1. **Report Generation**:
   - Use consistent timezone
   - Validate input data
   - Handle missing metrics

2. **Data Presentation**:
   - Format numbers consistently
   - Use appropriate units
   - Include context for metrics

3. **Performance**:
   - Optimize large datasets
   - Cache calculations
   - Clean up resources 