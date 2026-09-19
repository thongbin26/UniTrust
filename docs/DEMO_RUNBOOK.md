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

## B. Expected Demo Order (2-3 Minutes)

1. **Home Page (15 seconds)**
   - Open `http://127.0.0.1:8501`.
   - Explain the core thesis: "Đúng nguồn. Đúng phiên bản. Đúng người."
   - Explain that UniTrust verifies forwarded student claims against official structured evidence.

2. **Verify Supported Claim (45 seconds)**
   - Navigate to **Xác minh**.
   - Paste the prepared, source-derived claim and click **Xác minh thông tin**.
   - Explain the Vietnamese conclusion and point out the official evidence used by the result.

3. **Verify Controlled Conflict Mutation (30 seconds)**
   - Replace the deadline in the prepared claim with the controlled conflict value, then verify again.
   - Note to audience: *This is a SYNTHETIC DEMO MUTATION derived from reviewed DUT evidence.*
   - Explain the result: The system flags a **Conflict** (Có mâu thuẫn) because the student's deadline (30/06) conflicts with the official deadline (26/06).
   - Show the field comparison and the official-source link when the reviewed evidence provides a real URL.

4. **Evidence Page (20 seconds)**
   - Navigate to **Tra cứu thông báo**.
   - Search for `điểm rèn luyện`, select a result, and show its official content and source.

5. **For You Page (20 seconds)**
   - Navigate to **Dành cho bạn**.
   - Create the prepared profile with ngành **Công nghệ thông tin** and khóa **K22**.
   - Show the Vietnamese groups **Có thể áp dụng cho bạn** and **Chưa đủ thông tin để xác định** without exposing technical enum names.

## C. Data Provenance & Transparency

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

## D. Recovery Procedure

- **Normal stop:** Press `Ctrl+C` once in the launcher terminal. Wait for `Demo supervisor stopped` before restarting.
- **Startup failure:** Read the named backend/frontend failure and the log tail printed by the launcher. Run the same startup command again after resolving the reported port or artifact problem.
- **Port conflict:** Preflight reports the owning PID and process name. Verify that process yourself; the launcher never kills an unrelated process automatically.
- **Offline / No Internet:** Preflight requires a complete local `multilingual-e5-small` snapshot. When it passes, the launcher forces local-only model loading and disables Hub access for the demo processes.
- **Logs:** Backend and frontend logs are written under `tmp/demo/` for recovery diagnostics; this directory is ignored by Git.

## E. Known Limitations

If asked, honestly state:
- The system relies on human-reviewed structured annotations for its high precision. Pure LLM-extraction has not replaced human review for the "Ground Truth" data in this phase.
- Historical temporal versions are not currently populated in the live DB; the system only operates on the latest indexed versions.
