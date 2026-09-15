from fastapi import APIRouter

from app.db.database import init_database
from app.models.source import (
    SourceCheckResult,
    SourceRead,
)
from app.sources.health import check_all_sources
from app.sources.repository import (
    list_sources,
    seed_sources,
)


router = APIRouter(
    prefix="/sources",
    tags=["sources"],
)


@router.get(
    "",
    response_model=list[SourceRead],
)
def get_sources() -> list[SourceRead]:

    init_database()
    seed_sources()

    return list_sources()


@router.post(
    "/check",
    response_model=list[SourceCheckResult],
)
def check_sources() -> list[SourceCheckResult]:

    init_database()
    seed_sources()

    return check_all_sources()