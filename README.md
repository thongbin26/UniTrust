# UniTrust V2

**Temporal Evidence & Obligation Intelligence for University Notices**

> Đúng nguồn. Đúng phiên bản. Đúng người.

UniTrust V2 is a competition prototype for verifying student-facing
information against authoritative university notices and tracking how
student obligations change over time.

## Current status

Step 2 — Project Setup

Current components:

- FastAPI backend
- Streamlit frontend
- SQLite database
- Environment configuration
- Pytest test suite
- Git repository

## Project structure

- `app/` — backend and core application logic
- `frontend/` — Streamlit interface
- `data/` — datasets and annotations
- `tests/` — automated tests
- `scripts/` — utility scripts
- `docs/` — project documentation

## Prerequisites
- Activate `.venv` (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Unix).
- Local semantic AI (Ollama with Qwen3:4b) is **optional**. The backend will start and perform deterministic verification regardless of Ollama's availability.

## Local Demo Startup Workflow

Open two terminals.

**Terminal A (Backend):**
```bash
uvicorn main:app --reload
```

**Terminal B (Frontend):**
```bash
streamlit run frontend/Home.py
```

## Demo & Coverage Limitations

- **Structured Semantic Coverage:** UniTrust currently has human-reviewed structured coverage for a subset of the indexed DUT notices. Other official notices remain browseable, but structured verification may abstain when reviewed fields are not available.
- **Temporal History:** Real temporal data currently has zero historical versions. The Evidence page will honestly reflect this ("No historical version is currently stored for this notice."). Synthetic demo examples are explicitly marked in the code and do not mutate the real database.
- **Local Embedding Model:** `multilingual-e5-small` is initialized once during FastAPI startup. It is heavily cached for interactive query latency.