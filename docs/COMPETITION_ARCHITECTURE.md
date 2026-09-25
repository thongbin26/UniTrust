# UniTrust competition architecture

```text
Official DUT sources
  -> crawl, normalization, version-aware SQLite evidence store
  -> chunks + BM25Plus / multilingual-E5 / RRF
  -> reviewed obligation annotations

Student input: Text | Screenshot | URL
  -> text normalization | optional local OCR | safe URL extraction
  -> structured claim
  -> hybrid retrieval
  -> obligation applicability
  -> deterministic field comparison + temporal adjustment
  -> VERIFIED | PARTIALLY_VERIFIED | CONFLICT | INSUFFICIENT_EVIDENCE
  -> official provenance in the UI
```

E5 supports semantic retrieval and PaddleOCR can read screenshots when its
isolated local sidecar is available. AI/ML helps understand or find content;
official evidence and deterministic comparison ground the verdict. No LLM is
currently used to decide truth.
