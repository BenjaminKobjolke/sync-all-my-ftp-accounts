import random

import pytest

from ftp_sync.stores import nppftp_password, winscp_password


@pytest.mark.parametrize("password", ["secret", "pä$$ wörd!", "", "x" * 60])
def test_winscp_roundtrip(password: str) -> None:
    encrypted = winscp_password.encrypt("host.example", "bob", password)
    assert winscp_password.decrypt("host.example", "bob", encrypted) == password


def test_winscp_encrypt_is_hex_and_padded() -> None:
    encrypted = winscp_password.encrypt("h", "u", "pw", rng=random.Random(1))
    assert all(c in "0123456789ABCDEF" for c in encrypted)
    assert len(encrypted) >= 100  # WinSCP pads to PWALG_SIMPLE_MAXLEN chars


def test_winscp_decrypt_legacy_without_flag() -> None:
    # Old format: length byte first, no key prefix. Encode chars with WinSCP's char cipher.
    encode = winscp_password._encode_byte
    legacy = encode(2) + encode(0) + encode(ord("o")) + encode(ord("k"))
    assert winscp_password.decrypt("h", "u", legacy) == "ok"


@pytest.mark.parametrize("password", ["secret", "pä$$ wörd!", "a"])
def test_nppftp_roundtrip(password: str) -> None:
    encrypted = nppftp_password.encrypt(password)
    assert encrypted == encrypted.upper()
    assert len(encrypted) == 2 * len(password.encode("utf-8"))
    assert nppftp_password.decrypt(encrypted) == password


def test_nppftp_empty() -> None:
    assert nppftp_password.encrypt("") == ""
    assert nppftp_password.decrypt("") == ""
