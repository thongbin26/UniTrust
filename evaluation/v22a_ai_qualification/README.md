# V2.2A Q001-Q006 provider qualification workflow

This directory contains the human-accepted Q001-Q006 authoring batch and
offline-first provider qualification tooling. It is separate from frozen
Step 13, Step 18H, and the UniTrust student runtime.

## Stage 1 — Human benchmark acceptance

Complete: Q001-Q006 are the accepted candidates. Rejected Q002/Q004 revisions
remain in the authoring audits and are never loaded by the evaluator.

## Stage 2 — Qualification harness validation

Status: `HUMAN_ACCEPTED`.

Run the static authoring validator and the local evaluator tests. Offline mode
requires `--offline-fixtures` and makes zero provider requests.

```powershell
.venv\Scripts\python.exe evaluation\v22a_ai_qualification\validate_q001_q003.py
.venv\Scripts\python.exe -m pytest tests\test_provider_qualification.py tests\test_gemini_qualification.py
```

## Stage 3 — Provider access smoke

`scripts/run_gemini_qualification_smoke.py` is a separate one-request access
and connectivity check. It is not quality qualification.

## Stage 4 — Real Q001-Q006 provider evaluation

Requires explicit human authorization, `--real-provider`, and the existing
`UNITRUST_ALLOW_REAL_PROVIDER_EVAL=1` lock plus Gemini credentials/model.
The current one-input-per-extraction adapter plans six real requests for the
six accepted samples. Reports are sanitized and written below `reports/`.

## Stage 5 — Threshold review / qualification decision

The human-approved pre-registered policy is in
[`QUALIFICATION_POLICY.md`](QUALIFICATION_POLICY.md). The harness returns only
the policy states defined there; a positive result is limited to evaluated
fields and never authorizes runtime integration.

## Stage 6 — Runtime integration decision

Separate future gate. The current product ignores provider output and preserves
deterministic extraction as its only runtime behavior.
