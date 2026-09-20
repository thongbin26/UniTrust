from app.models.source import SourceSeed, SourceType


DUT_SCHEME = "https"
DUT_DOMAIN = "dut.udn.vn"

DUT_BASE = f"{DUT_SCHEME}://{DUT_DOMAIN}"


SEED_SOURCES = [
    SourceSeed(
        source_id="dut_ctsv",
        name="Phòng Công tác Sinh viên",
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
        authority_scope="student affairs",
        notes="Nguồn chuyên trách công tác sinh viên; có thể trùng với cổng sinh viên.",
    ),

    SourceSeed(
        source_id="dut_academic",
        name="Thông báo đào tạo và khảo thí DUT",
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
        authority_scope="academic",
        notes="Danh mục thông báo trung tâm theo chủ đề đào tạo; có thể là mirror.",
    ),

    SourceSeed(
        source_id="dut_it_faculty",
        name="Khoa Công nghệ Thông tin",
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
        authority_scope="faculty-specific: information technology",
        notes="Nguồn khoa đại diện, chỉ có thẩm quyền trong phạm vi khoa.",
    ),

    SourceSeed(
        source_id="dut_sv_portal",
        name="Trang Sinh viên DUT",
        source_type=SourceType.STUDENT_PORTAL,
        base_url="https://sv1.dut.udn.vn",
        listing_url="https://sv1.dut.udn.vn/",
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="Học phí, lệ phí",
        provenance_note=(
            "Public notice area of the official DUT student information system; "
            "authenticated student functions are out of scope."
        ),
        authority_scope="university-wide student notices",
        crawl_method="dut_public_discovery",
        notes="Discovery portal; linked DUT detail pages remain canonical evidence.",
    ),

    SourceSeed(
        source_id="dut_finance",
        name="Thông báo học phí và tài chính DUT",
        source_type=SourceType.FINANCE,
        base_url=f"{DUT_BASE}/Phong/Taichinh",
        listing_url=f"{DUT_BASE}/Tintuc/Thongbaods/gid/101",
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="HỌC PHÍ",
        provenance_note=(
            "Official DUT central tuition category. Canonical detail ownership is "
            "retained when a linked department page exists."
        ),
        authority_scope="finance",
        notes=(
            "The Finance Office generic list route mirrored unrelated central items; "
            "this verified topic feed is used instead."
        ),
    ),

    SourceSeed(
        source_id="dut_training_quality",
        name="Phòng Đào tạo và Bảo đảm chất lượng",
        source_type=SourceType.ACADEMIC,
        base_url=f"{DUT_BASE}/Phong/Daotao",
        listing_url=f"{DUT_BASE}/Phong/Daotao/Thongbaods/gids/1009",
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="ĐÀO TẠO ĐẠI HỌC",
        provenance_note="Official DUT Training and Quality Assurance Office notice listing.",
        authority_scope="academic, examination and quality assurance",
        notes="Department source; shared official IDs are deduplicated against mirrors.",
    ),

    SourceSeed(
        source_id="dut_transport_energy_faculty",
        name="Khoa Cơ khí Giao thông và Năng lượng",
        source_type=SourceType.FACULTY,
        base_url=f"{DUT_BASE}/khoackgt",
        listing_url=f"{DUT_BASE}/KhoaCokhiGT/Thongbaods/gids/1668",
        official_domain=DUT_DOMAIN,
        is_official=True,
        expected_marker="THÔNG TIN - THÔNG BÁO",
        provenance_note=(
            "Official post-restructure faculty page; the listing retains a legacy "
            "KhoaCokhiGT route."
        ),
        authority_scope="faculty-specific: transport engineering and energy",
        notes="Faculty notices must not override university-wide policy.",
    ),
]


SOURCE_BY_ID = {source.source_id: source for source in SEED_SOURCES}
BASELINE_SOURCES = SEED_SOURCES[:3]
