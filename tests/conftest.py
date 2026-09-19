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

    original_database_url = settings.database_url
    settings.database_url = f"sqlite:///{database_path}"

    import app.retrieval.dense as dense_module

    original_dense_retriever = dense_module.DenseRetriever

    class IsolatedDenseRetriever(original_dense_retriever):
        def __init__(self, model_name="intfloat/multilingual-e5-small", cache_dir=None):
            super().__init__(
                model_name=model_name,
                cache_dir=str(retrieval_cache) if cache_dir is None else cache_dir,
            )

    dense_module.DenseRetriever = IsolatedDenseRetriever
    try:
        yield {
            "database_path": database_path,
            "retrieval_cache": retrieval_cache,
        }
    finally:
        dense_module.DenseRetriever = original_dense_retriever
        settings.database_url = original_database_url
        assert _protected_hashes(root) == protected_before


@pytest.fixture(scope="session")
def isolated_app_client(isolated_runtime_artifacts):
    from main import app

    with TestClient(app) as client:
        yield client
