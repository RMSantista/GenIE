"""Security utilities: AES-256-GCM encryption and encrypted API key vault.

The master key is resolved in this order:
1. ``GENIE_MASTER_KEY`` environment variable (base64, 32 bytes)
2. ``{data_dir}/.master_key`` file (auto-generated on first run, mode 0600)

API keys are encrypted at rest in SQLite and are NEVER returned in
plaintext by any API endpoint — only a masked preview (first 4 chars).
"""

import base64
import hashlib
import hmac
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from spec.core.config import get_settings
from spec.core.exceptions import InvalidConfig, StorageError

logger = logging.getLogger(__name__)

_MASTER_KEY_BYTES = 32
_NONCE_BYTES = 12


def _load_or_create_master_key(data_dir: str, env_value: Optional[str]) -> bytes:
    """Resolve the 32-byte master key from env or key file.

    Args:
        data_dir: Data directory for the fallback key file
        env_value: Value of GENIE_MASTER_KEY env var (base64) or None

    Returns:
        bytes: 32-byte master key

    Raises:
        InvalidConfig: If the env value is malformed
    """

    if env_value:
        try:
            key = base64.b64decode(env_value)
        except Exception as e:
            raise InvalidConfig(f"GENIE_MASTER_KEY is not valid base64: {e}")
        if len(key) != _MASTER_KEY_BYTES:
            raise InvalidConfig(
                "GENIE_MASTER_KEY must decode to exactly 32 bytes "
                "(generate with: openssl rand -base64 32)"
            )
        return key

    key_path = Path(data_dir) / ".master_key"
    if key_path.exists():
        key = key_path.read_bytes()
        if len(key) != _MASTER_KEY_BYTES:
            raise InvalidConfig(f"Corrupt master key file: {key_path}")
        return key

    key = os.urandom(_MASTER_KEY_BYTES)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    os.chmod(key_path, 0o600)
    logger.warning(
        "Generated new master key at %s (mode 0600). "
        "Set GENIE_MASTER_KEY env var for production deployments.",
        key_path,
    )
    return key


class SecretCipher:
    """AES-256-GCM encryption helper bound to the application master key."""

    def __init__(self, master_key: bytes) -> None:
        """Initialize the cipher.

        Args:
            master_key: 32-byte symmetric key
        """

        if len(master_key) != _MASTER_KEY_BYTES:
            raise InvalidConfig("Master key must be 32 bytes")
        self._aesgcm = AESGCM(master_key)
        self._master_key = master_key

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a string, returning nonce-prefixed ciphertext.

        Args:
            plaintext: Secret to encrypt

        Returns:
            bytes: nonce (12 bytes) + ciphertext + GCM tag
        """

        nonce = os.urandom(_NONCE_BYTES)
        return nonce + self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    def decrypt(self, blob: bytes) -> str:
        """Decrypt nonce-prefixed ciphertext back to a string.

        Args:
            blob: nonce + ciphertext + tag as produced by encrypt()

        Returns:
            str: Decrypted secret

        Raises:
            StorageError: If decryption fails (wrong key or corrupt data)
        """

        try:
            nonce, ciphertext = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
            return self._aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as e:
            raise StorageError(f"Failed to decrypt secret: {e}")

    def sign(self, message: str) -> str:
        """Compute an HMAC-SHA256 signature for short-lived signed URLs.

        Args:
            message: Message to sign

        Returns:
            str: Hex-encoded signature
        """

        return hmac.new(
            self._master_key, message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def verify(self, message: str, signature: str) -> bool:
        """Verify an HMAC-SHA256 signature in constant time.

        Args:
            message: Original message
            signature: Hex signature to check

        Returns:
            bool: True if the signature is valid
        """

        return hmac.compare_digest(self.sign(message), signature)


def mask_secret(secret: str) -> str:
    """Build a safe masked preview of a secret (first 4 chars + bullets).

    Args:
        secret: Secret value

    Returns:
        str: Masked preview, e.g. "AIza••••"
    """

    prefix = secret[:4] if len(secret) > 8 else ""
    return f"{prefix}{'•' * 8}"


class KeyVault:
    """Encrypted, persistent store for LLM provider API keys.

    Keys are encrypted with AES-256-GCM before hitting disk (SQLite).
    Plaintext is only ever materialized in memory, on demand, for
    outbound provider calls.
    """

    def __init__(self, db_path: str, cipher: SecretCipher) -> None:
        """Initialize the vault.

        Args:
            db_path: Path to the SQLite database file
            cipher: Cipher used for encryption at rest
        """

        self._db_path = db_path
        self._cipher = cipher
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self._db_path, timeout=10)

    def _init_db(self) -> None:
        """Create the api_keys table if missing and restrict file perms."""

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    provider TEXT PRIMARY KEY,
                    ciphertext BLOB NOT NULL,
                    masked TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
        try:
            os.chmod(self._db_path, 0o600)
        except OSError:
            pass

    def store(self, provider: str, key: str) -> str:
        """Encrypt and persist an API key for a provider.

        Args:
            provider: Provider name (e.g. "google")
            key: Plaintext API key

        Returns:
            str: Masked preview of the stored key
        """

        if not key or not key.strip():
            raise InvalidConfig("API key cannot be empty")

        key = key.strip()
        masked = mask_secret(key)
        blob = self._cipher.encrypt(key)

        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO api_keys (provider, ciphertext, masked, created_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(provider) DO UPDATE SET "
                "ciphertext=excluded.ciphertext, masked=excluded.masked, "
                "created_at=excluded.created_at",
                (provider, blob, masked, int(time.time())),
            )

        logger.info("Stored encrypted API key for provider: %s", provider)
        return masked

    def get_plaintext(self, provider: str) -> Optional[str]:
        """Decrypt and return a provider key for internal outbound calls.

        NEVER expose the return value through any API response or log.

        Args:
            provider: Provider name

        Returns:
            Optional[str]: Plaintext key or None if absent
        """

        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT ciphertext FROM api_keys WHERE provider = ?", (provider,)
            ).fetchone()

        if row is None:
            return None
        return self._cipher.decrypt(row[0])

    def masked(self, provider: str) -> Optional[str]:
        """Return the masked preview for a provider key.

        Args:
            provider: Provider name

        Returns:
            Optional[str]: Masked preview or None if absent
        """

        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT masked FROM api_keys WHERE provider = ?", (provider,)
            ).fetchone()
        return row[0] if row else None

    def has(self, provider: str) -> bool:
        """Check whether a key exists for a provider.

        Args:
            provider: Provider name

        Returns:
            bool: True if a key is stored
        """

        return self.masked(provider) is not None

    def delete(self, provider: str) -> bool:
        """Remove a provider key.

        Args:
            provider: Provider name

        Returns:
            bool: True if a key was deleted
        """

        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM api_keys WHERE provider = ?", (provider,))
        deleted = cur.rowcount > 0
        if deleted:
            logger.info("Deleted API key for provider: %s", provider)
        return deleted


_cipher: Optional[SecretCipher] = None
_vault: Optional[KeyVault] = None


def get_cipher() -> SecretCipher:
    """Get the global SecretCipher singleton.

    Returns:
        SecretCipher: Cipher bound to the application master key
    """

    global _cipher
    if _cipher is None:
        settings = get_settings()
        master = _load_or_create_master_key(settings.data_dir, settings.master_key)
        _cipher = SecretCipher(master)
    return _cipher


def get_key_vault() -> KeyVault:
    """Get the global KeyVault singleton.

    Returns:
        KeyVault: Encrypted API key store
    """

    global _vault
    if _vault is None:
        settings = get_settings()
        _vault = KeyVault(settings.db_path, get_cipher())
    return _vault


def reset_security_singletons() -> None:
    """Reset cached cipher/vault (used by tests)."""

    global _cipher, _vault
    _cipher = None
    _vault = None
