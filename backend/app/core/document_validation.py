"""Check-digit validation for CPF and CNPJ (including alphanumeric CNPJ)."""

from typing import Final

_CNPJ_WEIGHTS_FIRST: Final[tuple[int, ...]] = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_WEIGHTS_SECOND: Final[tuple[int, ...]] = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CPF_WEIGHTS_FIRST: Final[tuple[int, ...]] = (10, 9, 8, 7, 6, 5, 4, 3, 2)
_CPF_WEIGHTS_SECOND: Final[tuple[int, ...]] = (11, 10, 9, 8, 7, 6, 5, 4, 3, 2)


def _cnpj_char_value(c: str) -> int:
    """Convert a CNPJ character to its numeric value per RFB spec (ASCII code minus 48).

    0-9 → 0-9, A-Z → 17-42.
    """
    code = ord(c)
    if 48 <= code <= 57:  # 0-9
        return code - 48
    if 65 <= code <= 90:  # A-Z
        return code - 48
    raise ValueError(f"Invalid CNPJ character: '{c}'")


def is_valid_cpf(cpf: str) -> bool:
    """Validate CPF check digits (módulo 11).

    Expects a stripped string of exactly 11 digits. Returns False for
    repeated-digit numbers (e.g. 111.111.111-11) or wrong check digits.
    """
    if not cpf.isdigit() or len(cpf) != 11:
        return False
    # Reject all identical digits.
    if cpf == cpf[0] * 11:
        return False

    # First check digit.
    total = sum(int(cpf[i]) * _CPF_WEIGHTS_FIRST[i] for i in range(9))
    first = (total * 10) % 11
    if first == 10:
        first = 0
    if first != int(cpf[9]):
        return False

    # Second check digit.
    total = sum(int(cpf[i]) * _CPF_WEIGHTS_SECOND[i] for i in range(10))
    second = (total * 10) % 11
    if second == 10:
        second = 0
    return second == int(cpf[10])


def is_valid_cnpj(cnpj: str) -> bool:
    """Validate CNPJ check digits (módulo 11), supporting alphanumeric (ASCII-48).

    Expects a stripped string of exactly 14 characters (0-9, A-Z).
    Returns False for repeated-character numbers or wrong check digits.
    """
    if len(cnpj) != 14:
        return False
    # Reject all identical characters.
    if cnpj == cnpj[0] * 14:
        return False

    try:
        # First check digit.
        total = sum(_cnpj_char_value(cnpj[i]) * _CNPJ_WEIGHTS_FIRST[i] for i in range(12))
        first = 0 if total % 11 < 2 else 11 - (total % 11)
        if first != _cnpj_char_value(cnpj[12]):
            return False

        # Second check digit.
        total = sum(_cnpj_char_value(cnpj[i]) * _CNPJ_WEIGHTS_SECOND[i] for i in range(13))
        second = 0 if total % 11 < 2 else 11 - (total % 11)
        return second == _cnpj_char_value(cnpj[13])
    except ValueError:
        return False
