from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken

from .config import settings


_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = settings.credential_encryption_key
    # Accept both raw urlsafe base64 keys and plain strings (for local dev).
    try:
        # Validate base64 key length; Fernet expects 32 urlsafe-base64-encoded bytes.
        base64.urlsafe_b64decode(key)
        fernet_key = key.encode("utf-8")
    except Exception:
        # Derive a Fernet-compatible key from the configured string.
        padded = base64.urlsafe_b64encode(key.encode("utf-8").ljust(32, b"0")[:32])
        fernet_key = padded

    _fernet_instance = Fernet(fernet_key)
    return _fernet_instance


def encrypt_credential_payload(payload: Dict[str, Any]) -> bytes:
    fernet = _get_fernet()
    data = json.dumps(payload).encode("utf-8")
    return fernet.encrypt(data)


def decrypt_credential_payload(blob: bytes) -> Dict[str, Any]:
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(blob)
    except InvalidToken as exc:
        raise ValueError("Invalid credential payload") from exc
    return json.loads(decrypted.decode("utf-8"))


@dataclass
class DecryptedCourseCredentials:
    username: str
    password: str

