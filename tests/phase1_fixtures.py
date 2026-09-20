"""Route-only test app: temporary SQLite, no production lifespan or retrieval cache."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.evidence import router as evidence_router
from app.api.routes.for_you import router as for_you_router
from app.core.config import settings
from app.db.database import get_connection, init_database
from app.crawler.repository import init_notice_tables
from app.annotations.repository import init_annotation_tables
from app.models.obligation import CanonicalNoticeAnnotation
from app.actionability import DUT_TIMEZONE
from app.api.routes.for_you import get_actionability_now
from app.sources.repository import seed_sources
from datetime import datetime


@pytest.fixture
def phase1_client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'phase1.db'}")
    init_database()
    init_notice_tables()
    init_annotation_tables()
    seed_sources()
    annotation_dir = Path(__file__).resolve().parents[1] / "data/annotations/batch_001"
    annotations = [
        CanonicalNoticeAnnotation.model_validate_json((annotation_dir / name).read_text(encoding="utf-8"))
        for name in ("09_notice_13.json", "06_notice_24.json")
    ]
    with get_connection() as conn:
        for annotation in annotations:
            # Read-only reviewed inputs copied into a disposable test database.
            conn.execute("""
                INSERT INTO notices (notice_id, source_id, canonical_url, title,
                    publication_date, current_content_hash, first_observed_at,
                    last_observed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (annotation.notice_id, annotation.source.source_id, annotation.url,
                  annotation.title, str(annotation.publication_time), annotation.content_hash,
                  str(annotation.observed_at), str(annotation.observed_at),
                  str(annotation.observed_at), str(annotation.observed_at)))
            conn.execute("""
                INSERT INTO notice_versions (version_id, notice_id, raw_text,
                    content_hash, observed_at, fetched_at, raw_html_hash,
                    raw_html_path, attachment_links_json, parse_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (annotation.version_id, annotation.notice_id, annotation.raw_text,
                  annotation.content_hash, str(annotation.observed_at), str(annotation.observed_at),
                  "test-only", "test-only", "[]", "test-fixture"))

    app = FastAPI()
    app.include_router(evidence_router)
    app.include_router(for_you_router)
    app.dependency_overrides[get_actionability_now] = lambda: datetime(
        2026, 9, 20, 12, 0, tzinfo=DUT_TIMEZONE
    )
    app.state.repository = SimpleNamespace(cache={
        (a.notice_id, a.version_id): a for a in annotations
    })
    with TestClient(app) as client:
        yield client


@pytest.fixture
def frontend_http(phase1_client, monkeypatch):
    """Keep APIClient serialization/timeouts, dispatch HTTP to the real routes."""
    import streamlit as st
    from frontend.api_client import api_client

    calls = []

    def get(url, timeout):
        path = url.removeprefix(api_client.base_url)
        calls.append(("GET", path, None, timeout))
        return phase1_client.get(path)

    def post(url, json, timeout):
        path = url.removeprefix(api_client.base_url)
        calls.append(("POST", path, json, timeout))
        return phase1_client.post(path, json=json)

    monkeypatch.setattr("frontend.api_client.httpx.get", get)
    monkeypatch.setattr("frontend.api_client.httpx.post", post)
    st.cache_data.clear()
    yield calls
    st.cache_data.clear()
