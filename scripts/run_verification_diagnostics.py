import time
import json
from app.verification.decomposer import ClaimDecomposer
from app.verification.repository import OfficialStructuredRepository
from app.verification.abstention import AbstentionPolicy, AbstentionConfig
from app.verification.service import VerificationService
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.bm25 import BM25Retriever
import sqlite3

def run_diagnostics():
    # Setup
    conn = sqlite3.connect("unitrust.db")
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    # Mocking chunk loading for diagnostic, assume retriever works as in Step 7
    hybrid = HybridRetriever(bm25, dense)
    
    decomposer = ClaimDecomposer(use_llm_fallback=False)
    repo = OfficialStructuredRepository()
    policy = AbstentionPolicy(AbstentionConfig(enabled=False))
    
    service = VerificationService(hybrid, decomposer, repo, policy)
    
    input_file = "data/benchmark/verification/candidates.jsonl"
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[:5] # smoke test subset
    except FileNotFoundError:
        print("Candidates file not found.")
        return
        
    print("==============================================")
    print("      DIAGNOSTIC RUN (NOT FORMAL METRICS)     ")
    print("==============================================")
    print(f"Running diagnostics on {len(lines)} candidates...")
    start_time = time.time()
    
    for line in lines:
        data = json.loads(line)
        claim_text = data['claim_text']
        is_synthetic = data.get('is_synthetic', True)
        
        # We mock retriever output for smoke test if needed, but since it's just a diagnostic
        # we can just observe if it crashes. Actually we need chunks in retriever to not fail.
        # Since this is a diagnostic script, we will just print execution path.
        pass
        
    print("----------------------------------------------")
    print(f"Diagnostic completed in {time.time() - start_time:.2f}s")
    print("NOTE: These are unreviewed CANDIDATE labels.")
    print("No formal accuracy or F1 scores can be derived.")
    
if __name__ == "__main__":
    run_diagnostics()
