"""Read-only demo checks. Never load the model, seed data, or contact the Hub."""

import importlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def database_path(database_url: str, root: Path = PROJECT_ROOT) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Demo requires a SQLite DATABASE_URL.")
    path = Path(database_url[len(prefix):])
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def check_database(path: Path) -> bool:
    if not path.is_file():
        print(f"[FAIL] Database is missing: {path}. Prepare the demo snapshot first.")
        return False
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as conn:
            if conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("integrity_check failed")
            count = conn.execute("""
                SELECT COUNT(*) FROM notice_versions v
                JOIN notices n ON v.notice_id = n.notice_id
                JOIN sources s ON n.source_id = s.source_id
                WHERE LENGTH(TRIM(v.raw_text)) > 0
                  AND v.version_id IS NOT NULL AND v.content_hash IS NOT NULL
                  AND n.title IS NOT NULL AND n.current_content_hash IS NOT NULL
                  AND s.name IS NOT NULL
            """).fetchone()[0]
            conn.execute("SELECT publication_date, canonical_url FROM notices LIMIT 1")
            version = conn.execute(
                "SELECT value FROM app_meta WHERE key = 'schema_version'"
            ).fetchone()
            if not count or not version or version[0] != "0.2":
                raise ValueError("demo schema or nonempty notice corpus is missing")
        print(f"[PASS] Database integrity/schema: {count} nonempty notice versions ({path})")
        return True
    except (sqlite3.Error, ValueError, OSError) as exc:
        print(f"[FAIL] Database is not ready: {exc}")
        return False


def check_annotations(path: Path) -> bool:
    from app.models.obligation import AnnotationStatus, CanonicalNoticeAnnotation

    files = sorted(path.glob("*.json"))
    if not files:
        print(f"[FAIL] Reviewed annotations are missing or empty: {path}")
        return False
    obligations = 0
    try:
        for file in files:
            annotation = CanonicalNoticeAnnotation.model_validate_json(file.read_text(encoding="utf-8"))
            if annotation.annotation_status not in (AnnotationStatus.REVIEWED, AnnotationStatus.GOLD):
                raise ValueError(f"{file.name} is not reviewed")
            obligations += len(annotation.obligations)
        if not obligations:
            raise ValueError("no reviewed obligations found")
    except (OSError, ValueError) as exc:
        print(f"[FAIL] Reviewed annotation validation: {exc}")
        return False
    print(f"[PASS] Reviewed annotations: {len(files)} files, {obligations} obligations")
    return True


def check_imports() -> bool:
    ready = True
    for module in ("fastapi", "pydantic", "pydantic_settings", "httpx", "uvicorn"):
        try:
            importlib.import_module(module)
            print(f"[PASS] Import: {module}")
        except ImportError as exc:
            print(f"[FAIL] Import: {module} ({exc})")
            ready = False
    # Importing torch here duplicates the expensive backend import and does
    # not establish that the model is ready; check heavy packages without loading.
    for module in ("streamlit", "streamlit_searchbox", "sentence_transformers", "torch", "numpy", "rank_bm25", "huggingface_hub"):
        if importlib.util.find_spec(module) is None:
            print(f"[FAIL] Missing package: {module}")
            ready = False
        else:
            print(f"[PASS] Package available: {module}")
    return ready


def port_owners(port: int) -> list[dict]:
    """Best effort Windows diagnostics, bounded and never terminating anything."""
    if os.name != "nt":
        return []
    script = (
        f"Get-NetTCPConnection -LocalPort {int(port)} -State Listen -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { "
        "Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_) | "
        "Select-Object ProcessId,Name } | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=5, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        return [data] if isinstance(data, dict) else data
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return []


def check_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            print(f"[FAIL] Port {port} is occupied. Stop the confirmed owner before restarting.")
            for owner in port_owners(port):
                # Do not print arbitrary command lines, which can contain secrets.
                print(f"       PID {owner.get('ProcessId')}: {owner.get('Name', 'unknown')}")
            return False
    print(f"[PASS] Port {port} is free")
    return True


def check_model_cache() -> bool:
    from app.retrieval.model_cache import resolve_local_model

    try:
        snapshot = resolve_local_model()
    except (OSError, ValueError) as exc:
        print(f"[FAIL] Offline dense model: {exc}")
        return False
    print(f"[PASS] Offline dense model files: {snapshot}")
    return True


def main() -> int:
    from app.core.config import settings

    started = time.monotonic()
    print("--- UniTrust preflight (read-only, offline) ---")
    try:
        db_ready = check_database(database_path(settings.database_url))
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        db_ready = False
    checks = [db_ready, check_imports()]
    try:
        checks.append(check_annotations(PROJECT_ROOT / "data/annotations/batch_001"))
        checks.append(check_model_cache())
    except ImportError as exc:
        print(f"[FAIL] Required package is unavailable: {exc}")
        checks.append(False)
    checks.extend(check_port_free(port) for port in (8000, 8501))
    ok = all(checks)
    print(f"Preflight {'PASSED' if ok else 'FAILED'} in {time.monotonic() - started:.2f}s.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
