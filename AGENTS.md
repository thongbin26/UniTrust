# UniTrust — Repository Instructions for Codex

## Product

UniTrust is a Vietnamese university-information verification system for
students at DUT.

It is NOT a chatbot.

Main student-facing flows:

1. Trang chủ
2. Xác minh
3. Tra cứu thông báo
4. Dành cho bạn

Product name:
UniTrust

Slogan:
Kiểm chứng đúng nguồn, an tâm hành động.

All normal student-facing UI must be Vietnamese.

---

## Current development state

Steps 1–15 were completed before the current redesign.

Step 16 is partially implemented and was handed off from another coding agent.

The current Step 16 implementation contains unresolved UX/integration issues.

Do NOT assume the current Step 16 implementation is correct merely because
tests pass.

Before making large changes:
- inspect the existing implementation
- identify root causes
- explain the proposed fix
- prefer structural fixes over repeated local patches

---

## Frozen research/core behavior

Do NOT change these without explicit user approval:

- verification semantics
- retrieval semantics
- temporal reasoning semantics
- abstention behavior
- Step 13 benchmark data or metrics
- reviewed annotations
- existing ground-truth labels
- database data/schema unless strictly required for a confirmed bug

Reviewed annotations are under:

data/annotations/batch_001/

Do not rewrite or relabel them.

Step 13 is a frozen research baseline.

Do not improve Step 13 metrics by changing evaluation data, labels,
benchmarks, or semantics.

---

## Trust semantics

Core verification states:

- VERIFIED
- PARTIALLY_VERIFIED
- CONFLICT
- INSUFFICIENT_EVIDENCE

Temporal states include:

- CURRENT
- SUPERSEDED_OUTDATED
- UNKNOWN

Important:

- INSUFFICIENT_EVIDENCE does NOT mean false.
- CONFLICT does NOT mean scam.
- Do not silently convert uncertainty into a confident result.

---

## Evidence and provenance

Raw notice provenance must never be overwritten by AI-generated data.

Do not fabricate:
- official URLs
- historical versions
- source ownership
- faculty/program mappings
- official evidence

Use deterministic processing where appropriate.

AI must not replace provenance.

---

## DUT restructuring

DUT organizational restructuring became effective on 2026-08-20.

The current institutional structure contains 9 professional faculties.

Older official pages may represent pre-restructuring organization.

Current faculty structure:

1. Khoa Điện tử và Trí tuệ nhân tạo
2. Khoa Cơ khí Giao thông và Năng lượng
3. Khoa Hóa, Môi trường và Khoa học Sự sống
4. Khoa Xây dựng
5. Khoa Điện
6. Khoa Cơ khí
7. Khoa Công nghệ Thông tin
8. Khoa Quản lý Dự án và Công nghiệp
9. Khoa Kiến trúc

Institution-level public information indicates 49 programs/specializations
for 2026.

Do NOT infer that all 49 program-to-faculty mappings are verified.

Relationship status must distinguish:

- VERIFIED
- PROVISIONAL
- UNVERIFIED

Current working assumption for:

Khoa học dữ liệu và Trí tuệ nhân tạo

is:

Khoa Điện tử và Trí tuệ nhân tạo

but current direct post-restructuring official evidence has not yet been
established in this repo.

Therefore this relationship must remain PROVISIONAL unless stronger official
evidence is found.

Project-owner-reported information must remain distinguishable from official
evidence.

---

## Source temporal precedence

When sources disagree about organizational structure, prefer:

1. post-2026-08-20 official decisions or announcements
2. current official university directory
3. post-restructure official training documents
4. updated faculty pages
5. post-restructure admissions material
6. pre-2026-08-20 material
7. 2025 or older material

Do not use crawl date as a substitute for effective date.

---

## Architecture

Environment:
- Windows
- Python 3.13
- virtual environment: .venv

Backend:
- FastAPI
- default port 8000

Frontend:
- Streamlit
- default port 8501

Streamlit entrypoint:
frontend/Home.py

The app uses st.navigation / st.Page.

Primary startup command:

powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1

Test command:

.venv\Scripts\python -m pytest

Preflight:

.venv\Scripts\python scripts/preflight_demo.py

---

## Current Step 16 areas

Likely relevant files include:

- app/api/routes/evidence.py
- data/catalog/dut_catalog_2026.json
- frontend/api_client.py
- frontend/home_page.py
- frontend/pages/1_Verify.py
- frontend/pages/2_Evidence.py
- frontend/pages/3_For_You.py
- frontend/ui_style.py
- frontend/ui_translations.py
- .streamlit/config.toml
- requirements.txt

Autocomplete dependency:

streamlit-searchbox==0.1.24

Do not add another autocomplete package unless clearly justified.

---

## UX requirements

The product should feel like a polished student-facing application, not a
developer dashboard.

Do not expose normal users to:

- backend URLs
- connection diagnostics
- raw Python exceptions
- stack traces
- internal IDs
- raw enum values
- technical provenance fields without explanation
- English labels where a Vietnamese label should be shown

Home:
- clear value proposition
- polished hero
- clear CTA
- no backend/connection panel

Xác minh:
- blue primary action
- no demo/example clutter unless specifically required
- compact evidence-backed result

Tra cứu thông báo:
- one real searchable combobox
- clicking shows browseable notices
- typing shows suggestions immediately
- no Enter required
- deterministic relevance ranking
- do not fetch every notice detail up front
- fetch detail only after selection

Dành cho bạn:
- no raw API errors
- compact profile
- faculty/program/cohort only where supported
- no unsupported “Đại trà” assumptions
- persist profile through navigation/refresh where currently designed
- show uncertainty clearly for provisional applicability

---

## Performance

Avoid N+1 API calls.

Evidence browsing should prefer a single search-index request and fetch full
notice detail only after the user selects a result.

Do not trade correctness for apparent speed.

---

## Git and safety

Current development branch:

codex-step16-fix

Do not commit or push unless explicitly asked.

Before substantial work:

git status
git diff

Do not run broad destructive commands such as:

git reset --hard
git checkout .
git restore .
git clean -fd

without explicit approval.

Do not kill every Python process on the machine.

For ports 8000/8501:
- inspect owning PIDs first
- only terminate confirmed UniTrust processes

Do not modify unrelated files.

---

## Validation

Before declaring a task complete:

1. run relevant targeted tests
2. run full pytest when changes are substantial
3. run git diff --check
4. run preflight where applicable
5. inspect git diff for unintended changes
6. visually validate affected Streamlit flows

Passing tests alone does not mean the UI task is complete.