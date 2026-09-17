import json
import os
from pathlib import Path
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.retrieval.base import Retriever, RetrievalChunk, RetrievalResult
from app.core.config import settings

class DenseRetriever(Retriever):
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small", cache_dir: str = "data/processed/retrieval"):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is not installed.")
        
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = SentenceTransformer(self.model_name)
        self.chunks: List[RetrievalChunk] = []
        self.embeddings: np.ndarray | None = None
        
    def _get_passage_text(self, chunk: RetrievalChunk) -> str:
        # Asymmetric retrieval format for e5 models
        return f"passage: {chunk.title} {chunk.text}"
        
    def _get_query_text(self, query: str) -> str:
        return f"query: {query}"
        
    def index(self, chunks: List[RetrievalChunk]) -> None:
        self.chunks = chunks
        
        # TODO: Implement granular cache invalidation. For now, recompute or load if exact match.
        texts = [self._get_passage_text(c) for c in chunks]
        
        if not texts:
            self.embeddings = np.array([])
            return
            
        print(f"Generating dense embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        self.embeddings = np.array(embeddings)
        
        # Save to cache
        np.save(self.cache_dir / "embeddings.npy", self.embeddings)
        with open(self.cache_dir / "manifest.json", "w", encoding="utf-8") as f:
            manifest = [c.model_dump(mode="json") for c in chunks]
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            
    def load_cache(self) -> bool:
        emb_path = self.cache_dir / "embeddings.npy"
        man_path = self.cache_dir / "manifest.json"
        if emb_path.exists() and man_path.exists():
            self.embeddings = np.load(emb_path)
            with open(man_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                self.chunks = [RetrievalChunk(**m) for m in manifest]
            return True
        return False
        
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []
            
        q_text = self._get_query_text(query)
        q_emb = self.model.encode([q_text], normalize_embeddings=True)[0]
        
        # Cosine similarity (since vectors are normalized, dot product is equivalent)
        scores = np.dot(self.embeddings, q_emb)
        
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(ranked_indices):
            results.append(RetrievalResult(
                chunk=self.chunks[idx],
                rank=rank + 1,
                score=float(scores[idx]),
                retrieval_method="dense"
            ))
            
        return results
