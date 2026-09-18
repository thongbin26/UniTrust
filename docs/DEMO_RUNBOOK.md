# UniTrust - Demo Runbook

This runbook outlines the steps to present the final UniTrust prototype. The live demo is designed to last approximately 2-3 minutes.

## A. Pre-demo Setup & Commands

1. **Verify Environment**: Ensure you are in the project root.
2. **Start the System**:
   Run the unified startup script in PowerShell:
   ```powershell
   ./scripts/start_demo.ps1
   ```
   *This script runs preflight checks, sets the PYTHONPATH, starts the FastAPI backend (8000), waits for it to become healthy, and starts the Streamlit frontend (8501).*

3. **Health Checks**:
   - The startup script automatically polls `/health`.
   - Ensure the terminal outputs: `✅ Backend is healthy!`

## B. Expected Demo Order (2-3 Minutes)

1. **Home Page (15 seconds)**
   - Open `http://127.0.0.1:8501`.
   - Explain the core thesis: "Đúng nguồn. Đúng phiên bản. Đúng người."
   - Explain that UniTrust verifies forwarded student claims against official structured evidence.

2. **Verify Supported Claim (45 seconds)**
   - Navigate to the **Verify** page.
   - Click **Example 1: Verified (Real-Source Derived)**.
   - Explain the result: The claim is **Verified** (Đã xác minh) because it exactly matches the reviewed official evidence (Notice 13).
   - Point out the visual separation between the Trust State and Temporal State (Phiên bản hiện hành).

3. **Verify Controlled Conflict Mutation (30 seconds)**
   - Click **Example 2: Wrong Deadline**.
   - Note to audience: *This is a SYNTHETIC DEMO MUTATION derived from reviewed DUT evidence.*
   - Explain the result: The system flags a **Conflict** (Có mâu thuẫn) because the student's deadline (30/06) conflicts with the official deadline (26/06).
   - Expand the **Chi tiết kỹ thuật (Technical Details)** to show the exact provenance and source URL.

4. **Evidence Page (20 seconds)**
   - Navigate to the **Evidence** page.
   - Select Notice 13.
   - Show how the raw official text is accessible.
   - Point out the truthful "What Changed" section stating: *Hiện chưa lưu phiên bản lịch sử nào cho thông báo này.*

5. **For You Page (20 seconds)**
   - Navigate to the **For You** page.
   - Enter a test profile: Khoa `CNTT`, Khóa `K22`.
   - Click **Tìm nghĩa vụ liên quan**.
   - Show that the obligation from Notice 13 is correctly categorized under **CÓ (APPLIES)**, while ambiguous obligations fall under **CHƯA RÕ (UNKNOWN)**.

6. **Research Numbers (20 seconds)**
   - Return to the Home page to show the credibility block, explicitly differentiating product data from research benchmarks.

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

- **Frontend or Backend fails**: 
  1. Press `Ctrl+C` in the PowerShell terminal to terminate the `start_demo.ps1` script.
  2. If processes linger, close the terminal window completely.
  3. Open a new terminal and re-run `./scripts/start_demo.ps1`.
- **Offline / No Internet**: The dense embedding model (`multilingual-e5-small`) should be cached locally. Ensure it is cached before demoing without an internet connection. The preflight check will warn you if it's missing.

## E. Known Limitations

If asked, honestly state:
- The system relies on human-reviewed structured annotations for its high precision. Pure LLM-extraction has not replaced human review for the "Ground Truth" data in this phase.
- Historical temporal versions are not currently populated in the live DB; the system only operates on the latest indexed versions.
