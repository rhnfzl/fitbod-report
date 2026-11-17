"""Tests for browser embedding and PDF rendering."""

import json

from src.pdf.generator import _fix_heading_hierarchy, convert_to_pdf_bytes
from src.utils.web import js_string_literal


class TestJsStringLiteral:
    def test_script_close_tag_cannot_break_out(self):
        """A </script> in the report must not terminate the script element.

        Exercise names come from the uploaded CSV and are emitted verbatim into
        the report, so this is reachable with a crafted export.
        """
        payload = "</script><img src=x onerror=alert(1)>"
        encoded = js_string_literal(payload)

        assert "</script>" not in encoded
        assert "<" not in encoded
        assert ">" not in encoded

    def test_value_round_trips_unchanged(self):
        """Escaping must not corrupt the report the button copies."""
        for text in (
            "</script>",
            "plain text",
            "quotes \" and ' and backslash \\",
            "unicode: café 日本語 <>&",
            "newlines\nand\ttabs",
            "line separator   and paragraph separator  ",
        ):
            assert json.loads(js_string_literal(text)) == text

    def test_line_separators_escaped(self):
        """U+2028/U+2029 are literal line breaks in JS strings and must be escaped."""
        encoded = js_string_literal("a b c")

        assert " " not in encoded
        assert " " not in encoded
        assert "\\u2028" in encoded

    def test_ampersand_escaped(self):
        assert "&" not in js_string_literal("a & b")

    def test_result_is_a_quoted_literal(self):
        encoded = js_string_literal("hello")
        assert encoded.startswith('"') and encoded.endswith('"')


class TestPdf:
    def test_returns_non_empty_pdf_bytes(self):
        data = convert_to_pdf_bytes("# Title\n\nSome body text.\n")

        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF-")
        assert len(data) > 500

    def test_heading_hierarchy_never_skips_levels(self):
        """markdown-pdf raises 'bad hierarchy level' when heading levels jump."""
        fixed = _fix_heading_hierarchy("# One\n\n### Three\n\n##### Five\n")
        levels = [len(line.split(" ")[0]) for line in fixed.split("\n") if line.startswith("#")]

        assert levels == [1, 2, 3]

    def test_renders_a_report_with_skipped_headings(self):
        """The generator emits h1 then h3, which previously raised."""
        data = convert_to_pdf_bytes("# Report\n\n### Detail\n\n| a | b |\n| - | - |\n| 1 | 2 |\n")

        assert data.startswith(b"%PDF-")
