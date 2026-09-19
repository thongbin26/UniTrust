"""Keep every pytest run away from production database and retrieval artifacts."""

import shutil
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _protected_hashes(root):
    paths = [root / "unitrust.db", root / "data/catalog/dut_catalog_2026.json"]
    for directory in ("data/annotations", "data/benchmark", "data/processed/retrieval"):
        paths.extend(path for path in (root / directory).rglob("*") if path.is_file())
    return {
        path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


@pytest.fixture(scope="session", autouse=True)
def isolated_runtime_artifacts(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    protected_before = _protected_hashes(root)
    runtime_dir = tmp_path_factory.mktemp("unitrust-runtime")
    database_path = runtime_dir / "unitrust.db"
    retrieval_cache = runtime_dir / "retrieval"
    shutil.copy2(root / "unitrust.db", database_path)

    try:
        with pytest.MonkeyPatch.context() as runtime_config:
            runtime_config.setattr(settings, "database_url", f"sqlite:///{database_path}")
            runtime_config.setattr(settings, "retrieval_cache_dir", str(retrieval_cache))
            runtime_config.setattr(settings, "dense_local_files_only", True)
            runtime_config.setenv("HF_HUB_OFFLINE", "1")
            runtime_config.setenv("TRANSFORMERS_OFFLINE", "1")
            yield {
                "database_path": database_path,
                "retrieval_cache": retrieval_cache,
            }
    finally:
        assert _protected_hashes(root) == protected_before


@pytest.fixture(scope="session")
def isolated_app_client(isolated_runtime_artifacts):
    from main import app

    with TestClient(app) as client:
        yield client
