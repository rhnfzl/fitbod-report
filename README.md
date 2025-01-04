# Fitbod Workout Data Analysis Tool

A Streamlit-based web application that processes workout data exported from the [Fitbod](http://fitbod.me) app, generating detailed or summary reports in markdown and PDF formats. The tool provides weekly summaries, exercise progression tracking, and comprehensive workout analytics designed to be easily understood by both humans and AI tools.

## Features

- **Interactive Web Interface**:
  - Easy-to-use Streamlit dashboard
  - File upload functionality
  - Date range selection
  - Real-time report preview

- **Flexible Report Options**:
  - Generate both detailed and summary reports
  - Support for metric and imperial units
  - Export to Markdown or PDF format
  - AI-friendly structured output

- **Comprehensive Analytics**:
  - Weekly training summaries
  - Exercise-specific breakdowns
  - Week-over-week progress tracking
  - Set-by-set progression analysis
  - Warmup vs working set distinction
  - Exercise-specific statistics

- **Data Processing**:
  - Automatic unit conversion (meters to miles/km, kilograms to pounds)
  - CSV validation and error handling
  - Timezone-aware date processing
  - Clean, structured output

## Project Structure

```
fitbod-report/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Project dependencies
├── LICENSE               # MIT License file
├── docs/                 # Documentation files
├── src/                  # Source code modules
│   ├── __init__.py
│   ├── data/            # Data processing modules
│   │   ├── __init__.py
│   │   ├── processor.py # Data processing utilities
│   │   └── validator.py # Data validation utilities
│   ├── pdf/             # PDF generation modules
│   │   ├── __init__.py
│   │   └── generator.py # PDF conversion utilities
│   ├── report/          # Report generation modules
│   │   ├── __init__.py
│   │   └── generator.py # Report generation utilities
│   └── utils/           # Utility modules
│       ├── __init__.py
│       └── converters.py # Unit conversion utilities
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rhnfzl/fitbod-report.git
cd fitbod-report
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Data Preparation

1. Export your Fitbod data:
   - Open Fitbod app
   - Go to Log (lower right)
   - Click Settings (cog in upper right)
   - Scroll down to "Export Workout Data"
   - Save the CSV file

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Use the web interface:
   - Upload your Fitbod export CSV file
   - Select date range for analysis
   - Choose unit system (metric/imperial)
   - Select report format (summary/detailed)
   - Choose output format (markdown/PDF)
   - Generate and download your report

## Input Data Format

The CSV file should contain the following columns:
- `Date`: Workout date and time
- `Exercise`: Exercise name
- `Reps`: Number of repetitions
- `Weight(kg)`: Weight in kilograms
- `Duration(s)`: Duration in seconds
- `Distance(m)`: Distance in meters
- `Incline`: Incline setting
- `Resistance`: Resistance setting
- `isWarmup`: Whether it's a warmup set
- `Note`: Any additional notes
- `multiplier`: Exercise multiplier

## Dependencies

Key dependencies include:
- Python 3.8+
- streamlit>=1.31.0
- pandas>=2.2.0
- pytz>=2024.1
- markdown-pdf>=0.1.2

For a complete list of dependencies, see `requirements.txt`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [ftbod](https://github.com/juanino/fbod) for the initial data summary report