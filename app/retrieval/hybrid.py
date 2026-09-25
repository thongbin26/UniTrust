from typing import List, Dict
from app.retrieval.base import Retriever, RetrievalChunk, RetrievalResult

class HybridRetriever(Retriever):
    def __init__(self, retrievers: List[Retriever], rrf_k: int = 60):
        """
        Initializes a hybrid retriever using Reciprocal Rank Fusion (RRF).
        :param retrievers: List of initialized and indexed retrievers.
        :param rrf_k: The RRF constant.
        """
        self.retrievers = retrievers
        self.rrf_k = rrf_k
        self.chunks = []
        
    def index(self, chunks: List[RetrievalChunk]) -> None:
        self.chunks = chunks
        for retriever in self.retrievers:
            retriever.index(chunks)
            
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        chunk_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievalChunk] = {}
        
        # We query top_k * 2 from each retriever to get enough candidates for fusion
        for retriever in self.retrievers:
            results = retriever.search(query, top_k=top_k * 2)
            for res in results:
                chunk_id = res.chunk.chunk_id
                chunk_map[chunk_id] = res.chunk
                
                # RRF score: 1 / (k + rank)
                rrf_score = 1.0 / (self.rrf_k + res.rank)
                chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0.0) + rrf_score
                
        # Sort by RRF score descending
        sorted_chunks = sorted(chunk_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        
        final_results = []
        for rank, (chunk_id, score) in enumerate(sorted_chunks):
            final_results.append(RetrievalResult(
                chunk=chunk_map[chunk_id],
                rank=rank + 1,
                score=score,
                retrieval_method="hybrid_rrf"
            ))
            
        return final_results

    def search_current(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Search only current-version chunks without changing global search.

        Historical chunks stay indexed for audit/history features.  This
        verification-specific view asks each retriever for the full small
        corpus, filters by the persisted latest-version flag, then performs
        the unchanged RRF fusion over only current evidence.
        """
        if not self.chunks:
            return []

        chunk_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievalChunk] = {}
        for retriever in self.retrievers:
            for result in retriever.search(query, top_k=len(self.chunks)):
                if not result.chunk.is_latest_version:
                    continue
                chunk_id = result.chunk.chunk_id
                chunk_map[chunk_id] = result.chunk
                rrf_score = 1.0 / (self.rrf_k + result.rank)
                chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0.0) + rrf_score

        ranked = sorted(chunk_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            RetrievalResult(
                chunk=chunk_map[chunk_id],
                rank=rank + 1,
                score=score,
                retrieval_method="hybrid_rrf_current",
            )
            for rank, (chunk_id, score) in enumerate(ranked)
        ]
