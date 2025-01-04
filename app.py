"""Streamlit web application for Fitbod workout report generation."""
import os
import tempfile
from datetime import datetime
import streamlit as st
import pandas as pd
import time

from src.data.validator import validate_data_structure
from src.data.processor import process_data_from_df
from src.report.generator import summarize_by_week, generate_markdown_report, get_available_timezones
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
def process_and_generate_report(filtered_df, unit_system, report_format, timezone):
    """Process data and generate report with caching for better performance."""
    timer = monitor_performance("Report Generation")
    
    processed_data = process_data_from_df(filtered_df)
    weekly_summary = summarize_by_week(
        processed_data, 
        use_metric=(unit_system == "metric"),
        timezone=timezone
    )
    report = generate_markdown_report(
        weekly_summary, 
        use_metric=(unit_system == "metric"), 
        report_format=report_format
    )
    
    duration = timer()
    if duration > 5:  # Threshold for slow operations
        st.warning(f"Report generation took {duration:.2f} seconds. Consider reducing the date range for better performance.")
    
    return report

def handle_file_processing(uploaded_file):
    """Process uploaded file with comprehensive error handling."""
    try:
        with st.spinner("Processing file..."):
            df = pd.read_csv(uploaded_file)
            if df.empty:
                return None, "The uploaded file is empty"
            return df, None
    except pd.errors.EmptyDataError:
        return None, "The uploaded file is empty"
    except pd.errors.ParserError:
        return None, "Invalid CSV format"
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
uploaded_file = st.file_uploader("Upload your Fitbod export (CSV file)", type=['csv'])

if uploaded_file is not None:
    df, error = handle_file_processing(uploaded_file)
    if error:
        st.error(error)
        st.stop()
    
    try:
        is_valid, missing_cols = validate_data_structure(df, is_dataframe=True)
        
        if not is_valid:
            st.error(f"Invalid CSV structure. Missing columns: {', '.join(missing_cols)}")
            st.stop()
            
        # Convert dates to datetime for filtering
        df['Date'] = pd.to_datetime(df['Date'])
        # Add timezone information if not present
        if df['Date'].dt.tz is None:
            df['Date'] = df['Date'].dt.tz_localize('UTC')
            
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        
        # Date range selector
        st.subheader("Select Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date.date(), min_value=min_date.date(), max_value=max_date.date())
        with col2:
            end_date = st.date_input("End Date", max_date.date(), min_value=min_date.date(), max_value=max_date.date())
            
        # Filter data based on date range
        mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
        filtered_df = df[mask]
        
        if filtered_df.empty:
            st.warning("No data available for the selected date range.")
            st.stop()
            
        # Report settings
        st.subheader("Report Settings")
        col3, col4, col5, col6 = st.columns(4)
        with col3:
            unit_system = st.selectbox("Unit System", ["metric", "imperial"], index=0)
        with col4:
            report_format = st.selectbox("Report Format", ["summary", "detailed"], index=0)
        with col5:
            output_format = st.selectbox("Output Format", ["markdown", "pdf"], index=0)
        with col6:
            # Get all timezones
            available_timezones = get_available_timezones()
            # Set default to Europe/Amsterdam (should be first in the list)
            default_index = 0  # Europe/Amsterdam is first in our new list
            
            # Add region separators in the UI
            def format_timezone(tz):
                if '/' in tz:
                    region, city = tz.split('/', 1)
                    return f"{region} - {city.replace('_', ' ')}"
                return tz
            
            formatted_timezones = [format_timezone(tz) for tz in available_timezones]
            timezone_display = st.selectbox(
                "Timezone",
                formatted_timezones,
                index=default_index,
                help="Select your timezone for accurate date handling"
            )
            # Convert back to actual timezone name
            timezone = available_timezones[formatted_timezones.index(timezone_display)]
            
        if st.button("Generate Report"):
            with st.spinner("Generating report..."):
                # Process data and generate report using cached function
                report_content = process_and_generate_report(
                    filtered_df,
                    unit_system,
                    report_format,
                    timezone
                )
                
                # Save report based on selected format
                if output_format == "markdown":
                    tmp_path = save_report(report_content, 'md')
                    with open(tmp_path, 'r') as f:
                        st.download_button(
                            "Download Report",
                            f.read(),
                            file_name=f"workout_report_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown"
                        )
                    os.unlink(tmp_path)
                else:  # PDF
                    # Generate PDF using markdown-pdf
                    pdf_path = os.path.join(tempfile.gettempdir(), f"workout_report_{datetime.now().strftime('%Y%m%d')}.pdf")
                    convert_to_pdf(report_content, pdf_path)
                    
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            "Download Report",
                            f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf"
                        )
                    
                    # Clean up temporary file
                    os.unlink(pdf_path)
                
                # Preview the report
                st.subheader("Report Preview")
                # Display report in a code block for easy copying
                st.code(report_content, language='markdown', line_numbers=True)
                # Also show rendered version
                # st.markdown("### Rendered Preview")
                # st.markdown(report_content)
                
    except Exception as e:
        st.error(f"Error processing file: {str(e)}") 