"""PDF generation utilities for workout reports."""
from markdown_pdf import MarkdownPdf, Section

def convert_to_pdf(markdown_content, output_path):
    """Convert markdown content to PDF.
    
    Args:
        markdown_content: Markdown formatted string
        output_path: Path where to save the PDF file
    """
    pdf = MarkdownPdf()
    pdf.add_section(Section(markdown_content))
    pdf.save(output_path)