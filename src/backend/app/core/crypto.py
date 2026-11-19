"""Cifrado de secretos guardados en la base (tokens de Withings, token de envío de Apple Salud).

La clave sale de SECRET_KEY si está en el entorno; si no, el servidor crea una aleatoria la primera vez en
<DATA_DIR>/secrets/app.key (permisos 600) y la reutiliza. Nunca va al repositorio ni a los logs."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets

from cryptography.fernet import Fernet, InvalidToken

from app.core import config

_fernet: Fernet | None = None


def _key() -> bytes:
    env = os.environ.get("SECRET_KEY", "").strip()
    if env:
        return base64.urlsafe_b64encode(hashlib.sha256(env.encode()).digest())
    path = config.settings.data_dir / "secrets" / "app.key"
    if path.exists():
        return path.read_bytes().strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key)
    return key


def _f() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_key())
    return _fernet


def reset() -> None:
    """Para los tests (cambia DATA_DIR)."""
    global _fernet
    _fernet = None


def encrypt(obj) -> str:
    return _f().encrypt(json.dumps(obj).encode()).decode()


def decrypt(token: str | None):
    if not token:
        return None
    try:
        return json.loads(_f().decrypt(token.encode()))
    except (InvalidToken, ValueError):
        return None


def new_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)
