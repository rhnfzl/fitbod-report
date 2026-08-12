"""PDF generation utilities for workout reports."""

import io
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


# Rendering cost grows superlinearly with the size of a single section: a
# 100 KB report renders in half a second, 200 KB in one section had not
# finished after several minutes. Splitting the same content into sections of
# roughly this size renders it in under a second.
_SECTION_MAX_CHARS = 40_000


def _split_sections(md, max_chars=_SECTION_MAX_CHARS):
    """Split markdown on top-level headings, packing into sections.

    Headings are kept with their content, so a section never starts mid-table.
    Content before the first heading, and any single oversized block, is
    emitted as its own section rather than being broken up.
    """
    parts = re.split(r"(?m)^(?=## )", md)
    sections = []
    current = ""
    for part in parts:
        if current and len(current) + len(part) > max_chars:
            sections.append(current)
            current = part
        else:
            current += part
    if current:
        sections.append(current)
    return sections or [md]


def _build_pdf(markdown_content):
    pdf = MarkdownPdf()
    for section in _split_sections(_fix_heading_hierarchy(markdown_content)):
        pdf.add_section(Section(section))
    return pdf


def convert_to_pdf_bytes(markdown_content):
    """Convert markdown content to PDF and return the bytes.

    Kept in memory deliberately.  The web app serves every user from one
    process, so writing reports to a shared temp path let one session read
    another's file.

    Args:
        markdown_content: Markdown formatted string

    Returns:
        bytes: the rendered PDF
    """
    buffer = io.BytesIO()
    _build_pdf(markdown_content).save_bytes(buffer)
    return buffer.getvalue()


def convert_to_pdf(markdown_content, output_path):
    """Convert markdown content to PDF and write it to output_path.

    Retained for command-line and test use.  The web app uses
    convert_to_pdf_bytes so that no report ever touches disk.

    Args:
        markdown_content: Markdown formatted string
        output_path: Path where to save the PDF file
    """
    _build_pdf(markdown_content).save(output_path)
