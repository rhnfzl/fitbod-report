from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd

from src.data.validator import validate_data_structure
from src.data.processor import process_data_from_df
from src.report.generator import (
    summarize_by_week,
    generate_markdown_report,
    detect_timezone
)
from src.pdf.generator import convert_to_pdf

async def generate_report(request):
    """Generate report endpoint."""
    try:
        form = await request.form()
        file = form['file']
        unit_system = form.get('unit_system', 'metric')
        report_format = form.get('report_format', 'summary')
        timezone = form.get('timezone', detect_timezone())
        
        # Read the uploaded file
        df = pd.read_csv(file.file)
        
        # Validate data structure
        if not validate_data_structure(df):
            return JSONResponse({
                'error': 'Invalid data structure in the uploaded file'
            }, status_code=400)
        
        # Process data
        processed_data = process_data_from_df(df)
        
        # Generate report
        if report_format == 'summary':
            weekly_summary = summarize_by_week(processed_data)
            report_content = generate_markdown_report(weekly_summary, unit_system, timezone)
        else:
            report_content = generate_markdown_report(processed_data, unit_system, timezone)
        
        return JSONResponse({
            'report': report_content,
            'status': 'success'
        })
    except Exception as e:
        return JSONResponse({
            'error': str(e)
        }, status_code=500)

# Define routes
routes = [
    Route('/api/generate-report', generate_report, methods=['POST'])
]

# Define middleware
middleware = [
    Middleware(CORSMiddleware,
              allow_origins=['*'],
              allow_methods=['POST'],
              allow_headers=['*'])
]

# Create UV application
app = Starlette(
    debug=True,
    routes=routes,
    middleware=middleware
)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000) 