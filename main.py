from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.db.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="UniTrust V2 Competition Demo API",
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(health_router)


@app.get("/")
def root() -> dict:
    return {
        "message": "UniTrust V2 API is running.",
        "docs": "/docs",
        "health": "/health",
    }