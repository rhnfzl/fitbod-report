# Getting Started with Fitbod Report Generator

This guide will help you get started with the Fitbod Report Generator tool.

## Prerequisites

- Python 3.8 or higher
- Fitbod app with workout data
- Basic understanding of workout metrics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rhnfzl/fitbod-report.git
cd fitbod-report
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Exporting Workout Data

1. Open your Fitbod app
2. Navigate to Log (bottom right)
3. Open Settings (gear icon, top right)
4. Scroll to "Export Workout Data"
5. Save the CSV file to your computer

## Using the Tool

1. Start the application:
```bash
streamlit run app.py
```

2. Upload your data:
   - Click "Browse files" or drag and drop your CSV file
   - The tool will validate your file structure
   - You'll see an error if any required columns are missing

3. Select date range:
   - Choose start and end dates for your analysis
   - The date range will be limited to your workout history

4. Configure report settings:
   - Unit System: Choose between metric and imperial units
   - Report Format: Select summary or detailed report
   - Output Format: Choose between markdown and PDF
   - Timezone: Select your local timezone for accurate date processing

5. Generate and download your report:
   - Click "Generate Report"
   - Preview the report in the browser
   - Download in your chosen format

## Understanding the Report

### Summary Report
- Weekly overview of workouts
- Total volume and distance by exercise
- Progress tracking with week-over-week changes

### Detailed Report
- Daily workout breakdowns
- Set-by-set analysis
- Exercise-specific statistics
- Warmup vs working set differentiation

## Timezone Handling

The tool handles timezones in three stages:
1. Data Import: Dates are read and converted to UTC if no timezone is specified
2. Processing: Data is converted to your selected timezone
3. Display: All dates and times are shown in your local timezone

## Troubleshooting

Common issues and solutions:
- **Missing Columns**: Ensure your CSV export is recent and complete
- **Date Format Issues**: The tool expects Fitbod's standard date format
- **Empty Report**: Check if your date range contains workout data 