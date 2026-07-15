"""PDF renderer for the contract generator.

This module is the *render phase* of the pipeline — it knows nothing about
the database, ``doc_content.json``, or how ``converted_data`` was built. Its
only inputs are:

* ``converted_data`` — the pure-data dict produced by ``generate_contract.py``:
  ``{section_name: {"lines": [...], "type": "title"|"paragh"|"sign"}}``.
* ``style_config`` — ``doc_style.json`` loaded as a dict.

Dispatch is keyed on the ``type`` of each section, so there are exactly three
render paths (title / paragh / sign) regardless of how many tokens the contract
template grows to. Styling lives entirely in ``doc_style.json``; tweaking
layout is a JSON edit, not a code change.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_styles(style_config: dict) -> dict:
    """Translate ``doc_style.json`` into ReportLab style objects.

    Returns a dict keyed by section type::

        {"title": ParagraphStyle, "paragh": ParagraphStyle,
         "sign_table": TableStyle}

    Paragraph styles (``title`` / ``paragh``) are declared in JSON as
    ``{"name", "parent", <overrides...>}`` — the same shape the old
    ``sign_style`` entry used. The ``parent`` value names a built-in
    ``getSampleStyleSheet()`` entry to derive from (e.g. ``"Title"``,
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


def render(converted_data: dict, style_config: dict, output_path: Path) -> None:
    """Build a contract PDF from ``converted_data``.

    Iterates ``converted_data`` sections in insertion order (Python dicts
    preserve order), dispatches on ``section["type"]`` to the matching
    flowable, and writes the result to ``output_path``.

    Structural gaps that are layout rather than styling are hardcoded here:
    A4 page size and the ``Spacer`` separating the body paragraphs from the
    signature table. These are flowable/page concerns; the JSON rules style
    of *content* (fonts, alignment, padding), not document scaffolding.
    """
    styles = build_styles(style_config)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
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
