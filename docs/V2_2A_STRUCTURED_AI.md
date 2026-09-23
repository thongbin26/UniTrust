# V2.2A Structured Claim Understanding

V2.2A keeps deterministic extraction as the default. `TypedUserField` retains
the exact raw span, offsets, normalized value, extraction method, and optional
confidence. Coordinated clauses beginning with supported obligation actions are
decomposed into independent grounded claims. Each claim continues through the
existing retrieval, temporal gate, and deterministic comparator separately.

`StructuredClaimExtractor` is provider-neutral. The shipped optional-AI path
is unavailable by design; it cannot emit a verdict and deterministic fallback
remains available. Future provider outputs must validate against the existing
action/date/amount contracts before entering verification.

Message summaries are deterministic: any conflict wins; all verified means
verified; a verified/insufficient mix is partially verified. Claim results are
always retained as the authoritative detail.
