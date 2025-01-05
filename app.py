"""Streamlit web application for Fitbod workout report generation."""
import os
import tempfile
from datetime import datetime
import streamlit as st
import pandas as pd
import time

from src.data.validator import validate_data_structure
from src.data.processor import process_data_from_df
from src.report.generator import (
    summarize_by_week,
    generate_markdown_report,
    get_available_timezones,
    detect_timezone,
    format_timezone_display
)
from src.pdf.generator import convert_to_pdf

def save_report(report_content, file_format='md'):
    """Save report content to a temporary file and return the path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as tmp_file:
        tmp_file.write(report_content.encode('utf-8'))
        return tmp_file.name

def monitor_performance(operation_name):
    """Monitor performance of operations."""
    start_time = time.time()
    return lambda: time.time() - start_time

@st.cache_data
def process_and_generate_report(filtered_df, unit_system, report_format, timezone, period_type=None):
    """Process data and generate report with caching for better performance."""
    timer = monitor_performance("Report Generation")
    
    # Process data in chunks for detailed reports
    if report_format == "detailed" and len(filtered_df) > 1000:
        chunk_size = 1000
        chunks = [filtered_df[i:i + chunk_size] for i in range(0, len(filtered_df), chunk_size)]
        
        processed_data = []
        progress_bar = st.progress(0)
        for i, chunk in enumerate(chunks):
            chunk_data = process_data_from_df(chunk)
            processed_data.extend(chunk_data)  # Use extend instead of append since we're dealing with lists
            progress_bar.progress((i + 1) / len(chunks))
        
        progress_bar.empty()
    else:
        processed_data = process_data_from_df(filtered_df)
    
    weekly_summary = summarize_by_week(
        processed_data, 
        use_metric=(unit_system == "metric"),
        timezone=timezone
    )
    
    report = generate_markdown_report(
        weekly_summary, 
        use_metric=(unit_system == "metric"), 
        report_format=report_format,
        period_type=period_type
    )
    
    duration = timer()
    if duration > 5:  # Threshold for slow operations
        st.warning(f"Report generation took {duration:.2f} seconds. Consider using the summary format or reducing the date range for better performance.")
    
    return report

@st.cache_data
def load_and_validate_data(file_data):
    """Cache the data loading and validation process."""
    df = pd.read_csv(file_data)
    is_valid, missing_cols = validate_data_structure(df, is_dataframe=True)
    if not is_valid:
        raise ValueError(f"Invalid CSV structure. Missing columns: {', '.join(missing_cols)}")
    return df

@st.cache_data
def prepare_date_filtered_data(df, start_date, end_date):
    """Cache the date filtering process."""
    # Convert dates only for filtering
    date_series = pd.to_datetime(df['Date'])
    mask = (date_series.dt.date >= start_date) & (date_series.dt.date <= end_date)
    filtered_df = df[mask].copy()
    
    # Apply timezone only to filtered data
    filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
    if filtered_df['Date'].dt.tz is None:
        filtered_df['Date'] = filtered_df['Date'].dt.tz_localize('UTC')
    
    return filtered_df

def handle_file_processing(uploaded_file):
    """Process uploaded file with comprehensive error handling."""
    try:
        with st.spinner("Processing file..."):
            return load_and_validate_data(uploaded_file), None
    except pd.errors.EmptyDataError:
        return None, "The uploaded file is empty"
    except pd.errors.ParserError:
        return None, "Invalid CSV format"
    except ValueError as ve:
        return None, str(ve)
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def setup_page_config():
    """Configure Streamlit page with enhanced settings."""
    st.set_page_config(
        page_title="Fitbod Report Generator",
        page_icon="💪",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/rhnfzl/fitbod-report/issues',
            'Report a bug': 'https://github.com/rhnfzl/fitbod-report/issues/new',
            'About': "Fitbod Workout Analysis Tool v1.0"
        }
    )

setup_page_config()

st.title("Fitbod Workout Report Generator 💪")
st.markdown("""
This tool helps you analyze your Fitbod workout data and generate comprehensive reports.
Upload your exported workout data to get started!

⚡ **Features**:
- Detailed workout analysis
- Weekly progress tracking
- Customizable report formats
- Multiple unit systems
""")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your Fitbod export (CSV file)", 
    type=['csv'],
    help="Upload the CSV file exported from your Fitbod app. To export: Open Fitbod app > Log > Settings > Export Workout Data"
)

if uploaded_file is not None:
    df, error = handle_file_processing(uploaded_file)
    if error:
        st.error(error)
        st.stop()
    
    try:
        # Get min and max dates without timezone conversion
        date_series = pd.to_datetime(df['Date'])
        min_date = date_series.min()
        max_date = date_series.max()
        
        # Date range selector
        st.subheader("Select Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date", 
                min_date.date(), 
                min_value=min_date.date(), 
                max_value=max_date.date(),
                help="Select the start date for your workout analysis"
            )
        with col2:
            end_date = st.date_input(
                "End Date", 
                max_date.date(), 
                min_value=min_date.date(), 
                max_value=max_date.date(),
                help="Select the end date for your workout analysis"
            )
            
        # Filter data based on date range with caching
        filtered_df = prepare_date_filtered_data(df, start_date, end_date)
        
        if filtered_df.empty:
            st.warning("No data available for the selected date range.")
            st.stop()
            
        # Report settings
        st.subheader("Report Settings")
        col3, col4, col5, col6 = st.columns(4)
        with col3:
            unit_system = st.selectbox(
                "Unit System", 
                ["metric", "imperial"], 
                index=0,
                help="Choose metric (kg, km) or imperial (lbs, miles) units for your report"
            )
        with col4:
            report_format = st.selectbox(
                "Report Format", 
                ["summary", "detailed"], 
                index=0,
                help="Summary: Key metrics and statistics only. Detailed: Includes set-by-set breakdown and exercise details"
            )
            # Add warning for detailed format
            if report_format == "detailed":
                weeks_count = (end_date - start_date).days // 7
                if weeks_count > 12:  # More than 12 weeks
                    st.warning("⚠️ Detailed reports for long periods may be slow. Consider using summary format or reducing the date range.")
        with col5:
            output_format = st.selectbox(
                "Output Format", 
                ["markdown", "pdf"], 
                index=0,
                help="Markdown: Text-based format ideal for sharing with AI tools. PDF: Formatted document for printing or sharing"
            )
        with col6:
            # Get all timezones
            available_timezones = get_available_timezones()
            
            # Format timezones for display
            formatted_timezones = [format_timezone_display(tz) for tz in available_timezones]
            
            # Try to get detected timezone from session state or detect it
            if 'detected_timezone_index' not in st.session_state:
                detected_tz = detect_timezone(available_timezones)
                st.session_state.detected_timezone_index = available_timezones.index(detected_tz)
            
            timezone_display = st.selectbox(
                "Timezone",
                formatted_timezones,
                index=st.session_state.detected_timezone_index,
                help="Select your timezone for accurate date and time handling in the report"
            )
            # Convert back to actual timezone name
            timezone = available_timezones[formatted_timezones.index(timezone_display)]
            
        # Additional report settings
        st.subheader("Summary Options")
        period_type = st.selectbox(
            "Summary Period",
            ["weekly", "monthly", "4-weeks", "8-weeks", "12-weeks", "24-weeks"],
            index=0,
            help="Choose how to group your workout data. Weekly shows week-by-week progress, while other options provide broader trends"
        )
            
        # Create columns for buttons
        btn_col1, btn_col2 = st.columns(2)
        
        # Initialize session state for report content if not exists
        if 'report_content' not in st.session_state:
            st.session_state.report_content = None
        
        with btn_col1:
            if st.button(
                "Generate Report",
                help="Click to generate your workout report based on the selected options"
            ):
                with st.spinner("Generating report..."):
                    # Process data and generate report using cached function
                    try:
                        st.session_state.report_content = process_and_generate_report(
                            filtered_df,
                            unit_system,
                            report_format,
                            timezone,
                            period_type
                        )
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
                        st.stop()
                    
                    # Save report based on selected format
                    if output_format == "markdown":
                        tmp_path = save_report(st.session_state.report_content, 'md')
                        with open(tmp_path, 'r') as f:
                            with btn_col2:
                                st.download_button(
                                    "Download Report",
                                    f.read(),
                                    file_name=f"workout_report_{datetime.now().strftime('%Y%m%d')}.md",
                                    mime="text/markdown",
                                    help="Download your report in Markdown format"
                                )
                        os.unlink(tmp_path)
                    else:  # PDF
                        # Generate PDF using markdown-pdf
                        pdf_path = os.path.join(tempfile.gettempdir(), f"workout_report_{datetime.now().strftime('%Y%m%d')}.pdf")
                        convert_to_pdf(st.session_state.report_content, pdf_path)
                        
                        with open(pdf_path, 'rb') as f:
                            with btn_col2:
                                st.download_button(
                                    "Download Report",
                                    f.read(),
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    help="Download your report in PDF format"
                                )
                        
                        # Clean up temporary file
                        os.unlink(pdf_path)
        
        # Preview the report (outside of button click handler)
        if st.session_state.report_content is not None:
            st.markdown("---")  # Add a visual separator
            st.subheader("Report Preview")
            # Display report in a code block for easy copying
            st.code(st.session_state.report_content, language='markdown', line_numbers=True)
            # Also show rendered version
            # st.markdown("### Rendered Preview")
            # st.markdown(report_content)
                
    except Exception as e:
        st.error(f"Error processing file: {str(e)}") 