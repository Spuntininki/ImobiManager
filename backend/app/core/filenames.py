"""Generic filename sanitization helpers (cross-cutting, domain-free).

Pure utilities for reducing arbitrary text to a filename-safe ASCII slug.
Domain-specific filename assembly (e.g. contract PDF download names) belongs
in the relevant service module, composing these primitives.
"""

import re
import unicodedata

# Characters disallowed in filenames across common filesystems.
_ILLEGAL_FILENAME_CHARS = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


def to_ascii_filename_slug(text: str) -> str:
    """Reduce arbitrary text to a filename-safe ASCII slug.

    Deburr accents to their ASCII base (NFKD + ASCII-encode-ignore), then
    replace characters illegal across common filesystems and spaces with
    ``_``. Returns ``""`` when ``text`` yields no ASCII output.
    """
    deburred = unicodedata.normalize("NFKD", text)
    ascii_str = deburred.encode("ascii", "ignore").decode("ascii")
    sanitized = _ILLEGAL_FILENAME_CHARS.sub("_", ascii_str)
    return sanitized.replace(" ", "_")
