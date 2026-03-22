# Fitbod Workout Data Analysis Tool

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/rhnfzl/fitbod-report/actions/workflows/python-package.yml/badge.svg)](https://github.com/rhnfzl/fitbod-report/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://fitbod-report.streamlit.app/)

Try it out here: [https://fitbod-report.streamlit.app/](https://fitbod-report.streamlit.app/)

A Streamlit-based web application that processes workout data exported from the [Fitbod](http://fitbod.me) app, generating structured reports in GPT, Markdown, JSON, YAML, and PDF formats. The tool provides daily, weekly, monthly, quarterly, and yearly summaries with exercise progression tracking and comprehensive workout analytics.

The tool was primarily created to make Fitbod data more AI-friendly. The structured reports can be fed into AI assistants like ChatGPT, Claude, or Gemini to:
- Analyse workout patterns
- Get personalised recommendations
- Identify areas for improvement
- Build new workout plans based on historical data
- Compare/Build your routines with reference fitness books/programs

**FitbodGPT Integration**: The default "GPT" export format is optimized for [FitbodGPT](https://github.com/rhnfzl/fitbod-gpt), a custom ChatGPT GPT that analyzes your Fitbod data and builds personalized workout plans. GPT exports stay weekly for FitbodGPT so coaching stays week-based. Export your report in GPT format, use the copy button or download it, then paste/upload it into FitbodGPT for science-backed training recommendations.

**Privacy First**: No data is stored on the server - uploaded files are processed in-memory and discarded after your session ends.

## Features

- **Interactive Web Interface**:
  - Easy-to-use Streamlit dashboard
  - File upload functionality
  - Date range selection
  - Real-time report preview

- **Flexible Report Options**:
  - Summary or detailed (set-by-set) reports
  - Metric and imperial units
  - Export to GPT (default, token-efficient weekly export for FitbodGPT), Markdown, JSON, YAML, or PDF
  - Daily, weekly, monthly, quarterly, half-yearly, yearly grouping
  - Calendar-aligned or rolling window aggregation

- **Comprehensive Analytics**:
  - Exercise-specific breakdowns
  - Period-over-period progress tracking
  - Set-by-set progression analysis
  - Warmup vs working set distinction
  - Cardio and strength session tracking

## Prerequisites

- Python 3.11 or higher
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
   uv run streamlit run app.py
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
└── src/
    ├── data/             # Data processing modules
    ├── pdf/              # PDF generation
    └── report/           # Report generation logic
```

## Use with FitbodGPT

Once you generate a report, you can paste it into [FitbodGPT](https://chatgpt.com/g/g-69bfd1becff08191b3b93c1d0312fda9-fitbodgpt) to get personalized training analysis and workout plans based on your data. It detects your experience level, identifies muscle group imbalances, infers your available equipment, and builds structured plans you can add as custom workouts back into Fitbod.

The GPT export format is designed for this. Generate your report, copy it, and paste it into the chat.

Source code: [fitbod-gpt on GitHub](https://github.com/rhnfzl/fitbod-gpt)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [ftbod](https://github.com/juanino/fbod) for the initial data summary report
