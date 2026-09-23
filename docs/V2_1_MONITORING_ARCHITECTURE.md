# V2.1 Near-real-time official-source monitoring

The monitor is a separate, opt-in Python worker. It is never started by
Streamlit and is disabled in the frozen RC runtime. Run one V2 development
cycle with:

```powershell
.venv\Scripts\python scripts/run_monitor.py --data-root C:\path\to\unitrust-v2-data --once
```

The script copies the configured bootstrap SQLite database once, writes raw
responses and retrieval cache under the supplied data root, and rejects the
repository runtime path. Continuous mode omits `--once`; the interval defaults
to 600 seconds and cannot be shorter than five minutes.

Each enabled source is processed sequentially. Results are `NEW`, `UPDATED`,
`UNCHANGED`, or `FAILED`. The established notice repository supplies material
content detection and preserves earlier versions. A failed source preserves
existing evidence and does not stop later sources. Monitor state records the
latest outcome, failure count, bounded backoff schedule, errors, and change
times. The `/monitoring/status` endpoint exposes only student-safe aggregate
status when monitoring is enabled.

The current dense manifest is whole-corpus fingerprinted. Therefore V2.1
performs an atomic full-cache publication only after a `NEW` or `UPDATED`
cycle; it performs no embedding work for `UNCHANGED` or `FAILED`. This is the
safest compatible choice for the small current corpus. A future incremental
manifest format can replace it without changing monitor outcomes.
