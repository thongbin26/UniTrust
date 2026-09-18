from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.sources import router as sources_router
from app.api.routes.verify import router as verify_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.for_you import router as for_you_router
from app.core.config import settings
from app.db.database import init_database
from app.sources.repository import seed_sources

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    seed_sources()

    # Initialize expensive singletons once
    from app.retrieval.bm25 import BM25Retriever
    from app.retrieval.dense import DenseRetriever
    from app.retrieval.hybrid import HybridRetriever
    from app.verification.decomposer import ClaimDecomposer
    from app.verification.repository import OfficialStructuredRepository
    from app.verification.abstention import AbstentionPolicy
    from app.verification.service import VerificationService
    from app.retrieval.chunking import build_corpus

    # DenseRetriever loads E5 model here, blocking startup if it's very slow.
    # To keep Ollama optional, we do not require LLM here.
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    hybrid = HybridRetriever([bm25, dense])

    chunks = build_corpus()
    hybrid.index(chunks)

    decomposer = ClaimDecomposer(use_llm_fallback=False)
    repo = OfficialStructuredRepository()
    policy = AbstentionPolicy()

    app.state.repository = repo
    app.state.verification_service = VerificationService(hybrid, decomposer, repo, policy)

    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="UniTrust Competition Demo API",
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(sources_router)
app.include_router(verify_router)
app.include_router(evidence_router)
app.include_router(for_you_router)


@app.get("/")
def root() -> dict:
    return {
        "message": "UniTrust API is running.",
        "docs": "/docs",
        "health": "/health",
        "sources": "/sources",
    }