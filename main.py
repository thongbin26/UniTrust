from contextlib import asynccontextmanager, contextmanager
import logging
from time import perf_counter
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.sources import router as sources_router
from app.api.routes.verify import router as verify_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.for_you import router as for_you_router
from app.core.config import settings
from app.db.database import init_database
from app.sources.repository import seed_sources
from app.sources.seed import BASELINE_SOURCES

logger = logging.getLogger("uvicorn.error")


@contextmanager
def startup_step(name: str):
    started = perf_counter()
    yield
    logger.info("Startup %s: %.3fs", name, perf_counter() - started)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_ready = False
    with startup_step("database initialization"):
        init_database()
    with startup_step("source registry"):
        # Phase A must not migrate or update the production source registry.
        # A fresh demo DB may receive the three baseline rows, but existing rows
        # remain byte-stable until production ingestion is explicitly approved.
        seed_sources(sources=BASELINE_SOURCES, update_existing=False)

    # Initialize expensive singletons once
    with startup_step("retrieval imports"):
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
    with startup_step("dense model loading"):
        dense = DenseRetriever()
    hybrid = HybridRetriever([bm25, dense])

    with startup_step("corpus loading"):
        chunks = build_corpus()
    with startup_step("BM25 and dense indexing"):
        hybrid.index(chunks)

    decomposer = ClaimDecomposer(use_llm_fallback=False)
    with startup_step("reviewed annotations"):
        repo = OfficialStructuredRepository()
    policy = AbstentionPolicy()

    app.state.repository = repo
    app.state.verification_service = VerificationService(hybrid, decomposer, repo, policy)

    app.state.startup_ready = True
    try:
        yield
    finally:
        app.state.startup_ready = False


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
