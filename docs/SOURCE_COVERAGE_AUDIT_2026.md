# UniTrust official source coverage audit (2026)

Audit date: 2026-09-20
Scope: public, official DUT sources only. No authenticated student function, private API, CAPTCHA bypass, social scraping, or production ingestion was used.

## Decision summary

UniTrust currently configures seven public official source families. The registry is the source of truth for display name, type, authority scope, enabled state, crawl method, expected marker, and notes. The SQLite `sources` table remains backward-compatible; the additional operational metadata is configuration-owned rather than added through an unapproved production migration.

The Phase A staging crawl was deliberately limited to five list items per source. It is a coverage validation, not a claim that UniTrust monitors every DUT notice.

## Source audit

| Source | Official URL | Public? | Authority | Content type | Structure / pagination | Detail page? | Attachments? | Overlap | Crawl feasibility | Priority | Decision / notes |
|---|---|---:|---|---|---|---:|---:|---|---|---|---|
| Central academic topic (`dut_academic`) | [DUT academic notices](https://dut.udn.vn/Tintuc/Thongbaods/gid/dt) | Yes | Academic topic discovery | Training and examination notices | Server-rendered DUT list; numbered pages | Yes | Yes | Training office and student portal | Stable HTML, shared DUT adapter | Core | Enabled. Treat as an aggregate/discovery route when a department-owned detail exists. |
| Student Affairs (`dut_ctsv`) | [Student Affairs notices](https://dut.udn.vn/Phong/CTSV/Thongbaods/gids/1013) | Yes | Student affairs | Scholarships, conduct, support, student administration | Server-rendered DUT list; numbered pages | Yes | Yes | Student portal and central categories | Stable HTML, shared DUT adapter | Core | Enabled. Existing source ID retained. |
| IT Faculty (`dut_it_faculty`) | [IT Faculty notices](https://dut.udn.vn/KhoaCNTT/Thongbaods/gids/1906) | Yes | Faculty-specific | IT faculty notices | Server-rendered DUT list; numbered pages | Yes | Yes | Central DUT feed | Stable HTML, shared DUT adapter | Core faculty sample | Enabled. Existing source ID retained; cannot override university-wide policy. |
| Public student portal (`dut_sv_portal`) | [DUT student information portal](https://sv1.dut.udn.vn/) | Yes, notice area only | University-wide student notice discovery | General, training, classes, student affairs, examination, fees, rules | Server-rendered tabs; linked official details | Usually an official DUT detail; some direct files | Yes | High overlap with departments and central feed | Stable discovery adapter; no login | Core discovery | Enabled. `sv.dut.udn.vn` authenticated functions and public person-level lists are out of scope. |
| Tuition and finance topic (`dut_finance`) | [DUT tuition notices](https://dut.udn.vn/Tintuc/Thongbaods/gid/101) | Yes | Finance topic | Tuition, fees and related finance notices | Server-rendered DUT list; numbered pages | Yes | Yes | Training, Student Affairs and central feed | Stable HTML, shared DUT adapter | Core | Enabled. The generic Finance Office list route was rejected because it mirrored unrelated central items. |
| Training and Quality Assurance (`dut_training_quality`) | [Training office notices](https://dut.udn.vn/Phong/Daotao/Thongbaods/gids/1009) | Yes | Academic, examination and quality assurance | Training, examinations, graduation and quality notices | Server-rendered DUT list; numbered pages | Yes | Yes | Central academic topic and student portal | Stable HTML, shared DUT adapter | Core | Enabled. Shared official IDs collapse mirrors. |
| Transport Engineering and Energy Faculty (`dut_transport_energy_faculty`) | [Faculty notices](https://dut.udn.vn/KhoaCokhiGT/Thongbaods/gids/1668) | Yes | Faculty-specific | Scholarships, events and faculty notices | Server-rendered DUT list; numbered pages | Yes | Yes | Central DUT feed | Stable HTML after content-container scoping | Core faculty sample | Enabled. Current faculty identity uses a legacy route retained by the official site. |
| Central all-notice feed | [DUT central notices](https://dut.udn.vn/Tintuc/Thongbaods/gid/all) | Yes | University-wide discovery | Mixed notices | Server-rendered, paginated | Yes | Yes | Very high | Technically feasible | Secondary | Deferred as a separate source because it is predominantly an aggregator and would add mirror volume rather than authority coverage. |
| Electronics and AI Faculty | [Current DUT directory](https://dut.udn.vn/Danhba/id/53) | Directory is public | Faculty-specific | Directory confirmed; stable notice feed not established | No verified post-restructure notice listing | Unknown | Unknown | Possible legacy ECE pages | Not ready | Faculty candidate | Deferred. A legacy guessed route returned 404; no URL is fabricated. |
| DUT admissions | DUT official admissions material | Public | Reference/admissions | Admissions and program reference | Multiple pages and documents | Varies | Yes | Low daily-obligation value | Feasible selectively | Reference | Deferred as `OFFICIAL_REFERENCE`; not bulk-ingested into the student obligation feed. |
| Official Facebook pages | Official pages vary | Public access is not reliably stable | Supplementary discovery only | Social posts | Dynamic, login/anti-bot risk, unstable extraction | Permalinks vary | Media-heavy | Often mirrors official web notices | Not sufficiently stable | Supplementary | `DEFERRED_SOCIAL_SOURCE`. No browser automation, login, OCR, or Facebook crawler is added. |

## Existing source re-audit

| Source ID | Status | Role |
|---|---|---|
| `dut_academic` | HTTP 200, expected marker present | Official central academic topic/discovery source |
| `dut_ctsv` | HTTP 200, expected marker present | Canonical student-affairs authority when the detail is department-owned |
| `dut_it_faculty` | HTTP 200, expected marker present | Faculty-scoped authority only |

Existing source IDs were not renamed. Their Vietnamese display names were corrected separately.

## Canonical identity and deduplication

Identity resolution is deterministic and conservative:

1. Normalize an official URL without discarding meaningful ID parameters.
2. Reuse an exact canonical URL when present.
3. For DUT detail routes, reuse a shared official `/Thongbao/id/<number>` only when that stable ID is present.
4. Otherwise create a separate notice. Titles alone never merge notices.

Tracking parameters (`utm_*`, `fbclid`, `gclid`, and a small explicit allowlist of other tracking keys) and fragments are removed. DUT subdomains are normalized to HTTPS, default ports and duplicate slashes are removed, meaningful query parameters are retained, and query keys are sorted. Similar-looking URLs are not merged heuristically.

`notice_discoveries` records every configured source and discovery URL that led to a canonical notice. A mirror discovery therefore does not create another notice, version, or independent evidence row.

## Versioning

The existing `notice_versions` semantics are unchanged:

- same canonical notice and same normalized content hash: no new version;
- same canonical notice and changed official content hash: a new version;
- a mirror with the same shared official ID: discovery provenance only, not a content version;
- presentation-only `Hot`/`New` badge cleanup: no false historical version for legacy rows.

Publication date, observation time, and fetch time remain distinct. Missing publication dates remain unknown.

## Attachment provenance

No `notice_attachments` table is required in Step 17C. The current chain is queryable as:

`notices` → `notice_versions` → `attachment_links_json`

This preserves the official notice/version that supplied each external PDF, Office document, or Google Drive URL. An external URL is not trusted independently; trust begins at the official DUT notice. The current schema does not store a separate attachment display label, which is a documented limitation rather than grounds for an additional unapproved migration.

## Parser and health policy

- DUT list pages are scoped to `.wd-list-content .wd-list-report` when that structure exists, preventing navigation and program-introduction links from being ingested.
- The public student portal uses discovery-only extraction of official DUT detail links.
- A missing expected marker fails the source before ingest.
- HTTP 200 alone is insufficient: official hostname, response size, marker, and parse results are checked.
- Crawls are sequential, use bounded retries/backoff, identify UniTrust in the user agent, and support a per-source item limit.
- Unit tests use stored minimal HTML fixtures and never require Internet access.

## Remaining gaps

- Only one additional post-restructure faculty source is enabled; Electronics and AI remains deferred until a stable official notice URL is established.
- Direct-file-only entries on the student portal are retained as a future adapter gap; Step 17C does not invent a detail page.
- Pagination beyond the configured staging limit was not crawled.
- Social sources, OCR, authenticated student functions, and private/student-specific records remain out of scope.
- The source set should be described as “seven configured public official sources,” never as complete DUT coverage.
