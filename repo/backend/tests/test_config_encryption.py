from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.security import decrypt_config_secret


def test_decrypt_config_secret_with_enc_wrapper() -> None:
    key = Fernet.generate_key().decode("utf-8")
    token = Fernet(key.encode("utf-8")).encrypt(b"super-secret").decode("utf-8")
    value = decrypt_config_secret(f"ENC({token})", key)
    assert value == "super-secret"


def test_decrypt_config_secret_passthrough_for_plain_values() -> None:
    assert decrypt_config_secret("plain-text", None) == "plain-text"
