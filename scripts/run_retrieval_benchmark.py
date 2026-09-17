import json
import time
from pathlib import Path
import sqlite3
from typing import List

from app.db.database import get_connection
from app.retrieval.chunking import chunk_notice_version
from app.retrieval.base import RetrievalChunk
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.models.obligation import CanonicalNoticeAnnotation

def load_corpus() -> List[RetrievalChunk]:
    chunks = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                nv.notice_id, nv.version_id, n.source_id, 
                nv.raw_text, n.title, n.publication_date, n.canonical_url,
                (nv.content_hash = n.current_content_hash) as is_latest
            FROM notice_versions nv
            JOIN notices n ON nv.notice_id = n.notice_id
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            raise RuntimeError("SQLite database 'notice_versions' is empty. Do not fall back to annotations.")
            
        for row in rows:
            notice_id, version_id, source_id, raw_text, title, pub_date, url, is_latest = row
            
            new_chunks = chunk_notice_version(
                notice_id=notice_id,
                version_id=version_id,
                source_id=source_id,
                raw_text=raw_text,
                title=title,
                publication_date=None, # simplify date parsing for benchmark
                canonical_url=url,
                is_latest_version=bool(is_latest)
            )
            chunks.extend(new_chunks)
    return chunks

def load_queries():
    queries = []
    annotations_dir = Path("data/annotations/batch_001")
    for file_path in annotations_dir.glob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            a = CanonicalNoticeAnnotation(**data)
            for obl in a.obligations:
                if obl.action:
                    # Action query
                    queries.append({
                        "query": obl.action.text,
                        "target_notice_id": a.notice_id,
                        "target_version_id": a.version_id
                    })
                    # Action + Audience query
                    if obl.audience and obl.audience.raw_text:
                        queries.append({
                            "query": f"{obl.audience.raw_text} {obl.action.text}",
                            "target_notice_id": a.notice_id,
                            "target_version_id": a.version_id
                        })
                    # Action + Deadline query
                    if obl.deadline:
                        queries.append({
                            "query": f"{obl.action.text} {obl.deadline.raw_text}",
                            "target_notice_id": a.notice_id,
                            "target_version_id": a.version_id
                        })
                    # Action + Required Document
                    if obl.required_documents:
                        queries.append({
                            "query": f"{obl.action.text} {obl.required_documents[0].text}",
                            "target_notice_id": a.notice_id,
                            "target_version_id": a.version_id
                        })
    return queries

def evaluate_retriever(retriever, queries, name="Retriever"):
    hits_1 = 0
    hits_3 = 0
    hits_5 = 0
    recalls_1 = 0
    recalls_3 = 0
    recalls_5 = 0
    mrr_sum = 0.0
    latencies = []
    
    for q in queries:
        start_time = time.time()
        results = retriever.search(q["query"], top_k=5)
        latencies.append(time.time() - start_time)
        
        target_n_id = q["target_notice_id"]
        target_v_id = q["target_version_id"]
        
        # Relevance is evaluated at the notice_id + version_id level
        hit_at_1 = False
        hit_at_3 = False
        hit_at_5 = False
        best_rank = None
        
        # We only count 1 relevant document (the target version)
        # So hit@k is the same as recall@k for a single relevant document.
        
        for r in results:
            if r.chunk.notice_id == target_n_id and r.chunk.version_id == target_v_id:
                if best_rank is None:
                    best_rank = r.rank
                if r.rank <= 1: hit_at_1 = True
                if r.rank <= 3: hit_at_3 = True
                if r.rank <= 5: hit_at_5 = True
                
        if hit_at_1: hits_1 += 1
        if hit_at_3: hits_3 += 1
        if hit_at_5: hits_5 += 1
        
        if hit_at_1: recalls_1 += 1
        if hit_at_3: recalls_3 += 1
        if hit_at_5: recalls_5 += 1
        
        if best_rank is not None:
            mrr_sum += 1.0 / best_rank
            
    n = len(queries)
    if n == 0:
        return {}
        
    metrics = {
        "Hit@1": hits_1 / n,
        "Hit@3": hits_3 / n,
        "Hit@5": hits_5 / n,
        "Recall@1": recalls_1 / n,
        "Recall@3": recalls_3 / n,
        "Recall@5": recalls_5 / n,
        "MRR": mrr_sum / n,
        "latency_mean_ms": sum(latencies)/n * 1000,
        "latency_median_ms": sorted(latencies)[n//2] * 1000 if n > 0 else 0
    }
    
    print(f"\n--- {name} Results ---")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")
        
    return metrics

def main():
    print("Loading corpus...")
    chunks = load_corpus()
    print(f"Loaded {len(chunks)} chunks from DB.")
    
    print("Loading queries...")
    queries = load_queries()
    print(f"Loaded {len(queries)} queries from annotations.")
    
    bm25 = BM25Retriever()
    print("Indexing BM25...")
    bm25.index(chunks)
    
    dense = DenseRetriever()
    print("Indexing Dense...")
    dense.index(chunks)
    
    hybrid = HybridRetriever([bm25, dense])
    print("Indexing Hybrid...")
    hybrid.index(chunks)
    
    bm25_metrics = evaluate_retriever(bm25, queries, "BM25Plus")
    dense_metrics = evaluate_retriever(dense, queries, "Dense")
    hybrid_metrics = evaluate_retriever(hybrid, queries, "Hybrid")
    
    out_dir = Path("data/benchmark/retrieval")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "bm25": bm25_metrics,
            "dense": dense_metrics,
            "hybrid": hybrid_metrics,
            "corpus_size_chunks": len(chunks)
        }, f, indent=2)

if __name__ == "__main__":
    main()
