# PDF Generation Module Documentation

## Overview

The PDF generation module converts markdown reports into formatted PDF documents using the markdown-pdf library. It maintains the structure and formatting while providing a professional PDF output.

## Modules

### generator.py

Handles PDF conversion and formatting.

#### Functions

`convert_to_pdf_bytes(markdown_content)`
- **Purpose**: Converts markdown content to PDF in memory (used by the web app, so no report touches disk)
- **Returns**: the PDF as `bytes`
- **Process**:
  1. Normalises heading levels
  2. Cuts tables longer than 30 rows into chunks that repeat the header (MuPDF can loop forever on a table taller than a page)
  3. Packs the report into ~20 KB sections split at h2-h4 headings (layout cost grows superlinearly with section size)
  4. Renders each section with a page cap, raising `RuntimeError` instead of hanging

`convert_to_pdf(markdown_content, output_path)`
- Same, but writes the PDF to `output_path`. For command-line and test use.

## PDF Features

1. **Document Structure**:
   - Table of Contents
   - Section headers
   - Page numbers
   - Consistent formatting

2. **Content Formatting**:
   - Tables
   - Lists
   - Code blocks
   - Text styling

3. **Layout**:
   - A4 page size
   - Readable margins
   - Proper spacing
   - Clear hierarchy

## Implementation Details

### Markdown to PDF Process

1. **Content Preparation**:
   ```python
   pdf = MarkdownPdf()
   pdf.add_section(Section(markdown_content))
   ```

2. **PDF Generation**:
   ```python
   pdf.save(output_path)
   ```

### Supported Elements

1. **Text Elements**:
   - Headers (H1-H6)
   - Paragraphs
   - Bold/Italic
   - Links

2. **Structural Elements**:
   - Tables
   - Lists
   - Blockquotes
   - Horizontal rules

3. **Data Elements**:
   - Workout tables
   - Progress metrics
   - Exercise details

## Best Practices

1. **Content Preparation**:
   - Validate markdown syntax
   - Check for special characters
   - Ensure proper formatting

2. **File Handling**:
   - Use temporary files
   - Clean up after generation
   - Handle path issues

3. **Error Handling**:
   - Check file permissions
   - Validate output path
   - Handle conversion errors

## Common Issues

1. **Formatting Issues**:
   - Table alignment
   - Special characters
   - Long content wrapping

2. **File Issues**:
   - Permission denied
   - Path not found
   - File in use

3. **Content Issues**:
   - Invalid markdown
   - Missing content
   - Broken links

## Usage Examples

1. **Basic Conversion**:
   ```python
   convert_to_pdf("# Title\nContent", "output.pdf")
   ```

2. **With Error Handling**:
   ```python
   try:
       convert_to_pdf(content, path)
   except Exception as e:
       handle_error(e)
   ```

3. **Temporary Files**:
   ```python
   with tempfile.NamedTemporaryFile() as tmp:
       convert_to_pdf(content, tmp.name)
   ```

## Dependencies

- markdown-pdf>=0.1.2
- PyMuPDF (backend)
- markdown-it-py (markdown parsing) 