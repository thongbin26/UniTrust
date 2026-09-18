# UniTrust

**Temporal Evidence & Obligation Intelligence for University Notices**

> Đúng nguồn. Đúng phiên bản. Đúng người.

UniTrust is a competition prototype for verifying student-facing information against authoritative university notices and tracking how student obligations change over time.

## Problem & System Thesis

University notices are often forwarded through unofficial channels (Zalo, Facebook) without context, leading to missed deadlines and confusion. UniTrust solves this by decomposing claims into structured obligations and verifying them against the exact, current official evidence.

Thesis: "Đúng nguồn. Đúng phiên bản. Đúng người." (Right Source. Right Version. Right Person.)

## Architecture

- **Backend**: FastAPI with a pipeline covering Claim Decomposition, Hybrid Retrieval (BM25 + multilingual-e5-small), Typed Verification, Temporal Resolution, and Abstention mechanisms.
- **Frontend**: Streamlit providing a clear, interactive prototype for the three core capabilities.
- **Data**: SQLite database storing notices, versions, sources, and reviewed annotations.

## Three Core Capabilities

1. **Verify (Xác minh)**: Checks forwarded messages against official obligations and outputs a clear Trust State, Temporal State, and exact provenance.
2. **Evidence (Bằng chứng)**: A transparent browser for official notices, their structural coverage, and version history.
3. **For You (Dành cho bạn)**: A personalized view filtering obligations by a student's profile (Faculty, Major, Cohort, Program).

## Trust & Temporal State Definitions

**Trust State:**
- **VERIFIED (Đã xác minh)**: Official evidence supports the material claim.
- **PARTIALLY_VERIFIED (Xác minh một phần)**: Some parts are supported, but others are unclear.
- **CONFLICT (Có mâu thuẫn)**: A material field conflicts with official evidence.
- **INSUFFICIENT_EVIDENCE (Chưa đủ bằng chứng)**: The system abstains safely when evidence or coverage is lacking.

**Temporal State:**
- **CURRENT (Phiên bản hiện hành)**: Matches the current known official version.
- **SUPERSEDED_OUTDATED (Đã bị thay thế / lỗi thời)**: Matches historical information that is no longer current.
- **UNKNOWN (Chưa xác định phiên bản)**: Current validity could not be established.

## Evaluation & Data Provenance

UniTrust relies on a combination of real product data and controlled benchmark metrics.

**REAL PRODUCT DATA:**
- 3 official DUT sources
- 30 crawled notices
- 10 human-reviewed notices
- 18 reviewed obligations

**CONTROLLED RESEARCH RESULTS:**
- **Hybrid Hit@1**: 94.83% (N=58 source-derived retrieval benchmark)
- **Controlled verification accuracy**: 78% (N=50 synthetic mutations derived from reviewed DUT evidence)
- **Reviewed source-derived accuracy**: 66.67% (N=18)

*Note on Benchmarks: Do not overgeneralize the benchmark results (e.g., claiming "95% accurate overall"). They represent performance on specifically curated populations.*

## Limitations

- **Structured Semantic Coverage:** UniTrust currently has human-reviewed structured coverage for a subset of the indexed DUT notices. Verification over unreviewed documents may abstain safely.
- **Temporal History:** The current live database has zero historical versions. The Evidence page will truthfully reflect this.
- **Local Embedding Model:** `multilingual-e5-small` must be cached locally to run offline.

## Setup & Startup Workflow

### Prerequisites
- Python 3.10+
- Activate `.venv` (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Unix).
- Local semantic AI (Ollama) is **optional**.

### Starting the Demo (Windows)
Run the automated startup script which handles preflight checks, backend, and frontend:
```powershell
./scripts/start_demo.ps1
```
The script will output the URLs for the Backend API (`http://127.0.0.1:8000`) and Frontend UI (`http://127.0.0.1:8501`).

### Demo Instructions
See [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md) for the operator flow and expected cases.

## Project Structure

- `app/` — Backend and core verification logic pipeline
- `frontend/` — Streamlit UI and demo cases
- `data/` — Datasets, reviews, and SQLite database (`unitrust.db`)
- `tests/` — Automated test suite
- `scripts/` — Utility scripts and demo startup
- `docs/` — Project specifications and runbooks