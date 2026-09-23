from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import get_verification_service
from app.api.routes.verify_image import get_ocr_provider, router
from app.ocr.models import OCRProcessingError, OCRResult
from app.verification.models import OverallVerdict, VerificationResult


def image_bytes(image_format="PNG"):
    output = BytesIO()
    Image.new("RGB", (24, 16), "white").save(output, format=image_format)
    return output.getvalue()


class FakeOCRProvider:
    def __init__(self, result=None, error=None):
        self.result = result or OCRResult(
            text="Sinh viên K26 đóng học phí 450.000 đồng.\nHạn cuối: 30/09/2026",
            engine="fake",
        )
        self.error = error
        self.images = []

    def extract_text(self, image):
        self.images.append(image)
        if self.error:
            raise self.error
        return self.result


class RecordingVerificationService:
    def __init__(self):
        self.calls = []

    def verify(self, text, top_k=5):
        self.calls.append((text, top_k))
        return [VerificationResult(
            claim_id="fake",
            raw_claim_text=text,
            verdict=OverallVerdict.INSUFFICIENT_EVIDENCE,
        )]


def client(provider=None, service=None):
    app = FastAPI()
    app.include_router(router)
    service = service or RecordingVerificationService()
    app.dependency_overrides[get_verification_service] = lambda: service
    app.dependency_overrides[get_ocr_provider] = lambda: provider or FakeOCRProvider()
    return TestClient(app), service


def test_image_endpoint_passes_exact_unicode_ocr_text_once_with_default_top_k():
    provider = FakeOCRProvider()
    test_client, service = client(provider)

    response = test_client.post(
        "/verify/image",
        files={"image": ("notice.png", image_bytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert service.calls == [(provider.result.text, 5)]
    assert payload["input_type"] == "IMAGE"
    assert payload["ocr"]["text"] == provider.result.text
    assert "Sinh viên K26 đóng học phí 450.000 đồng." in payload["ocr"]["text"]


def test_image_endpoint_forwards_top_k_and_accepts_inactive_use_llm():
    test_client, service = client()

    response = test_client.post(
        "/verify/image",
        files={"image": ("notice.webp", image_bytes("WEBP"), "image/webp")},
        data={"top_k": "7", "use_llm": "true"},
    )

    assert response.status_code == 200
    assert service.calls[0][1] == 7


def test_image_endpoint_rejects_invalid_image_before_verification():
    test_client, service = client()

    response = test_client.post("/verify/image", files={"image": ("notice.png", b"invalid", "image/png")})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_IMAGE"
    assert not service.calls


def test_empty_ocr_text_is_not_converted_into_retrieval_abstention():
    provider = FakeOCRProvider(result=OCRResult(text="  ", engine="fake"))
    test_client, service = client(provider)

    response = test_client.post("/verify/image", files={"image": ("notice.jpg", image_bytes("JPEG"), "image/jpeg")})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "NO_TEXT_DETECTED"
    assert not service.calls


def test_unavailable_ocr_is_a_distinct_api_error():
    provider = FakeOCRProvider(error=OCRProcessingError("OCR_UNAVAILABLE", "not installed"))
    test_client, _ = client(provider)

    response = test_client.post("/verify/image", files={"image": ("notice.png", image_bytes(), "image/png")})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "OCR_UNAVAILABLE"


def test_failed_ocr_is_a_distinct_api_error():
    provider = FakeOCRProvider(error=OCRProcessingError("OCR_FAILED", "engine error"))
    test_client, _ = client(provider)

    response = test_client.post("/verify/image", files={"image": ("notice.png", image_bytes(), "image/png")})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "OCR_FAILED"


def test_image_endpoint_rejects_invalid_top_k_before_verification():
    test_client, service = client()

    response = test_client.post(
        "/verify/image",
        files={"image": ("notice.png", image_bytes(), "image/png")},
        data={"top_k": "0"},
    )

    assert response.status_code == 422
    assert not service.calls
