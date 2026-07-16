"""PDF renderer for the contract generation pipeline.

This module is the *render phase* — it knows nothing about the database, the
contract template, or how ``converted_data`` was built. Its only inputs are:

* ``converted_data`` — the pure-data dict produced by the pipeline:
  ``{section_name: {"lines": [...], "type": "title"|"paragh"|"sign"}}``.
* ``style_config`` — ``doc_style`` JSON loaded from a ``contract_templates``
  row, already parsed as a dict.

Dispatch is keyed on the ``type`` of each section, so there are exactly three
render paths (title / paragh / sign) regardless of how many tokens the
contract template grows to. Styling lives entirely in the style dict;
tweaking layout is a row edit, not a code change.

``render`` returns PDF bytes (not a file path) so the HTTP endpoint can stream
them directly back to the browser via ``StreamingResponse``.
"""

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_styles(style_config: dict) -> dict:
    """Translate the style dict into ReportLab style objects.

    Returns a dict keyed by section type::

        {"title": ParagraphStyle, "paragh": ParagraphStyle,
         "sign_table": TableStyle}

    Paragraph styles (``title`` / ``paragh``) are declared in the style dict
    as ``{"name", "parent", <overrides...>}``. The ``parent`` value names a
    built-in ``getSampleStyleSheet()`` entry to derive from (e.g. ``"Title"``,
    ``"Normal"``); any other keys are forwarded as constructor kwargs so
    overrides (e.g. ``"alignment": 4``) come from the data, not the code.

    The sign block is a Table, so its style is a flat list of TableStyle
    commands — passed verbatim (already in ReportLab's command tuple form).
    """
    sample = getSampleStyleSheet()
    styles: dict = {}

    for section_type in ("title", "paragh"):
        entry = style_config[section_type]
        parent = sample[entry["parent"]]
        overrides = {k: v for k, v in entry.items() if k not in ("name", "parent")}
        styles[section_type] = ParagraphStyle(name=entry["name"], parent=parent, **overrides)

    styles["sign_table"] = TableStyle(style_config["sign_table"])
    return styles


def render(converted_data: dict, style_config: dict) -> bytes:
    """Build a contract PDF from ``converted_data`` and return it as bytes.

    Iterates ``converted_data`` sections in insertion order (Python dicts
    preserve order), dispatches on ``section["type"]`` to the matching
    flowable, and returns the rendered PDF as a bytestring.

    A4 page size and the ``Spacer`` separating the body paragraphs from the
    signature table are structural scaffolding hardcoded here — they are
    flowable/page concerns, not content style. The style dict rules style
    of *content* (fonts, alignment, padding), not document layout.
    """
    styles = build_styles(style_config)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story: list = []

    for section in converted_data.values():
        section_type = section["type"]
        if section_type == "title":
            for line in section["lines"]:
                story.append(Paragraph(line, styles["title"]))
        elif section_type == "paragh":
            for line in section["lines"]:
                story.append(Paragraph(line, styles["paragh"]))
        elif section_type == "sign":
            story.append(Spacer(0.5 * inch, 0.5 * inch))
            story.append(Table(section["lines"], style=styles["sign_table"]))
        else:
            raise ValueError(f"Unknown section type: {section_type!r}")

    doc.build(story)
    return buffer.getvalue()
