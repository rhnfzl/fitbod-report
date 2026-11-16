"""PDF generation utilities for workout reports."""

import io
import re

import fitz
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


# Two MuPDF layout limits, both hit by real detailed reports:
# - cost grows superlinearly with the size of one section, so the report is
#   packed into small sections, split at h2-h4 headings;
# - a table taller than a page overflows it, and the layout can then loop
#   forever emitting pages (reproduced with pymupdf 1.27.1 and 2.1), so long
#   tables are cut into chunks that each repeat the header row.
_SECTION_MAX_CHARS = 20_000
_TABLE_MAX_ROWS = 30
# A section of _SECTION_MAX_CHARS fills a few dozen pages; far more means the
# layout is looping, and failing beats hanging the app.
_SECTION_MAX_PAGES = 500

_TABLE_SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")


def _chunk_tables(md, max_rows=_TABLE_MAX_ROWS):
    """Split markdown tables longer than max_rows, repeating the header."""
    lines = md.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and _TABLE_SEPARATOR.match(lines[i + 1]):
            header, separator = lines[i], lines[i + 1]
            out += [header, separator]
            i += 2
            rows = 0
            while i < len(lines) and lines[i].startswith("|"):
                if rows and rows % max_rows == 0:
                    out += ["", header, separator]
                out.append(lines[i])
                rows += 1
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _split_sections(md, max_chars=_SECTION_MAX_CHARS):
    """Split markdown at h2-h4 headings, packing the parts into sections.

    Headings are kept with their content, so a section never starts mid-table.
    A single oversized part is emitted as its own section rather than broken up.
    """
    parts = re.split(r"(?m)^(?=#{2,4} )", md)
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


class _GuardedMarkdownPdf(MarkdownPdf):
    """MarkdownPdf whose page loop stops instead of running forever."""

    def add_section(self, section, user_css=None):
        # Mirrors MarkdownPdf.add_section (markdown-pdf 1.13) with a page cap.
        where = section.rect + section.borders
        html = self.m_d.render(self.apply_plugins(section.text))
        story = fitz.Story(html=html, archive=section.root, user_css=user_css)
        more = 1
        while more:
            if section.page_count >= _SECTION_MAX_PAGES:
                raise RuntimeError("PDF layout did not finish; download the Markdown report instead.")
            self.page_num += 1
            section.page_count += 1
            device = self.writer.begin_page(section.rect)
            more, _ = story.place(where)
            story.element_positions(self._recorder, {"toc": section.toc, "pdfile": self})
            story.draw(device)
            self.writer.end_page()
        self.sections.append(section)
        return html


def _build_pdf(markdown_content):
    pdf = _GuardedMarkdownPdf()
    for section in _split_sections(_chunk_tables(_fix_heading_hierarchy(markdown_content))):
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
