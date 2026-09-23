from time import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_verification_service
from app.api.routes.verify import verify_claim
from app.api.schemas import OCRResponse, VerifyImageResponse, VerifyRequest
from app.ocr.image_validation import MAX_UPLOAD_BYTES, ImageValidationError, validate_image_bytes
from app.ocr.models import OCRProcessingError
from app.ocr.provider import OCRProvider
from app.ocr.sidecar_provider import LocalOCRSidecarProvider
from app.verification.service import VerificationService


router = APIRouter(prefix="/verify", tags=["Verify"])


def get_ocr_provider() -> OCRProvider:
    """Use the local OCR sidecar; the main application never imports PaddleOCR."""
    return LocalOCRSidecarProvider()


def _raise_ocr_error(error: ImageValidationError | OCRProcessingError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


@router.post("/image", response_model=VerifyImageResponse)
async def verify_image(
    image: UploadFile = File(...),
    top_k: int = Form(5, ge=1, le=20),
    use_llm: bool = Form(False),
    service: VerificationService = Depends(get_verification_service),
    ocr_provider: OCRProvider = Depends(get_ocr_provider),
):
    started = time()
    payload = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        _raise_ocr_error(ImageValidationError("IMAGE_TOO_LARGE", "Image upload exceeds 8 MiB.", 413))
    try:
        decoded = validate_image_bytes(payload, image.filename)
        ocr = ocr_provider.extract_text(decoded)
    except (ImageValidationError, OCRProcessingError) as exc:
        _raise_ocr_error(exc)

    if not ocr.text.strip():
        _raise_ocr_error(OCRProcessingError("NO_TEXT_DETECTED", "No readable text was detected in this image.", 422))

    # Reuse the established JSON response mapping; OCR only supplies its text input.
    verification = verify_claim(VerifyRequest(text=ocr.text, use_llm=use_llm, top_k=top_k), service)
    return VerifyImageResponse(
        input_type="IMAGE",
        ocr=OCRResponse(**ocr.model_dump()),
        original_input=verification.original_input,
        results=verification.results,
        latency_ms=(time() - started) * 1000,
    )
