# Step 18H post-fix evaluation

This directory contains a separate **same-set development comparison**. It
reuses the immutable `18h-v1` inputs against the post-fix product and writes
only under `postfix/reports/`. It is not an independent benchmark.

Run locally and offline:

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
.venv\Scripts\python evaluation\step18h\postfix\run_postfix_evaluation.py
```
