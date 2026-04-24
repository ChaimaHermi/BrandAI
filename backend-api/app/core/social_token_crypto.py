"""Chiffrement au repos des jetons OAuth sociaux (Fernet, clé dérivée de SECRET_KEY)."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import settings


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_json_payload(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _fernet().encrypt(raw).decode("ascii")


def decrypt_json_payload(ciphertext: str) -> dict[str, Any]:
    raw = _fernet().decrypt(ciphertext.encode("ascii"))
    return json.loads(raw.decode("utf-8"))
