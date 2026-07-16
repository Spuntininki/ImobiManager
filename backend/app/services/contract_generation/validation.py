"""Validate contract templates against the registered formatters.

When the template lives in Postgres, edits made via SQL/UI can't be caught
by code review, so silent bugs become possible — a template references a
token no formatter is registered for, and the ``<REPLACE>...</REPLACE>`` text
survives verbatim into the rendered PDF.

``validate_template`` is the loud-failure guard. The pipeline must call it
once per template load (before token-filling) so the first contract generated
after a bad edit fails loudly with a precise error, instead of silently
producing a malformed PDF.

Checks (first violation wins):

1. Every section in ``content`` has a known ``type``
   (``title`` / ``paragh`` / ``sign``).
2. Every ``<REPLACE>token</REPLACE>`` referenced in the section lines has an
   entry under the template's ``replace`` key.
3. Every token in ``replace`` flagged ``computed: true`` has a registered
   formatter (a key in ``formatters``).
4. Every non-computed token declares ``colum`` and ``table``.
5. Each token's ``document_type`` (when present) is a valid
   ``DocumentType`` enum value.
"""

import re

from app.models.enums import DocumentType

# Section types the renderer knows how to dispatch on.
_KNOWN_SECTION_TYPES = frozenset({"title", "paragh", "sign"})

# Matches ``<REPLACE>token</REPLACE>`` tokens in template lines.
_TOKEN_RE = re.compile(r"<REPLACE>(.*?)</REPLACE>")


def validate_template(template: dict, formatters: dict) -> None:
    """Validate a contract template against the registered formatters.

    Raises ``ValueError`` on the first violation; returns ``None`` on success.
    Idempotent and side-effect free, so the pipeline can call it cheaply each
    time a template is loaded from the DB.
    """
    content = template.get("content")
    replace = template.get("replace")
    if not isinstance(content, dict) or not isinstance(replace, dict):
        raise ValueError(
            "Template must have 'content' and 'replace' top-level dicts"
        )

    # 1. Section types must be known to the renderer.
    for section_name, section in content.items():
        if not isinstance(section, dict) or "type" not in section:
            raise ValueError(f"Section '{section_name}' must have a 'type' field")
        section_type = section["type"]
        if section_type not in _KNOWN_SECTION_TYPES:
            raise ValueError(
                f"Section '{section_name}' has unknown type {section_type!r}; "
                f"expected one of {sorted(_KNOWN_SECTION_TYPES)}"
            )

    # 2. Every token referenced in the prose must exist in `replace`.
    for section_name, section in content.items():
        for line in section.get("lines", []):
            _check_tokens_referenced(line, section_name, replace)

    # 3-5. Validate each entry in `replace`.
    for token, entry in replace.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Token {token!r} entry must be a dict")
        if entry.get("computed") and token not in formatters:
            raise ValueError(
                f"Token {token!r} is marked computed but has no registered formatter"
            )
        if "table" not in entry:
            raise ValueError(f"Token {token!r} is missing 'table'")
        if not entry.get("computed") and "colum" not in entry:
            raise ValueError(f"Token {token!r} is missing 'colum'")
        if "document_type" in entry:
            _check_document_type(entry["document_type"], token)


def _check_tokens_referenced(line, section_name: str, replace: dict) -> None:
    """Recurse into list-of-strings lines (the sign block is a nested list)."""
    if isinstance(line, str):
        for token in _TOKEN_RE.findall(line):
            if token not in replace:
                raise ValueError(
                    f"Token {token!r} referenced in section '{section_name}' "
                    "has no entry under 'replace'"
                )
    elif isinstance(line, list):
        for item in line:
            _check_tokens_referenced(item, section_name, replace)


def _check_document_type(value, token: str) -> None:
    """Document-type tokens must reference a valid DocumentType enum member."""
    try:
        DocumentType(value)
    except ValueError as e:
        raise ValueError(
            f"Token {token!r} has invalid document_type {value!r}"
        ) from e
