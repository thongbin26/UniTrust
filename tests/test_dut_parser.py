from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from app.crawler.dut_parser import (
    extract_notice_links,
    parse_notice_detail,
)


FIXTURES = (
    Path(__file__).parent
    / "fixtures"
)


def read_fixture(
    name: str,
) -> str:

    return (
        FIXTURES
        / name
    ).read_text(
        encoding="utf-8"
    )


def test_extract_listing_links():

    html = read_fixture(
        "dut_listing.html"
    )

    links = extract_notice_links(
        html=html,
        listing_url=(
            "https://dut.udn.vn/"
            "Tintuc/Thongbaods/gid/dt"
        ),
        official_domain=(
            "dut.udn.vn"
        ),
    )

    assert len(links) == 2

    assert (
        links[0].external_id
        == "123"
    )

    assert (
        links[1].external_id
        == "124"
    )


def test_parse_notice_detail():

    html = read_fixture(
        "dut_detail.html"
    )

    now = datetime.now(
        timezone.utc
    )

    notice = parse_notice_detail(
        html=html,
        source_id="dut_academic",
        final_url=(
            "https://dut.udn.vn/"
            "Tintuc/Thongbao/id/123"
        ),
        observed_at=now,
        fetched_at=now,
        raw_html_hash="abc",
        raw_html_path=(
            "data/raw/test.html"
        ),
    )

    assert (
        notice.external_id
        == "123"
    )

    assert (
        "tiếng Anh"
        in notice.title
    )

    assert (
        notice.publication_date
        is not None
    )

    assert (
        "450.000"
        in notice.raw_text
    )

    assert (
        "không thuộc bài viết"
        not in notice.raw_text
    )

    assert (
        len(
            notice.attachment_links
        )
        == 1
    )

    assert (
        notice.content_hash
    )


def test_student_portal_discovers_official_details_without_duplicates():
    links = extract_notice_links(
        html=read_fixture("dut_student_portal.html"),
        listing_url="https://sv1.dut.udn.vn/",
        official_domain="dut.udn.vn",
    )

    assert [link.external_id for link in links] == ["12279", "12280"]
    assert all("example.org" not in link.url for link in links)


def test_parser_handles_missing_date_and_content_without_inventing_date():
    now = datetime.now(timezone.utc)
    notice = parse_notice_detail(
        html="<html><head><title>Thông báo tiếng Việt</title></head><body></body></html>",
        source_id="dut_finance",
        final_url="https://dut.udn.vn/Phong/Taichinh/Thongbao/id/9001",
        observed_at=now,
        fetched_at=now,
        raw_html_hash="abc",
        raw_html_path="tmp/detail.html",
    )

    assert notice.publication_date is None
    assert notice.raw_text == "Thông báo tiếng Việt"
    assert notice.parse_mode == "title_only"


def test_listing_parser_tolerates_malformed_html_and_relative_links():
    links = extract_notice_links(
        html='<div><a href="/Phong/CTSV/Thongbao/id/77">Thông báo học bổng',
        listing_url="https://dut.udn.vn/Phong/CTSV/Thongbaods/gids/1013",
        official_domain="dut.udn.vn",
    )

    assert len(links) == 1
    assert links[0].url == "https://dut.udn.vn/Phong/CTSV/Thongbao/id/77"


def test_listing_parser_ignores_navigation_notice_links_when_list_container_exists():
    html = """
    <nav><a href="/KhoaCKGT/Thongbao/id/6086">Giới thiệu</a></nav>
    <div class="wd-list-content"><ul class="wd-list-report"><li>
      <a href="/KhoaCokhiGT/Thongbao/id/12001">Thông báo học bổng</a>
    </li></ul></div>
    """
    links = extract_notice_links(
        html=html,
        listing_url="https://dut.udn.vn/KhoaCokhiGT/Thongbaods/gids/1668",
        official_domain="dut.udn.vn",
    )

    assert [link.external_id for link in links] == ["12001"]


def test_detail_parser_removes_presentation_badge_from_canonical_title():
    now = datetime.now(timezone.utc)
    parsed = parse_notice_detail(
        html="""
        <html><body><h2>Thông báo kiểm tra tiếng Anh Hot New</h2>
        <p>18/09/2026 08:30</p><div>Nội dung chính thức đủ dài cho parser.</div>
        </body></html>
        """,
        source_id="dut_academic",
        final_url="https://dut.udn.vn/Tintuc/Thongbao/id/9998",
        observed_at=now,
        fetched_at=now,
        raw_html_hash="abc",
        raw_html_path="tmp/9998.html",
    )

    assert parsed.title == "Thông báo kiểm tra tiếng Anh"
