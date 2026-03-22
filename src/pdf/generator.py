"""PDF generation utilities for workout reports."""

import re

from markdown_pdf import MarkdownPdf, Section


def _fix_heading_hierarchy(md):
    """Ensure headings never skip levels (e.g. h1 -> h3 without h2).

    The markdown-pdf library raises 'bad hierarchy level' when heading
    levels jump.  This normalises the tree so each heading is at most
    one level deeper than the previous one.
    """
    lines = md.split("\n")
    result = []
    prev_level = 0
    for line in lines:
        m = re.match(r"^(#{1,6})\s", line)
        if m:
            hashes = m.group(1)
            level = len(hashes)
            if prev_level == 0:
                target = 1
            else:
                target = min(level, prev_level + 1)
            line = "#" * target + line[level:]
            prev_level = target
        result.append(line)
    return "\n".join(result)


def convert_to_pdf(markdown_content, output_path):
    """Convert markdown content to PDF.

    Args:
        markdown_content: Markdown formatted string
        output_path: Path where to save the PDF file
    """
    pdf = MarkdownPdf()
    pdf.add_section(Section(_fix_heading_hierarchy(markdown_content)))
    pdf.save(output_path)
