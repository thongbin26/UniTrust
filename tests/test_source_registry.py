import httpx

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