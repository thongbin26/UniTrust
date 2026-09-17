# UNITRUST V2 — MASTER TECHNICAL SPECIFICATION

## 1. PRODUCT VISION
UniTrust AI (Hệ thống AI xác minh thông tin và nghĩa vụ sinh viên dựa trên bằng chứng chính thống theo thời gian) is not a generic chatbot. It is a highly constrained, evidence-grounded AI assistant tailored for the University of Science and Technology — The University of Danang (DUT).

**Tagline**: "Đúng nguồn. Đúng phiên bản. Đúng người."

**Core Value Proposition**: Verify forwarded information, track current official obligations, detect outdated/superseded notices, and ensure every conclusion traces explicitly back to official university evidence. The LLM must NEVER be the source of truth.

## 2. THREE HERO CAPABILITIES
1. **Temporal Evidence Verify**: Validate student claims against official sources. Output states: `VERIFIED`, `PARTIALLY VERIFIED`, `CONFLICT`, `INSUFFICIENT EVIDENCE`.
2. **What Changed / Change-to-Impact**: Resolve temporal supersession (`AMENDS`, `SUPERSEDES`, `DUPLICATES`, `RELATED`). Differentiate between a "match with old text" and "currently valid".
3. **For You / Personal Obligation Timeline**: Surface applicable obligations based on controlled student dimensions (Faculty, Major, Cohort, Program).

## 3. CORE ARCHITECTURAL INVARIANTS
### 3.1 Immutable Source Provenance
Raw notice text, source URLs, notice identities, content hashes, observed times, and official provenance must NEVER be silently rewritten or synthesized by the LLM.

### 3.2 Evidence Grounding
All final extracted evidence must map directly to raw text substrings. An LLM-generated sentence is not evidence. The system uses a **Semantic Draft -> Deterministic Canonicalizer** architecture where the LLM produces unstructured fields, and strict Python rules align those fields to exact character spans in the raw HTML/text.

### 3.3 Strict Semantic Trust States
- `INSUFFICIENT EVIDENCE` != False. The system must explicitly abstain rather than hallucinate if coverage is low.
- `CONFLICT` != Scam. 
- `OUTDATED` != Originally False. A claim can perfectly match historical evidence but still be superseded.

### 3.4 No Fabricated Data
- Do not fabricate evaluation metrics. All numbers must come from real runs.
- Do not fabricate DUT notices. Synthetic mutations for benchmarking must be explicitly labeled as `is_synthetic = True` and derived from real evidence.
- Do not rewrite reviewed annotation data to artificially boost performance metrics.

## 4. ARCHITECTURE ROADMAP (STEPS 7–14)

### STEP 7: Retrieval Baselines & Evidence Retrieval
- **Corpus**: The full set of official notice versions (`notice_versions` table). Historical versions must be preserved for temporal reasoning.
- **Chunking**: Deterministic, paragraph/line-aware chunking preserving precise `notice_id`, `version_id`, `start_char`, and `end_char` offsets.
- **Models**:
  1. Lexical Baseline: `BM25`.
  2. Dense Multilingual Baseline: `intfloat/multilingual-e5-small` (via `sentence-transformers`).
  3. Hybrid Retrieval: Reciprocal Rank Fusion (RRF).
- **Vector Storage**: Numpy-based local embeddings cached alongside SQLite metadata. No heavy vector DBs (e.g., Chroma, Qdrant) during this phase.

### STEP 8: Verification Benchmark Dataset
- Scaffolding to generate synthetic candidate claims from real official evidence.
- Categories include: exact match, wrong deadline, wrong amount, unsupported, etc.
- Claims maintain a strict `Review Status` (`CANDIDATE`, `REVIEWED`, `GOLD`). Automatic promotion to GOLD is strictly forbidden.

### STEP 9: Claim-Level Typed Verification
- Decompose student queries into typed fields (audience, action, deadline, etc.).
- Deterministic comparison between the student's claimed fields and retrieved evidence fields.

### STEP 10: Temporal / Supersession Resolution
- Evidence-backed resolution of temporal edges.
- Resolves conflicts when a claim matches an older notice but is superseded by a newer one.

### STEP 11: Coverage-Aware Abstention
- Explicit, configurable thresholds based on retrieval ranking and field coverage to return `INSUFFICIENT EVIDENCE`.
- Hardcoded arbitrary thresholds are forbidden; they must be calibrated against a dev set.

### STEP 12: API + Product Integration
- Build FastAPI routes for the three main capabilities.
- Build the Streamlit interface matching the vision.

### STEP 13 & 14: E2E Evaluation & Hardening
- Rigorous pipeline benchmarking, caching, pre-computation optimizations to mitigate LLM latency, UI loading states, and demo seeding.

## 5. LOCAL-AI / PROVIDER ABSTRACTION
The current baseline uses Qwen3 4B via Ollama. Given high latency (~137s per extraction), extraction is strictly asynchronous. All semantic operations (LLM / Embeddings) must be hidden behind provider abstractions to allow swapping without breaking the core pipeline.


> [!WARNING]
> **Benchmark Limitation Note:**
> The current Step 7 benchmark queries are source-derived from human-reviewed official notices. Therefore, the high retrieval metrics measure retrieval on evidence-grounded/source-derived queries and must not be presented as performance on naturally occurring student paraphrases.
