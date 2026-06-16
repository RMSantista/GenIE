"""Tests for AES-256-GCM encryption and the encrypted key vault."""

import os

import pytest

from spec.core.exceptions import InvalidConfig, StorageError
from spec.core.security import KeyVault, SecretCipher, mask_secret


@pytest.fixture
def cipher() -> SecretCipher:
    return SecretCipher(os.urandom(32))


def test_encrypt_decrypt_roundtrip(cipher: SecretCipher) -> None:
    secret = "AIzaSyA-example-key-1234567890"
    blob = cipher.encrypt(secret)

    assert secret.encode() not in blob
    assert cipher.decrypt(blob) == secret


def test_encrypt_is_non_deterministic(cipher: SecretCipher) -> None:
    blob1 = cipher.encrypt("same-secret")
    blob2 = cipher.encrypt("same-secret")

    assert blob1 != blob2


def test_tampered_ciphertext_fails(cipher: SecretCipher) -> None:
    blob = bytearray(cipher.encrypt("secret"))
    blob[-1] ^= 0xFF

    with pytest.raises(StorageError):
        cipher.decrypt(bytes(blob))


def test_wrong_key_fails(cipher: SecretCipher) -> None:
    other = SecretCipher(os.urandom(32))
    blob = cipher.encrypt("secret")

    with pytest.raises(StorageError):
        other.decrypt(blob)


def test_master_key_must_be_32_bytes() -> None:
    with pytest.raises(InvalidConfig):
        SecretCipher(b"short")


def test_sign_and_verify(cipher: SecretCipher) -> None:
    signature = cipher.sign("job-1:output.json:123")

    assert cipher.verify("job-1:output.json:123", signature)
    assert not cipher.verify("job-1:output.json:124", signature)
    assert not cipher.verify("job-1:output.json:123", signature[:-2] + "ff")


def test_mask_secret_hides_content() -> None:
    masked = mask_secret("sk-ant-veryverysecret")

    assert masked.startswith("sk-a")
    assert "secret" not in masked
    assert mask_secret("short") == "••••••••"


class TestKeyVault:
    @pytest.fixture
    def vault(self, tmp_path) -> KeyVault:
        return KeyVault(str(tmp_path / "vault.db"), SecretCipher(os.urandom(32)))

    def test_store_and_retrieve(self, vault: KeyVault) -> None:
        masked = vault.store("google", "AIzaSyExample123456")

        assert masked.startswith("AIza")
        assert vault.has("google")
        assert vault.masked("google") == masked
        assert vault.get_plaintext("google") == "AIzaSyExample123456"

    def test_plaintext_never_on_disk(self, vault: KeyVault, tmp_path) -> None:
        vault.store("openai", "sk-supersecret-key-material")

        raw = (tmp_path / "vault.db").read_bytes()
        assert b"sk-supersecret-key-material" not in raw

    def test_overwrite_key(self, vault: KeyVault) -> None:
        vault.store("google", "first-key-value")
        vault.store("google", "second-key-value")

        assert vault.get_plaintext("google") == "second-key-value"

    def test_delete(self, vault: KeyVault) -> None:
        vault.store("anthropic", "sk-ant-example")

        assert vault.delete("anthropic")
        assert not vault.has("anthropic")
        assert vault.get_plaintext("anthropic") is None
        assert not vault.delete("anthropic")

    def test_empty_key_rejected(self, vault: KeyVault) -> None:
        with pytest.raises(InvalidConfig):
            vault.store("google", "   ")
