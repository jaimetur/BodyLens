import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("FRONTEND_DIR", str(ROOT / "frontend"))
    monkeypatch.setenv("BRANDING_DIR", str(ROOT / "branding"))
    monkeypatch.setenv("COOKIE_SECURE", "0")
    monkeypatch.setenv("SCHEDULER_ENABLED", "0")
    from app import config, db
    config.reload_settings()
    db.init_db()
    from app.security import login_throttle
    login_throttle._hits.clear()
    return tmp_path


@pytest.fixture()
def make_user(env):
    from app import db, users

    def _make(username, name=None, admin=False, password="contraseña-larga"):
        with db.tx() as con:
            return users.create_user(con, username, name or username.title(), password, is_admin=admin)
    return _make


@pytest.fixture()
def client(env):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        c.headers.update({"X-BodyLens": "1"})
        yield c


@pytest.fixture()
def login(client):
    def _login(username, password="contraseña-larga", c=None):
        from fastapi.testclient import TestClient
        from app.main import app
        c = c or TestClient(app)
        c.headers.update({"X-BodyLens": "1"})
        r = c.post("/api/login", json={"username": username, "password": password})
        assert r.status_code == 200, r.text
        return c
    return _login
