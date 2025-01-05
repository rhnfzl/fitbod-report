# Fitbod Workout Data Analysis Tool

Try it out here: [https://fitbod-report.streamlit.app/](https://fitbod-report.streamlit.app/)

A Streamlit-based web application that processes workout data exported from the [Fitbod](http://fitbod.me) app, generating detailed or summary reports in markdown and PDF formats. The tool provides weekly summaries, exercise progression tracking, and comprehensive workout analytics designed to be easily understood by both humans and AI tools.

The tool was primarily created to make Fitbod data more AI-friendly. The generated markdown reports can be easily fed into tools like ChatGPT, Claude, or Gemini to:
- Analyse workout patterns
- Get personalised recommendations
- Identify areas for improvement
- Build new workout plans based on historical data
- Compare/Build your routines with reference fitness books/programs

**Privacy First**: No data storage - everything is processed in your browser.

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

## Prerequisites

- Python 3.8 or higher
- UV package manager (for local development)

## Installation

### Using Streamlit Cloud (Recommended)
Simply visit [https://fitbod-report.streamlit.app/](https://fitbod-report.streamlit.app/) - no installation required!

### Local Development

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone this repository:
```bash
git clone https://github.com/rhnfzl/fitbod-report.git
cd fitbod-report
```

3. Install dependencies using UV:
```bash
uv pip install -e .
```

For development, install additional dependencies:
```bash
uv pip install -e ".[dev]"
```

## Usage

### Web Interface

1. **Streamlit Cloud (Recommended)**:
   - Visit [https://fitbod-report.streamlit.app/](https://fitbod-report.streamlit.app/)
   - Upload your Fitbod export CSV file
   - Select your preferences and generate reports

2. **Local Development**:
   ```bash
   uv run start
   ```
   This will start the web interface at http://localhost:8501

## Data Preparation

1. Export your Fitbod data:
   - Open Fitbod app
   - Go to Log (lower right)
   - Click Settings (cog in upper right)
   - Scroll down to "Export Workout Data"
   - Save the CSV file

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

## Project Structure

```
fitbod-report/
├── app.py                  # Streamlit web application
├── pyproject.toml         # Project configuration and dependencies
├── requirements.txt       # Legacy requirements file
└── src/
    ├── data/             # Data processing modules
    ├── pdf/              # PDF generation
    └── report/           # Report generation logic
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [ftbod](https://github.com/juanino/fbod) for the initial data summary report