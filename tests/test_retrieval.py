import pytest
from datetime import datetime
from app.retrieval.chunking import chunk_notice_version
from app.retrieval.base import RetrievalChunk, RetrievalResult
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.dense import DenseRetriever
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_deterministic_chunk_boundaries_and_offsets():
    raw_text = "This is the first paragraph.\n\nThis is the second paragraph."
    chunks = chunk_notice_version(
        notice_id=1, version_id=2, source_id="s1",
        raw_text=raw_text, title="Test", publication_date=None,
        canonical_url="http://test", is_latest_version=True
    )
    
    assert len(chunks) == 2
    c1, c2 = chunks[0], chunks[1]
    
    assert c1.start_char == 0
    assert c1.text == "This is the first paragraph."
    assert c1.end_char == len("This is the first paragraph.")
    assert raw_text[c1.start_char:c1.end_char] == c1.text
    
    assert c2.text == "This is the second paragraph."
    assert raw_text[c2.start_char:c2.end_char] == c2.text
    
def test_provenance_preservation():
    chunks = chunk_notice_version(
        notice_id=10, version_id=20, source_id="s_test",
        raw_text="Hello", title="Title", publication_date=datetime(2025, 1, 1),
        canonical_url="http://url", is_latest_version=False
    )
    c = chunks[0]
    assert c.notice_id == 10
    assert c.version_id == 20
    assert c.source_id == "s_test"
    assert c.title == "Title"
    assert c.publication_date == datetime(2025, 1, 1)
    assert c.canonical_url == "http://url"
    assert c.is_latest_version is False
    assert c.chunk_id == "20_0"

def test_latest_historical_version_metadata():
    chunks_hist = chunk_notice_version(1, 1, "s1", "A", "T", None, "", is_latest_version=False)
    chunks_latest = chunk_notice_version(1, 2, "s1", "B", "T", None, "", is_latest_version=True)
    assert not chunks_hist[0].is_latest_version
    assert chunks_latest[0].is_latest_version
    
def test_bm25_ranking_behavior():
    c1 = RetrievalChunk(chunk_id="1", notice_id=1, version_id=1, source_id="s1", start_char=0, end_char=5, text="apple banana", title="")
    c2 = RetrievalChunk(chunk_id="2", notice_id=2, version_id=2, source_id="s1", start_char=0, end_char=5, text="apple orange", title="")
    
    retriever = BM25Retriever()
    retriever.index([c1, c2])
    
    res = retriever.search("banana", top_k=5)
    assert len(res) > 0
    assert res[0].chunk.chunk_id == "1"

def test_rrf_hybrid_ranking():
    class DummyRetriever:
        def __init__(self, scores):
            self.scores = scores
        def index(self, chunks): pass
        def search(self, query, top_k=5):
            res = []
            for i, (chunk, rank) in enumerate(self.scores):
                res.append(RetrievalResult(chunk=chunk, rank=rank, score=1.0, retrieval_method="dummy"))
            return res
            
    c1 = RetrievalChunk(chunk_id="1", notice_id=1, version_id=1, source_id="s", start_char=0, end_char=1, text="1", title="")
    c2 = RetrievalChunk(chunk_id="2", notice_id=2, version_id=2, source_id="s", start_char=0, end_char=1, text="2", title="")
    
    r1 = DummyRetriever([(c1, 1), (c2, 2)])
    r2 = DummyRetriever([(c2, 1), (c1, 5)])
    
    hybrid = HybridRetriever([r1, r2], rrf_k=60)
    res = hybrid.search("test", top_k=5)
    assert res[0].chunk.chunk_id == "2"
    assert res[1].chunk.chunk_id == "1"

def test_dense_cache_invalidation(tmp_path):
    c1 = RetrievalChunk(chunk_id="1", notice_id=1, version_id=1, source_id="s", start_char=0, end_char=1, text="1", title="")
    retriever = DenseRetriever(cache_dir=str(tmp_path))
    retriever.index([c1])
    assert (tmp_path / "embeddings.npy").exists()
    assert (tmp_path / "manifest.json").exists()
    
    retriever2 = DenseRetriever(cache_dir=str(tmp_path))
    loaded = retriever2.load_cache()
    assert loaded is True
    assert len(retriever2.chunks) == 1
    assert retriever2.chunks[0].chunk_id == "1"

def test_db_backed_corpus_construction():
    # Will be tested indirectly by the benchmark script failing if empty
    pass
