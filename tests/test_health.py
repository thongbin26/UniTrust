import sqlite3
from contextlib import closing

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.health import router
from app.core.config import settings
from app.db.database import database_is_ready


def test_health_endpoint(isolated_app_client):
    response = isolated_app_client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "UniTrust"
    assert data["database"] == "ok"


def test_health_does_not_create_missing_database(monkeypatch, tmp_path):
    database = tmp_path / "missing.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database}")
    assert not database_is_ready()
    assert not database.exists()


def test_health_rejects_empty_database(monkeypatch, tmp_path):
    database = tmp_path / "empty.db"
    with closing(sqlite3.connect(database)):
        pass
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database}")
    before = database.read_bytes()
    assert not database_is_ready()
    assert database.read_bytes() == before


def test_health_requires_initialized_components(monkeypatch):
    monkeypatch.setattr("app.api.routes.health.database_is_ready", lambda: True)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "degraded"
        app.state.startup_ready = True
        assert client.get("/health").json()["status"] == "ok"
        monkeypatch.setattr("app.api.routes.health.database_is_ready", lambda: False)
        result = client.get("/health").json()
        assert result["status"] == "degraded"
        assert result["database"] == "unavailable"


def test_health_readiness_is_read_only(isolated_runtime_artifacts):
    database = isolated_runtime_artifacts["database_path"]
    before = database.read_bytes()
    assert database_is_ready()
    assert database_is_ready()
    assert database.read_bytes() == before
