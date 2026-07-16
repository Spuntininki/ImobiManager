"""Unit tests for the contract PDF renderer.

The renderer is DB-agnostic: it takes a ``converted_data`` dict (the pipeline's
output) and a ``style_config`` dict (loaded from a template row) and returns
PDF bytes. So these tests are pure — no session, no ORM models, no fixtures
— and run very fast.

Strategy: feed a minimal but real-shaped ``converted_data`` (three section
types) and assert the renderer (a) succeeds, (b) returns non-empty bytes
starting with the PDF magic header, (c) raises ``ValueError`` on an unknown
section type, and (d) tolerates inline markup ReportLab understands.
"""

import pytest

from app.services.contract_generation.renderer import build_styles, render


def _style_config() -> dict:
    """The minimum style dict the renderer needs (mirrors doc_style.json)."""
    return {
        "title": {"name": "TestTitle", "parent": "Title"},
        "paragh": {"name": "TestBody", "parent": "Normal", "alignment": 4},
        "sign_table": [
            ["ALIGN", [0, 0], [-1, -1], "CENTER"],
            ["FONTNAME", [0, 0], [-1, -1], "Helvetica-Bold"],
            ["FONTSIZE", [0, 0], [-1, -1], 12],
        ],
    }


def _converted_data(*, with_unknown: bool = False) -> dict:
    """A minimal converted_data dict with the three known section types."""
    data = {
        "title_lines": {"lines": ["CONTRATO DE TESTE"], "type": "title"},
        "content_lines": {
            "lines": [
                "Primeira cláusula do contrato, sem tokens.",
                "Segunda cláusula com <b>marcação bold</b> aceita pelo ReportLab.",
            ],
            "type": "paragh",
        },
        "sign_lines": {
            "lines": [
                ["LOCADOR", "LOCATÁRIO"],
                ["______________________", "______________________"],
                ["Fulano", "Beltrano"],
            ],
            "type": "sign",
        },
    }
    if with_unknown:
        data["weird"] = {"lines": ["x"], "type": "mystery"}
    return data


# --- build_styles -----------------------------------------------------------


def test_build_styles_returns_three_keys() -> None:
    styles = build_styles(_style_config())
    assert set(styles.keys()) == {"title", "paragh", "sign_table"}
    # Paragraph styles derive from the named sample-sheet parent.
    assert styles["title"].name == "TestTitle"
    assert styles["paragh"].name == "TestBody"
    # The alignment override flowed through.
    assert styles["paragh"].alignment == 4


# --- render: bytes shape ----------------------------------------------------


def test_render_returns_nonempty_pdf_bytes() -> None:
    pdf = render(_converted_data(), _style_config())
    assert isinstance(pdf, bytes)
    assert len(pdf) > 0
    # Every PDF document starts with %PDF- (magic header).
    assert pdf.startswith(b"%PDF-")


def test_render_returns_bytes_not_str() -> None:
    """The endpoint relies on bytes for StreamingResponse — guard the contract."""
    pdf = render(_converted_data(), _style_config())
    assert not isinstance(pdf, str)


# --- render: accepts inline markup ------------------------------------------


def test_render_handles_bold_markup_in_lines() -> None:
    """ReportLab Paragraph understands <b>...</b> inline; verify no exception."""
    data = _converted_data()
    data["content_lines"]["lines"] = [
        "Texto com <b>negrito</b> e <i>itálico</i> para o gerador."
    ]
    pdf = render(data, _style_config())
    assert pdf.startswith(b"%PDF-")


# --- render: unknown section type -------------------------------------------


def test_render_raises_on_unknown_section_type() -> None:
    with pytest.raises(ValueError, match="Unknown section type"):
        render(_converted_data(with_unknown=True), _style_config())


# --- render: empty converted_data -------------------------------------------


def test_render_empty_converted_data_still_produces_pdf() -> None:
    """No sections → empty story → still a valid (if tiny) PDF."""
    pdf = render({}, _style_config())
    assert pdf.startswith(b"%PDF-")


# --- render: sign section only ----------------------------------------------


def test_render_sign_only() -> None:
    """A converted_data with only a sign section should still render."""
    data = {
        "sign_lines": {
            "lines": [["LOCADOR", "LOCATÁRIO"], ["__", "__"], ["A", "B"]],
            "type": "sign",
        }
    }
    pdf = render(data, _style_config())
    assert pdf.startswith(b"%PDF-")
