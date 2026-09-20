import shutil
import sqlite3
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.crawler.identity import normalize_url, official_notice_id
from app.crawler.repository import (
    init_notice_tables,
    migrate_notice_discoveries,
    save_notice,
)
from app.db.database import get_connection, init_database
from app.models.notice import CrawledNotice
from app.sources.repository import seed_sources


def configure_empty_database(monkeypatch, tmp_path):
    database = tmp_path / "step17c.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database}")
    init_database()
    seed_sources()
    init_notice_tables()
    migrate_notice_discoveries()
    return database


def notice(*, source_id="dut_training_quality", external_id="9001", url=None, title="Thông báo cùng tiêu đề", body="Nội dung gốc", observed=None, attachments=None):
    observed = observed or datetime(2026, 9, 20, tzinfo=timezone.utc)
    url = url or f"https://dut.udn.vn/Phong/Daotao/Thongbao/id/{external_id}"
    from app.crawler.dut_parser import build_content_hash

    attachment_links = attachments or []
    return CrawledNotice(
        source_id=source_id,
        external_id=external_id,
        canonical_url=url,
        title=title,
        publication_date=None,
        raw_text=body,
        attachment_links=attachment_links,
        observed_at=observed,
        fetched_at=observed,
        content_hash=build_content_hash(title, None, body, attachment_links),
        raw_html_hash="raw-" + external_id,
        raw_html_path=f"tmp/{external_id}.html",
        parse_mode="body",
    )


def test_migrate_real_legacy_database_twice_preserves_notice_and_versions(
    monkeypatch, tmp_path
):
    source = __import__("pathlib").Path(__file__).resolve().parents[1] / "unitrust.db"
    staging = tmp_path / "legacy-copy.db"
    shutil.copy2(source, staging)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{staging}")

    with sqlite3.connect(staging) as connection:
        notice_ids_before = [row[0] for row in connection.execute("SELECT notice_id FROM notices ORDER BY notice_id")]
        versions_before = list(connection.execute("SELECT * FROM notice_versions ORDER BY version_id"))

    migrate_notice_discoveries()
    migrate_notice_discoveries()

    with sqlite3.connect(staging) as connection:
        notice_ids_after = [row[0] for row in connection.execute("SELECT notice_id FROM notices ORDER BY notice_id")]
        versions_after = list(connection.execute("SELECT * FROM notice_versions ORDER BY version_id"))
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert notice_ids_before == notice_ids_after == list(range(1, 31))
    assert versions_before == versions_after
    assert "notice_discoveries" in tables
    assert integrity == "ok"
    assert foreign_keys == []


def test_shared_id_collapses_mirror_and_keeps_two_discoveries(monkeypatch, tmp_path):
    configure_empty_database(monkeypatch, tmp_path)
    first = notice()
    mirror = notice(
        source_id="dut_academic",
        url="https://dut.udn.vn/Tintuc/Thongbao/id/9001",
        body="Mirror chrome must not become a version",
    )

    assert save_notice(first, discovery_source_id="dut_training_quality") == "CREATED"
    assert save_notice(mirror, discovery_source_id="dut_academic") == "DUPLICATE"
    assert save_notice(mirror, discovery_source_id="dut_academic") == "DUPLICATE"

    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM notice_versions").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM notice_discoveries").fetchone()[0] == 2


def test_same_numeric_id_in_different_resource_namespace_does_not_merge(
    monkeypatch, tmp_path
):
    configure_empty_database(monkeypatch, tmp_path)
    other_resource = notice(
        url="https://dut.udn.vn/Vanban/id/9001",
        body="Văn bản có namespace riêng",
    )
    official_notice = notice(
        url="https://dut.udn.vn/Phong/Daotao/Thongbao/id/9001",
        body="Thông báo chính thức",
    )

    assert official_notice_id(other_resource.canonical_url) is None
    assert official_notice_id(official_notice.canonical_url) == (
        "dut.udn.vn:thongbao:9001"
    )
    assert save_notice(other_resource) == "CREATED"
    assert save_notice(official_notice) == "CREATED"

    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM notice_versions").fetchone()[0] == 2


def test_same_title_different_ids_do_not_merge_and_tracking_url_does(monkeypatch, tmp_path):
    configure_empty_database(monkeypatch, tmp_path)
    assert save_notice(notice(external_id="9101")) == "CREATED"
    assert save_notice(notice(external_id="9102")) == "CREATED"
    tracked = notice(
        external_id="9101",
        url="https://dut.udn.vn/Phong/Daotao/Thongbao/id/9101?utm_source=facebook&fbclid=x",
    )
    assert save_notice(tracked, discovery_source_id="dut_sv_portal") == "UNCHANGED"

    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 2
    assert normalize_url(tracked.canonical_url).endswith("/Thongbao/id/9101")


def test_content_versions_are_idempotent_and_attachments_do_not_create_notice(monkeypatch, tmp_path):
    configure_empty_database(monkeypatch, tmp_path)
    first = notice(attachments=["https://drive.google.com/file/d/abc/view"])
    same = first.model_copy(update={"observed_at": first.observed_at + timedelta(hours=1)})
    changed = notice(body="Nội dung đã đổi", observed=first.observed_at + timedelta(hours=2))

    assert save_notice(first) == "CREATED"
    assert save_notice(same) == "UNCHANGED"
    assert save_notice(changed) == "UPDATED"

    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM notice_versions").fetchone()[0] == 2


def test_deleting_discovery_cannot_delete_canonical_notice_or_version(monkeypatch, tmp_path):
    configure_empty_database(monkeypatch, tmp_path)
    save_notice(notice())
    with get_connection() as connection:
        connection.execute("DELETE FROM notice_discoveries")
        connection.commit()
        assert connection.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM notice_versions").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_presentation_badge_cleanup_does_not_create_false_version(monkeypatch, tmp_path):
    configure_empty_database(monkeypatch, tmp_path)
    legacy = notice(title="Thông báo tiếng Anh Hot")
    cleaned = notice(title="Thông báo tiếng Anh", observed=legacy.observed_at + timedelta(hours=1))

    assert save_notice(legacy) == "CREATED"
    assert save_notice(cleaned) == "UNCHANGED"
    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM notice_versions").fetchone()[0] == 1
