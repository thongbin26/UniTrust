# UniTrust - Demo Runbook

This runbook outlines the steps to present the UniTrust prototype. The live demo is designed to last approximately 3-5 minutes.

## A. Pre-demo Setup & Commands

1. **Verify Environment**: Ensure you are in the project root.
2. **Run the read-only preflight** (optional when the unified launcher is used):
   ```powershell
   .venv\Scripts\python scripts/preflight_demo.py
   ```
3. **Start the System** with one command:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1
   ```
   The launcher runs preflight, starts the backend, waits for full readiness, then starts and waits for the frontend. Start the demo only after it prints `UniTrust is ready: http://127.0.0.1:8501`.

4. **Optional quick smoke check** in a second terminal:
   ```powershell
   .venv\Scripts\python scripts/smoke_test.py
   ```
   A successful run checks health, Evidence, For You, and one deterministic verification request.

## A1. Optional Continuous Official-Source Freshness Runtime

Use this only when the demo needs the opt-in monitoring worker. The production
database and published retrieval cache remain read-only inputs: all monitor
writes go to one external runtime root shared by the three demo processes.

Open PowerShell in the repository root and prepare the external snapshot once:

```powershell
$runtime = "C:\Users\DELL\unitrust-demo-freshness-runtime"
if (Test-Path $runtime) { throw "Use the existing prepared runtime; do not overwrite it." }
New-Item -ItemType Directory -Path $runtime | Out-Null
Copy-Item .\unitrust.db "$runtime\unitrust-v2.db"
Copy-Item .\data\processed\retrieval "$runtime\retrieval" -Recurse
```

Set the same runtime configuration in each terminal before starting a process:

```powershell
$runtime = "C:\Users\DELL\unitrust-demo-freshness-runtime"
$env:DATABASE_URL = "sqlite:///$($runtime.Replace('\', '/'))/unitrust-v2.db"
$env:RETRIEVAL_CACHE_DIR = "$runtime\retrieval"
$env:MONITORING_RAW_DATA_DIR = "$runtime\raw"
$env:MONITORING_ENABLED = "true"
$env:DENSE_LOCAL_FILES_ONLY = "true"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
```

Start each process separately. The worker is deliberately never started by
FastAPI or Streamlit.

```powershell
# Terminal 1 — backend
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
.venv\Scripts\python -m streamlit run frontend\Home.py --server.address 127.0.0.1 --server.port 8501

# Terminal 3 — monitor worker (repeats every 10 minutes; Ctrl+C stops only this worker)
.venv\Scripts\python scripts\run_monitor.py --data-root $runtime --interval-seconds 600 --limit 3 --bootstrap-from .\unitrust.db
```

For a bounded controlled cycle instead of continuous monitoring, use
`--once` with the same command. Run the read-only preflight in either web-app
terminal before presenting:

```powershell
.venv\Scripts\python scripts\preflight_demo.py
```

Stop each terminal with `Ctrl+C`. Do not point `DATABASE_URL` or
`RETRIEVAL_CACHE_DIR` back at the repository while the monitor worker is
running.

## B. Fixed Demo Cases

Use these exact inputs so the live result remains traceable to the reviewed data:

1. **Case A - real source-derived claim (`VERIFIED`)**
   ```text
   Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.
   ```
   This matches reviewed notice 13. In the student UI, describe the result as **Đã xác minh**.

2. **Case B - controlled mutation (`CONFLICT`)**
   ```text
   Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 30/06/2026.
   ```
   This is a synthetic deadline mutation of Case A for demonstration and evaluation. Say that explicitly. The reviewed official deadline remains 26/06/2026; the UI should show **Có thông tin mâu thuẫn**.

3. **Case C - unsupported claim (`INSUFFICIENT_EVIDENCE`)**
   ```text
   Đại học yêu cầu sinh viên đi học mặc áo màu đỏ
   ```
   The system has no sufficient reviewed evidence for this claim. The UI should show **Chưa đủ bằng chứng**, never describe it as false.

## C. Expected Demo Order (3-5 Minutes)

1. **0:00-0:30 - Home Page and problem**
   - Open `http://127.0.0.1:8501`.
   - Explain the core thesis: "Đúng nguồn. Đúng phiên bản. Đúng người."
   - Explain that UniTrust verifies forwarded student claims against official structured evidence.

2. **0:30-1:25 - Verify Case A**
   - Navigate to **Xác minh**.
   - Paste Case A and click **Xác minh thông tin**.
   - Explain the Vietnamese conclusion and point out the official evidence used by the result.

3. **1:25-2:05 - Verify Case B**
   - Paste Case B and verify again.
   - Note to audience: *This is a SYNTHETIC DEMO MUTATION derived from reviewed DUT evidence.*
   - Explain the result: The system flags a **Conflict** (Có mâu thuẫn) because the student's deadline (30/06) conflicts with the official deadline (26/06).
   - Show the field comparison and the official-source link when the reviewed evidence provides a real URL.

4. **2:05-2:30 - Verify Case C**
   - Paste Case C.
   - Explain that UniTrust abstains as **Chưa đủ bằng chứng** instead of turning missing evidence into a false claim.

5. **2:30-3:15 - Evidence search**
   - Navigate to **Tra cứu thông báo**.
   - Type `điểm rèn luyện` without pressing Enter, select the leading relevant result, and show its official content and source.
   - If time permits, replace the query with `tốt nghiệp` to show the deterministic ranking of directly related notices.

6. **3:15-4:20 - For You**
   - Navigate to **Dành cho bạn**.
   - Select khoa **Khoa Công nghệ Thông tin**, ngành **Công nghệ thông tin**, and khóa **K22**.
   - Show the Vietnamese groups **Có thể áp dụng cho bạn** and **Chưa đủ thông tin để xác định** without exposing technical enum names.
   - Explain that the display label is mapped to the reviewed canonical value `CNTT`; do not present this internal value in the student UI.

7. **4:20-5:00 - Product difference and close**
   - Restate the product promise: **Kiểm chứng đúng nguồn, an tâm hành động.**
   - Emphasize official provenance, explicit uncertainty, and student-specific applicability.

## D. Data Provenance & Transparency

**REAL PRODUCT DATA:**
- 3 official DUT sources
- 30 crawled notices
- 10 human-reviewed notices
- 18 reviewed obligations

**CONTROLLED RESEARCH RESULTS:**
- Hybrid Hit@1: 94.83% (N=58 source-derived retrieval benchmark)
- Controlled verification accuracy: 78% (N=50 synthetic mutations derived from reviewed DUT evidence)
- Reviewed source-derived accuracy: 66.67% (N=18)

*Do not state "UniTrust is 95% accurate" as it overgeneralizes the retrieval benchmark.*

## E. Recovery Procedure

- **Normal stop:** Press `Ctrl+C` once in the launcher terminal. Wait for `Demo supervisor stopped` before restarting.
- **Startup failure:** Read the named backend/frontend failure and the log tail printed by the launcher. Run the same startup command again after resolving the reported port or artifact problem.
- **Port conflict:** Preflight reports the owning PID and process name. Verify that process yourself; the launcher never kills an unrelated process automatically.
- **Offline / No Internet:** Preflight requires a complete local `multilingual-e5-small` snapshot. When it passes, the launcher forces local-only model loading and disables Hub access for the demo processes.
- **Logs:** Backend and frontend logs are written under `tmp/demo/` for recovery diagnostics; this directory is ignored by Git.

## F. Known Limitations

If asked, honestly state:
- The system relies on human-reviewed structured annotations for its high precision. Pure LLM-extraction has not replaced human review for the "Ground Truth" data in this phase.
- Historical temporal versions are not currently populated in the live DB; the system only operates on the latest indexed versions.
