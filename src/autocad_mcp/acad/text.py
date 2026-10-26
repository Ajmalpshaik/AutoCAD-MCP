"""Plain text from MText (Lee Mac's UnFormat String idea, Heron's own code).

MText stores formatting inline: fonts, heights, colours, underline, stacked
fractions and grouping braces. Searches, counts and comparisons need the words
only, so this strips the codes and keeps the escaped characters.
"""

from __future__ import annotations

import re

_SLASH, _OPEN, _CLOSE = "\x00S", "\x00O", "\x00C"
_STACK = re.compile(r"\\S([^;]*?)[\^#/]([^;]*?);")
_VALUE_CODES = re.compile(r"\\[ACcFfHQTWp][^;\\]*;")
_SWITCH_CODES = re.compile(r"\\[LlOoKk]")


def unformat(text: str, keep_paragraphs: bool = False) -> str:
    """The words of an MText string, without its formatting codes.

    keep_paragraphs: True keeps \\P line breaks (for writing the text back);
    False turns them into spaces (for searching and counting).
    """
    s = str(text).replace("\\\\", _SLASH).replace("\\{", _OPEN).replace("\\}", _CLOSE)
    s = _STACK.sub(r"\1/\2", s)
    s = _VALUE_CODES.sub("", s)
    s = _SWITCH_CODES.sub("", s)
    s = s.replace("\\~", " ").replace("\\X", "\\P")
    s = s.replace("\\P", "\x00P") if keep_paragraphs else s.replace("\\P", " ")
    s = s.replace("{", "").replace("}", "")
    s = s.replace("\x00P", "\\P").replace(_SLASH, "\\").replace(_OPEN, "{").replace(_CLOSE, "}")
    return re.sub(r"[ \t]+", " ", s).strip()
