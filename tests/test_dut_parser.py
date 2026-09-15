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