# V2.2 AI Core plan (design only)

AI may perceive and understand text, image OCR, and URLs; official evidence
must support facts; deterministic rules decide trust. In short:

**AI UNDERSTANDS. EVIDENCE SUPPORTS. RULES DECIDE TRUST.**

Future work can add schema-validated structured extraction with spans and
confidence, multi-claim decomposition, a reranker after BM25+E5 candidate
retrieval, structured version-change explanations, and screenshot field
grounding. None may assign a verification verdict independently.

Evaluation must separate held-out source-derived cases, same-set development
measurements, controlled synthetic safety cases, and real-source cases. New
rerankers must use a new held-out benchmark rather than optimize frozen Step
18H material.
