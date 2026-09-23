from io import BytesIO

import httpx
from PIL import Image
import pytest

from app.ocr.models import OCRProcessingError
from app.ocr.sidecar_provider import LocalOCRSidecarProvider


def sample_image():
    return Image.new("RGB", (12, 8), "white")


def test_sidecar_provider_serializes_png_and_preserves_vietnamese_unicode(monkeypatch):
    captured = {}

    def post(url, *, content, headers, timeout):
        captured.update(url=url, content=content, headers=headers, timeout=timeout)
        return httpx.Response(200, json={
            "text": "Sinh viên đóng học phí 450.000 đồng.",
            "engine": "paddleocr",
            "warnings": [],
            "mean_confidence": 0.99,
        })

    monkeypatch.setattr(httpx, "post", post)
    result = LocalOCRSidecarProvider().extract_text(sample_image())

    assert result.text == "Sinh viên đóng học phí 450.000 đồng."
    assert captured["url"] == "http://127.0.0.1:8765/ocr"
    assert captured["headers"] == {"Content-Type": "image/png"}
    assert captured["timeout"] == 60.0
    assert Image.open(BytesIO(captured["content"])).format == "PNG"


@pytest.mark.parametrize("error", [httpx.ConnectError("offline"), httpx.ReadTimeout("slow")])
def test_sidecar_provider_maps_transport_errors_to_unavailable(monkeypatch, error):
    def post(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(OCRProcessingError, match="unavailable") as raised:
        LocalOCRSidecarProvider().extract_text(sample_image())
    assert raised.value.code == "OCR_UNAVAILABLE"


@pytest.mark.parametrize(
    "response",
    [httpx.Response(503), httpx.Response(200, content=b"not json"), httpx.Response(200, json={"text": 1})],
)
def test_sidecar_provider_maps_bad_responses_to_failed(monkeypatch, response):
    monkeypatch.setattr(httpx, "post", lambda *_args, **_kwargs: response)
    with pytest.raises(OCRProcessingError) as raised:
        LocalOCRSidecarProvider().extract_text(sample_image())
    assert raised.value.code == "OCR_FAILED"


def test_sidecar_provider_rejects_non_loopback_operator_url():
    with pytest.raises(OCRProcessingError) as raised:
        LocalOCRSidecarProvider(sidecar_url="http://example.org:8765")
    assert raised.value.code == "OCR_UNAVAILABLE"
