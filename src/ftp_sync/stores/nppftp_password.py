"""NppFTP password encryption: DES-CFB64 with the built-in key, hex encoded.

Mirrors Encryption::DES_encrypt in NppFTP's Encryption.cpp: the key gets odd parity and the
parity-adjusted key doubles as IV (OpenSSL DES_cfb64_encrypt with ivec = key, n = 0).
Only the default key is supported; a user-set NppFTP master password will fail to decrypt.
"""

from Crypto.Cipher import DES

from ftp_sync import constants


def _odd_parity(key: bytes) -> bytes:
    return bytes((b & 0xFE) | ((bin(b & 0xFE).count("1") + 1) % 2) for b in key)


def _cipher() -> "DES.DesCipher":  # type: ignore[name-defined]
    key = _odd_parity(constants.NPP_DEFAULT_KEY)
    return DES.new(key, DES.MODE_CFB, iv=key, segment_size=64)


def encrypt(password: str) -> str:
    if not password:
        return ""
    return bytes(_cipher().encrypt(password.encode("utf-8"))).hex().upper()


def decrypt(encrypted: str) -> str:
    if not encrypted:
        return ""
    return bytes(_cipher().decrypt(bytes.fromhex(encrypted))).decode("utf-8")
