import re
from typing import List
from rank_bm25 import BM25Plus
from app.retrieval.base import Retriever, RetrievalChunk, RetrievalResult

def tokenize(text: str) -> List[str]:
    """Simple deterministic tokenization preserving Vietnamese diacritics."""
    # Lowercase and split by non-alphanumeric (keeping Vietnamese chars)
    # \w matches unicode word characters including Vietnamese diacritics
    return [t for t in re.split(r'\W+', text.lower()) if t]

class BM25Retriever(Retriever):
    def __init__(self):
        self.chunks: List[RetrievalChunk] = []
        self.bm25: BM25Plus | None = None
        
    def index(self, chunks: List[RetrievalChunk]) -> None:
        self.chunks = chunks
        tokenized_corpus = [tokenize(chunk.title + " " + chunk.text) for chunk in chunks]
        self.bm25 = BM25Plus(tokenized_corpus)
        
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if not self.bm25 or not self.chunks:
            return []
            
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Sort by score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for rank, idx in enumerate(ranked_indices):
            if scores[idx] > 0:
                results.append(RetrievalResult(
                    chunk=self.chunks[idx],
                    rank=rank + 1,
                    score=float(scores[idx]),
                    retrieval_method="bm25"
                ))
                
        return results
