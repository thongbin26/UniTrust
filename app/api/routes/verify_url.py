from time import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_verification_service
from app.api.routes.verify import verify_claim
from app.api.schemas import URLVerifyRequest, VerifyRequest, VerifyURLResponse
from app.url_fetch.errors import URLFetchError
from app.url_fetch.fetcher import WebContentFetcher
from app.verification.service import VerificationService


router = APIRouter(prefix="/verify", tags=["Verify"])

_ERROR_STATUS = {
    "INVALID_URL": 422,
    "UNSAFE_URL": 422,
    "FETCH_TIMEOUT": 504,
    "FETCH_FAILED": 502,
    "TOO_LARGE": 413,
    "UNSUPPORTED_CONTENT_TYPE": 415,
    "EMPTY_CONTENT": 422,
    "TOO_MANY_REDIRECTS": 422,
}


def get_web_content_fetcher() -> WebContentFetcher:
    return WebContentFetcher()


def _raise_fetch_error(error: URLFetchError) -> None:
    raise HTTPException(
        status_code=_ERROR_STATUS[error.code],
        detail={"code": error.code, "message": error.message},
    )


@router.post("/url", response_model=VerifyURLResponse)
def verify_url(
    request: URLVerifyRequest,
    service: VerificationService = Depends(get_verification_service),
    fetcher: WebContentFetcher = Depends(get_web_content_fetcher),
):
    started = time()
    try:
        extracted = fetcher.fetch(request.url)
    except URLFetchError as exc:
        _raise_fetch_error(exc)

    # The fetched text is untrusted claim input.  The existing service alone
    # retrieves and evaluates official evidence.
    verification = verify_claim(
        VerifyRequest(text=extracted.text, use_llm=request.use_llm, top_k=request.top_k),
        service,
    )
    return VerifyURLResponse(
        input_type="URL",
        requested_url=extracted.requested_url,
        final_url=extracted.final_url,
        page_title=extracted.title,
        extracted_text=extracted.text,
        content_type=extracted.content_type,
        warnings=extracted.warnings,
        original_input=verification.original_input,
        results=verification.results,
        latency_ms=(time() - started) * 1000,
    )
