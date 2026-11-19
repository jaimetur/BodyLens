"""Configuración leída de variables de entorno (nunca secretos en el código)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# raíz del repositorio (src/backend/app/core/config.py → ../../../..)
ROOT = Path(__file__).resolve().parents[4]


def _bool(v: str | None, default: bool) -> bool:
    if v is None or v == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "si", "sí", "on")


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", "/data")))
    frontend_dir: Path = field(default_factory=lambda: Path(os.environ.get("FRONTEND_DIR", str(ROOT / "src" / "frontend"))))
    branding_dir: Path = field(default_factory=lambda: Path(os.environ.get("BRANDING_DIR", str(ROOT / "assets" / "branding"))))
    # README*.md, CHANGELOG.md and help/<lang>/ (the Help module): the repository root, /app/docs in the image and
    # /app/code (the deployed commit) on the NAS
    docs_dir: Path = field(default_factory=lambda: Path(os.environ.get("DOCS_DIR", str(ROOT))))
    vendor_dir: Path = field(default_factory=lambda: Path(os.environ.get("VENDOR_DIR", str(ROOT / "src" / "frontend" / "vendor"))))
    public_url: str = field(default_factory=lambda: os.environ.get("PUBLIC_URL", "").rstrip("/"))
    # cookies «Secure» salvo que se desactive a propósito (desarrollo en http://localhost)
    cookie_secure: bool = field(default_factory=lambda: _bool(os.environ.get("COOKIE_SECURE"), True))
    session_days: int = field(default_factory=lambda: int(os.environ.get("SESSION_DAYS", "90")))
    sync_interval_min: int = field(default_factory=lambda: int(os.environ.get("SYNC_INTERVAL_MIN", "15")))
    scheduler_enabled: bool = field(default_factory=lambda: _bool(os.environ.get("SCHEDULER_ENABLED"), True))
    google_sa_json: str = field(default_factory=lambda: os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""))
    # cuenta de administración que se crea sola si la base está vacía (contraseña provisional: se cambia al entrar)
    admin_username: str = field(default_factory=lambda: os.environ.get("BODYLENS_ADMIN_USER", ""))
    admin_name: str = field(default_factory=lambda: os.environ.get("BODYLENS_ADMIN_NAME", "Administración"))
    admin_email: str = field(default_factory=lambda: os.environ.get("BODYLENS_ADMIN_EMAIL", ""))
    admin_password: str = field(default_factory=lambda: os.environ.get("BODYLENS_ADMIN_PASSWORD", "bodylens"))
    invite_days: int = field(default_factory=lambda: int(os.environ.get("INVITE_DAYS", "7")))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "bodylens.db"

    def user_dir(self, user_id: int) -> Path:
        d = self.data_dir / "users" / str(int(user_id))
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()


def reload_settings() -> Settings:
    """Vuelve a leer el entorno (para los tests)."""
    global settings
    settings = Settings()
    return settings
