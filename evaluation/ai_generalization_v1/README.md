# AI Generalization Evaluation Pack V1

This pack is an offline, provider-independent evaluation foundation. It is not
Gemini qualification and does not authorize runtime provider integration.

## Population

`dataset.jsonl` contains one record per current notice without reviewed
obligations, or one record per existing reviewed obligation. Records are
strictly separated into:

- `HUMAN_ACCEPTED`: existing `REVIEWED`/`GOLD` annotation reused verbatim with
  its source and evidence-span references.
- `CANDIDATE_UNREVIEWED`: current official notice requiring a reviewer to
  `ACCEPT / EDIT / REJECT`. These records never enter metrics.

`review_worksheet.jsonl` is the compact human-review queue. It includes the
complete source text, deterministic proposals, exact proposal offsets, and
source provenance. A null reviewed claim span means the existing annotation
does not provide one; it is not inferred here.

## Reproduction

Build only from local production data and existing annotations:

```powershell
.venv\Scripts\python.exe evaluation\ai_generalization_v1\build_pack.py
```

Run metrics with local model files and the already-published dense cache:

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
.venv\Scripts\python.exe evaluation\ai_generalization_v1\run_evaluation.py
```

The evaluator refuses to rebuild the dense cache. It uses `search_current`, so
historical versions are retained for audit but cannot count as retrieval hits.

## Future Provider Contract

A future qualified provider must submit predictions keyed by `record_id` with
`provider_id`, `model_id`, grounded `field_spans`, and normalized values. The
same `HUMAN_ACCEPTED` population and field contracts are then used for
`CURRENT_BASELINE` versus `GEMINI`; this pack itself makes no provider call.
