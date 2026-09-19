import httpx
from datetime import datetime, timezone

from app.core.config import settings
from app.db.database import init_database
from app.models.source import SourceHealthStatus
from app.sources.health import check_source
from app.sources.repository import (
    get_source,
    list_sources,
    seed_sources,
)


def use_temp_database(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "test_unitrust.db"

    monkeypatch.setattr(
        settings,
        "database_url",
        f"sqlite:///{database_path}",
    )

    init_database()
    seed_sources()


def test_seed_source_registry(
    monkeypatch,
    tmp_path,
):
    use_temp_database(
        monkeypatch,
        tmp_path,
    )

    sources = list_sources()

    assert len(sources) == 3

    assert all(
        source.is_official
        for source in sources
    )

    ids = {
        source.source_id
        for source in sources
    }

    assert "dut_ctsv" in ids
    assert "dut_academic" in ids
    assert "dut_it_faculty" in ids


def test_startup_is_byte_idempotent(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    database = tmp_path / "test_unitrust.db"
    before = database.read_bytes()
    monkeypatch.setattr("app.sources.repository.utc_now", lambda: datetime(2040, 1, 1, tzinfo=timezone.utc))

    init_database()
    seed_sources()
    init_database()
    seed_sources()

    assert database.read_bytes() == before


def test_seed_updates_only_changed_metadata(monkeypatch, tmp_path):
    from app.db.database import get_connection
    from app.sources import repository
    from app.sources.seed import SEED_SOURCES

    use_temp_database(monkeypatch, tmp_path)
    before = {source.source_id: source for source in list_sources()}
    changed = SEED_SOURCES[0].model_copy(update={"expected_marker": None})
    monkeypatch.setattr(repository, "SEED_SOURCES", [changed, *SEED_SOURCES[1:]])
    changed_at = datetime(2040, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(repository, "utc_now", lambda: changed_at)
    seed_sources()
    after = {source.source_id: source for source in list_sources()}

    assert after[changed.source_id].expected_marker is None
    with get_connection() as connection:
        changed_timestamps = connection.execute(
            "SELECT created_at, updated_at FROM sources WHERE source_id = ?",
            (changed.source_id,),
        ).fetchone()
    assert changed_timestamps["updated_at"] == changed_at.isoformat()
    assert changed_timestamps["created_at"] != changed_timestamps["updated_at"]
    assert after[changed.source_id].health_status == before[changed.source_id].health_status
    for source in SEED_SOURCES[1:]:
        assert after[source.source_id] == before[source.source_id]

    # Restoring a nullable marker is a real change, too (SQL must be null-safe).
    monkeypatch.setattr(repository, "SEED_SOURCES", SEED_SOURCES)
    seed_sources()
    assert get_source(changed.source_id).expected_marker == SEED_SOURCES[0].expected_marker


def test_seed_inserts_missing_source_only(monkeypatch, tmp_path):
    from app.db.database import get_connection

    use_temp_database(monkeypatch, tmp_path)
    kept = get_source("dut_academic")
    with get_connection() as connection:
        connection.execute("DELETE FROM sources WHERE source_id = 'dut_ctsv'")
    seed_sources()
    assert get_source("dut_ctsv") is not None
    assert get_source("dut_academic") == kept


def test_healthy_source_check_with_mock(
    monkeypatch,
    tmp_path,
):
    use_temp_database(
        monkeypatch,
        tmp_path,
    )

    source = get_source("dut_ctsv")

    assert source is not None

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:

        content = (
            "THÔNG TIN - THÔNG BÁO "
            + ("Official DUT content " * 100)
        )

        return httpx.Response(
            status_code=200,
            text=content,
            request=request,
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        follow_redirects=True,
    ) as client:

        result = check_source(
            source,
            client=client,
        )

    assert (
        result.health_status
        == SourceHealthStatus.HEALTHY
    )

    assert result.http_status == 200
    assert result.content_hash is not None

    updated_source = get_source("dut_ctsv")

    assert updated_source is not None

    assert (
        updated_source.health_status
        == SourceHealthStatus.HEALTHY
    )
