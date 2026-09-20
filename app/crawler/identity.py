import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}

OFFICIAL_NOTICE_ID_RE = re.compile(
    r"/Thongbao/id/(\d+)(?:/|$)",
    re.IGNORECASE,
)
OFFICIAL_NOTICE_NAMESPACE = "dut.udn.vn:thongbao"


def normalize_url(url: str) -> str:
    """Normalize identity-safe URL parts without discarding meaningful IDs."""
    parsed = urlsplit(url.strip())
    hostname = (parsed.hostname or "").lower()
    scheme = parsed.scheme.lower() or "https"
    if hostname == "dut.udn.vn" or hostname.endswith(".dut.udn.vn"):
        scheme = "https"

    port = parsed.port
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")

    query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.casefold()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS:
            continue
        query.append((key, value))

    return urlunsplit((scheme, netloc, path, urlencode(sorted(query)), ""))


def official_notice_id(url: str) -> str | None:
    parsed = urlsplit(normalize_url(url))
    hostname = parsed.hostname or ""
    if hostname != "dut.udn.vn":
        return None
    match = OFFICIAL_NOTICE_ID_RE.search(parsed.path)
    return (
        f"{OFFICIAL_NOTICE_NAMESPACE}:{match.group(1)}"
        if match
        else None
    )


def canonical_source_for_url(url: str, fallback_source_id: str) -> str:
    path = urlsplit(normalize_url(url)).path.casefold()
    prefixes = (
        ("/phong/ctsv/", "dut_ctsv"),
        ("/phong/sinhvien/", "dut_ctsv"),
        ("/phong/taichinh/", "dut_finance"),
        ("/phong/daotao/", "dut_training_quality"),
        ("/khoacntt/", "dut_it_faculty"),
        ("/khoacokhigt/", "dut_transport_energy_faculty"),
    )
    for prefix, source_id in prefixes:
        if path.startswith(prefix):
            return source_id
    if path.startswith("/tintuc/"):
        return "dut_academic" if fallback_source_id == "dut_sv_portal" else fallback_source_id
    return fallback_source_id
