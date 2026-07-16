"""Tests for the contract_templates model, validation guard, and seed data.

Two layers:

* ``validate_template`` is the safety guard that catches template/formatter
  drift at load time — every check has a positive case and at least one
  negative case. Pure (no DB), fast.
* The seeded fixture + DB round-trip prove the model writes and reads back
  the JSONB columns, so Phase 4's pipeline can rely on the shape.
* ``default_template`` smoke tests confirm the inlined JSON parses and has
  the top-level keys the pipeline expects — catches typos in the migration
  seed and the test fixture alike.
"""


import pytest

from app.services.contract_generation.default_template import (
    load_default_content,
    load_default_style,
)
from app.services.contract_generation.validation import validate_template

# --- fake formatters used by validate_template tests -----------------------


def _fake_formatter(_obj) -> str:
    return "fake"


_FAKE_FORMATTERS = {
    "owner_cpf": _fake_formatter,
    "owner_rg": _fake_formatter,
    "local_type": _fake_formatter,
    "unknown_thing": _fake_formatter,
}


# --- helpers ---------------------------------------------------------------


def _valid_template() -> dict:
    """A minimal template that passes all validate_template checks."""
    return {
        "content": {
            "title_lines": {"lines": ["TITLE"], "type": "title"},
            "content_lines": {
                "lines": [
                    "Text with <REPLACE>local_type</REPLACE> here.",
                    ["<REPLACE>owner_cpf</REPLACE>", "<REPLACE>owner_rg</REPLACE>"],
                ],
                "type": "paragh",
            },
            "sign_lines": {"lines": [["A", "B"]], "type": "sign"},
        },
        "replace": {
            "local_type": {"colum": "type", "table": "addresses", "computed": True},
            "owner_cpf": {
                "colum": "document",
                "table": "owner_documents",
                "document_type": "CPF",
                "computed": True,
            },
            "owner_rg": {
                "colum": "document",
                "table": "owner_documents",
                "document_type": "RG",
                "computed": True,
            },
        },
    }


# --- validate_template: positive cases -------------------------------------


def test_validate_template_accepts_valid_template() -> None:
    """A well-formed template + matching formatters returns None (no raise)."""
    validate_template(_valid_template(), _FAKE_FORMATTERS)


def test_validate_template_accepts_default_seeded_content() -> None:
    """The actual migration seed ('standard') must validate against a registry
    keyed like the production FORMATTERS — this is a smoke test for the
    end-to-end load flow.
    """
    # Build a fake formatters dict whose keys are every 'computed' token in
    # the seeded template.
    content = load_default_content()
    fake = {token: _fake_formatter for token, e in content["replace"].items() if e.get("computed")}
    validate_template(content, fake)


# --- validate_template: top-level shape ------------------------------------


def test_validate_template_rejects_missing_content_key() -> None:
    bad = _valid_template()
    del bad["content"]
    with pytest.raises(ValueError, match="content"):
        validate_template(bad, _FAKE_FORMATTERS)


def test_validate_template_rejects_missing_replace_key() -> None:
    bad = _valid_template()
    del bad["replace"]
    with pytest.raises(ValueError, match="replace"):
        validate_template(bad, _FAKE_FORMATTERS)


# --- validate_template: section type ---------------------------------------


def test_validate_template_rejects_unknown_section_type() -> None:
    bad = _valid_template()
    bad["content"]["title_lines"]["type"] = "weird"
    with pytest.raises(ValueError, match="unknown type"):
        validate_template(bad, _FAKE_FORMATTERS)


def test_validate_template_rejects_section_without_type() -> None:
    bad = _valid_template()
    del bad["content"]["title_lines"]["type"]
    with pytest.raises(ValueError, match="must have a 'type'"):
        validate_template(bad, _FAKE_FORMATTERS)


# --- validate_template: referenced tokens must exist in replace -----------


def test_validate_template_rejects_token_not_in_replace() -> None:
    bad = _valid_template()
    bad["content"]["title_lines"]["lines"] = ["<REPLACE>missing_token</REPLACE>"]
    with pytest.raises(ValueError, match="no entry under 'replace'"):
        validate_template(bad, _FAKE_FORMATTERS)


def test_validate_template_rejects_nested_token_not_in_replace() -> None:
    """Sign-section nested lists must be walked too."""
    bad = _valid_template()
    bad["content"]["sign_lines"]["lines"] = [["<REPLACE>missing</REPLACE>", "B"]]
    with pytest.raises(ValueError, match="no entry under 'replace'"):
        validate_template(bad, _FAKE_FORMATTERS)


# --- validate_template: computed tokens must have a formatter --------------


def test_validate_template_rejects_computed_without_formatter() -> None:
    bad = _valid_template()
    bad["replace"]["new_thing"] = {"colum": "name", "table": "owners", "computed": True}
    bad["content"]["title_lines"]["lines"].append("<REPLACE>new_thing</REPLACE>")
    # Need to remove 'unknown_thing' from fake formatters so it triggers
    formatters = {k: v for k, v in _FAKE_FORMATTERS.items() if k != "unknown_thing"}
    with pytest.raises(ValueError, match="no registered formatter"):
        validate_template(bad, formatters)


# --- validate_template: non-computed tokens must have colum+table ---------


def test_validate_template_rejects_non_computed_without_colum() -> None:
    bad = _valid_template()
    bad["replace"]["owner_name"] = {"table": "owners"}  # missing 'colum'
    bad["content"]["title_lines"]["lines"].append("<REPLACE>owner_name</REPLACE>")
    with pytest.raises(ValueError, match="missing 'colum'"):
        validate_template(bad, _FAKE_FORMATTERS)


def test_validate_template_rejects_entry_without_table() -> None:
    bad = _valid_template()
    bad["replace"]["owner_name"] = {"colum": "name"}  # missing 'table'
    bad["content"]["title_lines"]["lines"].append("<REPLACE>owner_name</REPLACE>")
    with pytest.raises(ValueError, match="missing 'table'"):
        validate_template(bad, _FAKE_FORMATTERS)


# --- validate_template: document_type must be a valid enum ----------------


def test_validate_template_rejects_invalid_document_type() -> None:
    bad = _valid_template()
    bad["replace"]["owner_cpf"]["document_type"] = "PASSPORT"
    with pytest.raises(ValueError, match="invalid document_type"):
        validate_template(bad, _FAKE_FORMATTERS)


# --- default_template smoke tests ------------------------------------------


def test_load_default_content_has_top_level_keys() -> None:
    content = load_default_content()
    assert "content" in content
    assert "replace" in content
    assert isinstance(content["content"], dict)
    assert isinstance(content["replace"], dict)


def test_load_default_content_has_three_sections() -> None:
    content = load_default_content()
    assert set(content["content"].keys()) == {"title_lines", "content_lines", "sign_lines"}
    for section in content["content"].values():
        assert "type" in section
        assert "lines" in section


def test_load_default_style_has_section_keys() -> None:
    style = load_default_style()
    assert set(style.keys()) == {"title", "paragh", "sign_table"}
    assert "parent" in style["title"]
    assert "parent" in style["paragh"]
    assert isinstance(style["sign_table"], list)


# --- DB round-trip — relies on the seeded_standard_template fixture --------


async def test_seeded_standard_template_round_trips(
    seeded_standard_template,
) -> None:
    """The 'standard' row inserted by the fixture reads back with the same
    JSONB content/style shape we asked it to insert.
    """
    tpl = seeded_standard_template
    assert tpl.code == "standard"
    assert tpl.is_active is True
    assert "content" in tpl.content
    assert "replace" in tpl.content
    assert "title" in tpl.style
    assert "paragh" in tpl.style
    assert "sign_table" in tpl.style
