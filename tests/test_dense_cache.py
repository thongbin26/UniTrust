"""Cache correctness with deterministic fake vectors; no Hub or real model loads."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

import app.retrieval.dense as dense_module
import app.retrieval.model_cache as model_cache
from app.retrieval.base import RetrievalChunk
from app.retrieval.dense import DenseRetriever


class FakeModel:
    max_seq_length = 512
    device = "cpu"

    def __init__(self, path, **kwargs):
        self.path = path
        self.kwargs = kwargs
        self.calls = []

    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        vectors = np.array([
            [byte + 1 for byte in hashlib.sha256(text.encode()).digest()[:3]]
            for text in texts
        ], dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


@pytest.fixture
def prepared_model(tmp_path, monkeypatch):
    snapshot = tmp_path / "model"
    snapshot.mkdir()
    (snapshot / "config.json").write_text('{"architecture":"test"}', encoding="utf-8")
    (snapshot / "model.safetensors").write_bytes(b"fake-model-weights")
    monkeypatch.setattr(dense_module, "resolve_local_model", lambda model_name: snapshot)
    monkeypatch.setattr(dense_module, "SentenceTransformer", FakeModel)
    return snapshot


@pytest.fixture
def chunks():
    return [RetrievalChunk(
        chunk_id=str(i), notice_id=i, version_id=i, source_id="official-test",
        start_char=0, end_char=7, text=f"Text {i}.", title=f"Notice {i}",
        is_latest_version=True,
    ) for i in (1, 2)]


def make_retriever(tmp_path):
    return DenseRetriever(cache_dir=str(tmp_path / "retrieval"), local_files_only=True)


def test_cache_hit_preserves_scores_order_and_cache_bytes(tmp_path, prepared_model, chunks, caplog):
    first = make_retriever(tmp_path)
    assert first.model.path == str(prepared_model)
    assert first.model.kwargs == {"local_files_only": True}
    first.index(chunks)
    original = first.search("test query")
    assert first.model.calls[0] == (
        ["passage: Notice 1 Text 1.", "passage: Notice 2 Text 2."],
        {"normalize_embeddings": True, "show_progress_bar": False},
    )
    assert first.model.calls[1] == (["query: test query"], {"normalize_embeddings": True})
    saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.cache_dir.iterdir()}

    second = make_retriever(tmp_path)
    with caplog.at_level("INFO"):
        second.index(chunks)
    assert second.model.calls == []
    assert "Dense cache HIT" in caplog.text
    assert second.search("test query") == original
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.cache_dir.iterdir()} == saved


@pytest.mark.parametrize("field,new_value", [
    ("text", "Changed text"), ("title", "Changed title"), ("version_id", 99),
    ("source_id", "changed-source"), ("is_latest_version", False), ("end_char", 20),
])
def test_changed_retrieval_input_rebuilds(tmp_path, prepared_model, chunks, field, new_value):
    make_retriever(tmp_path).index(chunks)
    updated = [chunks[0].model_copy(update={field: new_value}), chunks[1]]
    second = make_retriever(tmp_path)
    second.index(updated)
    assert len(second.model.calls) == 1
    assert second.chunks == updated


@pytest.mark.parametrize("change", ["reverse", "remove", "add"])
def test_order_and_membership_are_part_of_fingerprint(tmp_path, prepared_model, chunks, change):
    make_retriever(tmp_path).index(chunks)
    changed = list(reversed(chunks)) if change == "reverse" else chunks[:1]
    if change == "add":
        changed = chunks + [chunks[0].model_copy(update={"chunk_id": "extra"})]
    second = make_retriever(tmp_path)
    second.index(changed)
    assert len(second.model.calls) == 1
    assert second.chunks == changed


@pytest.mark.parametrize("filename", ["model.safetensors", "config.json"])
def test_model_bytes_invalidate_cache(tmp_path, prepared_model, chunks, filename):
    make_retriever(tmp_path).index(chunks)
    (prepared_model / filename).write_bytes(b"changed-model-input")
    second = make_retriever(tmp_path)
    second.index(chunks)
    assert len(second.model.calls) == 1


def test_embedding_configuration_invalidates_cache(tmp_path, prepared_model, chunks):
    make_retriever(tmp_path).index(chunks)
    second = make_retriever(tmp_path)
    second.model.max_seq_length = 256
    second.index(chunks)
    assert len(second.model.calls) == 1


def test_model_identifier_invalidates_cache(tmp_path, prepared_model, chunks):
    make_retriever(tmp_path).index(chunks)
    second = DenseRetriever(model_name="other/model", cache_dir=str(tmp_path / "retrieval"),
                            local_files_only=True)
    second.index(chunks)
    assert len(second.model.calls) == 1


@pytest.mark.parametrize("corruption", ["legacy", "json", "bytes", "shape", "dtype", "nan", "chunks"])
def test_unusable_cache_rebuilds(tmp_path, prepared_model, chunks, corruption):
    first = make_retriever(tmp_path)
    first.index(chunks)
    manifest_path = first.cache_dir / "manifest.json"
    embedding_path = first.cache_dir / "embeddings.npy"
    manifest = json.loads(manifest_path.read_text())
    if corruption == "legacy":
        manifest_path.write_text(json.dumps(manifest["chunks"]))
    elif corruption == "json":
        manifest_path.write_text("{")
    elif corruption == "bytes":
        embedding_path.write_bytes(b"broken")
    elif corruption == "chunks":
        manifest["chunks"][0]["title"] = "unmatched manifest"
        manifest_path.write_text(json.dumps(manifest))
    else:
        bad = {
            "shape": np.zeros((2, 5)), "dtype": np.zeros((2, 3), dtype=np.int64),
            "nan": np.full((2, 3), np.nan),
        }[corruption]
        np.save(embedding_path, bad)
        manifest["embeddings_sha256"] = hashlib.sha256(embedding_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    second = make_retriever(tmp_path)
    second.index(chunks)
    assert len(second.model.calls) == 1
    assert second.search("query")


def test_failed_cache_write_keeps_usable_in_memory_index(tmp_path, prepared_model, chunks, monkeypatch):
    retriever = make_retriever(tmp_path)
    monkeypatch.setattr(dense_module.os, "replace", lambda *args: (_ for _ in ()).throw(PermissionError()))
    retriever.index(chunks)
    assert len(retriever.search("query")) == 2
    assert list(retriever.cache_dir.iterdir()) == []


def test_empty_index_does_not_reuse_prior_chunks(tmp_path, prepared_model, chunks):
    retriever = make_retriever(tmp_path)
    retriever.index(chunks)
    retriever.index([])
    assert retriever.search("query") == []


def test_explicit_cache_load_validates_saved_inputs(tmp_path, prepared_model, chunks):
    make_retriever(tmp_path).index(chunks)
    second = make_retriever(tmp_path)
    assert second.load_cache()
    assert second.chunks == chunks
    assert second.model.calls == []


def test_local_only_failure_does_not_attempt_online_model_load(tmp_path, monkeypatch):
    def missing(name):
        raise FileNotFoundError("prepare model")
    monkeypatch.setattr(dense_module, "resolve_local_model", missing)
    calls = []
    monkeypatch.setattr(dense_module, "SentenceTransformer", lambda *a, **kw: calls.append((a, kw)))
    with pytest.raises(FileNotFoundError, match="prepare model"):
        make_retriever(tmp_path)
    assert not calls


def test_developer_fallback_only_when_local_model_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(dense_module, "resolve_local_model",
                        lambda name: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(dense_module, "SentenceTransformer", FakeModel)
    retriever = DenseRetriever(cache_dir=str(tmp_path), local_files_only=False)
    assert retriever.model.path == model_cache.DEFAULT_MODEL_NAME
    assert retriever.model.kwargs == {}
    assert retriever.model_identity is None


def test_model_identity_is_portable_and_ignores_readme(tmp_path):
    for name in ("one", "two"):
        path = tmp_path / name
        path.mkdir()
        (path / "config.json").write_text("{}")
        (path / "model.safetensors").write_bytes(b"same")
        (path / "README.md").write_text(name)
    assert dense_module._model_identity(tmp_path / "one") == dense_module._model_identity(tmp_path / "two")


def test_model_resolver_checks_completeness_without_model_loading(tmp_path, monkeypatch):
    for relative in model_cache._REQUIRED_JSON:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    calls = []
    monkeypatch.setenv("SENTENCE_TRANSFORMERS_HOME", "custom-cache")
    def find_cached(*args, **kwargs):
        calls.append((args, kwargs))
        return str(tmp_path / "config.json")
    monkeypatch.setattr(model_cache, "try_to_load_from_cache", find_cached)
    assert model_cache.resolve_local_model() == tmp_path
    assert calls == [((model_cache.DEFAULT_MODEL_NAME, "config.json"), {"cache_dir": "custom-cache"})]
    (tmp_path / "1_Pooling/config.json").unlink()
    with pytest.raises(FileNotFoundError, match="incomplete"):
        model_cache.resolve_local_model()


def test_model_resolver_reports_missing_cached_revision(monkeypatch):
    monkeypatch.setattr(model_cache, "try_to_load_from_cache", lambda *a, **kw: None)
    with pytest.raises(FileNotFoundError, match="unavailable"):
        model_cache.resolve_local_model()
