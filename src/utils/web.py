"""Helpers for embedding data in the HTML the app injects into the browser."""

import json


def js_string_literal(text):
    """Encode text as a JavaScript string literal that is safe inside <script>.

    json.dumps escapes quotes and backslashes but leaves "<", ">" and "&"
    alone.  The HTML parser closes a <script> element at a literal </script>
    regardless of JavaScript string context, so a report containing that
    sequence - an exercise name from the uploaded CSV is enough - would end the
    script early and let the remainder be parsed as HTML.

    U+2028 and U+2029 are also escaped: they are literal line terminators
    inside JavaScript string literals and would raise a syntax error.

    Args:
        text: Arbitrary text to embed.

    Returns:
        str: A quoted JavaScript string literal, safe to concatenate into a
        <script> element.
    """
    return (
        json.dumps(text)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
