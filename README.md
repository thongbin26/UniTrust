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

## Run backend

```bash
python -m uvicorn main:app --reload