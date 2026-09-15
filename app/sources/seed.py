from app.models.source import SourceSeed, SourceType


DUT_SCHEME = "https"
DUT_DOMAIN = "dut.udn.vn"

DUT_BASE = f"{DUT_SCHEME}://{DUT_DOMAIN}"


SEED_SOURCES = [
    SourceSeed(
        source_id="dut_ctsv",
        name="DUT Student Affairs",
        source_type=SourceType.STUDENT_AFFAIRS,
        base_url=f"{DUT_BASE}/Phong/CTSV",
        listing_url=(
            f"{DUT_BASE}"
            "/Phong/CTSV/Thongbaods/gids/1013"
        ),
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="THÔNG TIN - THÔNG BÁO",
        provenance_note=(
            "Official Student Affairs page hosted "
            "under the DUT first-party domain."
        ),
    ),

    SourceSeed(
        source_id="dut_academic",
        name="DUT Academic and Examination Notices",
        source_type=SourceType.ACADEMIC,
        base_url=DUT_BASE,
        listing_url=(
            f"{DUT_BASE}"
            "/Tintuc/Thongbaods/gid/dt"
        ),
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="ĐÀO TẠO",
        provenance_note=(
            "Official academic and examination notice "
            "category hosted by DUT."
        ),
    ),

    SourceSeed(
        source_id="dut_it_faculty",
        name="DUT Faculty of Information Technology",
        source_type=SourceType.FACULTY,
        base_url=f"{DUT_BASE}/KhoaCNTT",
        listing_url=(
            f"{DUT_BASE}"
            "/KhoaCNTT/Thongbaods/gids/1906"
        ),
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="THÔNG TIN - THÔNG BÁO",
        provenance_note=(
            "Official Faculty of Information Technology "
            "page hosted under the DUT first-party domain."
        ),
    ),
]