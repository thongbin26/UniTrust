"""Read-only competition preflight; never starts services or writes product data."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import preflight_demo


EXPECTED_HASHES = {
    "unitrust.db": "F36B66283F6BA2DE0134936A2C0D6551371BB247D6B945B7F87F91359F9CAED0",
    "data/processed/retrieval/embeddings.npy": "664024767936C63330F9F68855F4B25AB6E2E24F9FF9084E4C112E020235D3ED",
    "data/processed/retrieval/manifest.json": "581E5FC64EAD48BD2453028502F0E5F24306C054FFDE2675DAF17FCA9B3F7FDD",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def check_protected_artifacts(root: Path = ROOT) -> bool:
    ok = True
    for relative, expected in EXPECTED_HASHES.items():
        path = root / relative
        actual = sha256(path) if path.is_file() else None
        if actual == expected:
            print(f"[PASS] Protected artifact: {relative}")
        else:
            print(f"[FAIL] Protected artifact: {relative} (expected {expected}, got {actual})")
            ok = False
    sidecars = [root / f"unitrust.db-{suffix}" for suffix in ("wal", "shm", "journal")]
    present = [path.name for path in sidecars if path.exists()]
    if present:
        print(f"[FAIL] SQLite sidecars present: {', '.join(present)}")
        ok = False
    else:
        print("[PASS] No SQLite sidecars")
    return ok


def check_ocr_runtime(path: Path) -> bool:
    if path.is_file():
        print(f"[PASS] OCR runtime: {path}")
        return True
    print(f"[FAIL] OCR runtime missing: {path}")
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-ocr", action="store_true")
    parser.add_argument("--ocr-python", type=Path, default=Path(r"C:\Users\DELL\unitrust-ocr-runtime\.venv\Scripts\python.exe"))
    args = parser.parse_args(argv)
    checks = [check_protected_artifacts(), preflight_demo.check_imports(), preflight_demo.check_model_cache()]
    checks.extend(preflight_demo.check_port_free(port) for port in (8000, 8501))
    if args.with_ocr:
        checks.append(check_ocr_runtime(args.ocr_python))
    result = all(checks)
    print(f"Competition preflight {'PASSED' if result else 'FAILED'}.")
    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
