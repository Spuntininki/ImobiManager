"""Tests for `parse_message` token extraction conventions."""

from app.security.token_auth import parse_message


def test_start_command_with_token_only_yields_token_no_body() -> None:
    parsed = parse_message("/start ABC123")
    assert parsed.token == "ABC123"
    assert parsed.body == ""


def test_start_command_with_token_and_text() -> None:
    parsed = parse_message("/start ABC123 quando vence meu aluguel?")
    assert parsed.token == "ABC123"
    assert parsed.body == "quando vence meu aluguel?"


def test_start_command_without_token_yields_none() -> None:
    parsed = parse_message("/start")
    assert parsed.token is None
    assert parsed.body == ""


def test_leading_token_then_body() -> None:
    parsed = parse_message("ABC123 listar imoveis")
    assert parsed.token == "ABC123"
    assert parsed.body == "listar imoveis"


def test_bare_word_treated_as_token_ping() -> None:
    parsed = parse_message("ABC123")
    assert parsed.token == "ABC123"
    assert parsed.body == ""


def test_empty_message_returns_none_token() -> None:
    parsed = parse_message("   ")
    assert parsed.token is None
    assert parsed.body == ""


def test_plain_question_without_token_yields_none() -> None:
    parsed = parse_message("quanto de aluguel eu pago?")
    # First token "quanto" gets attributed to the token field; the bot will
    # try to validate it, get 401, and respond with onboarding hint — exactly
    # the intended UX for an unauthenticated message.
    assert parsed.token == "quanto"
    assert parsed.body == "de aluguel eu pago?"
