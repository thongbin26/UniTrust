from io import BytesIO
import json

from PIL import Image

from app.ocr.models import OCRResult
from scripts.ocr_sidecar import (
    MAX_OCR_BODY_BYTES,
    decode_normalized_png,
    handle_ocr_request,
    health_payload,
    ocr_payload,
)


class FakeOCRProvider:
    engine_name = "paddleocr"

    def extract_text(self, image):
        assert image.mode == "RGB"
        return OCRResult(text="Sinh viên K26", engine=self.engine_name, mean_confidence=0.99)


def normalized_png():
    output = BytesIO()
    Image.new("RGB", (12, 8), "white").save(output, format="PNG")
    return output.getvalue()


def test_sidecar_payload_uses_utf8_safe_json_values():
    payload = ocr_payload(FakeOCRProvider(), normalized_png())
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    assert decode_normalized_png(normalized_png()).mode == "RGB"
    assert "Sinh viên K26" in encoded.decode("utf-8")
    assert payload["engine"] == "paddleocr"


def test_sidecar_body_limit_is_bounded():
    assert MAX_OCR_BODY_BYTES == 20 * 1024 * 1024


def test_sidecar_health_payload_identifies_only_the_ready_local_engine():
    assert health_payload(FakeOCRProvider()) == {"status": "ok", "engine": "paddleocr"}


def test_sidecar_protocol_handles_success_and_bounded_rejections():
    image = normalized_png()

    status, payload = handle_ocr_request(FakeOCRProvider(), "image/png", str(len(image)), image)
    assert status == 200
    assert payload["text"] == "Sinh viên K26"

    status, payload = handle_ocr_request(FakeOCRProvider(), "image/png", None, b"")
    assert status == 411
    assert payload["code"] == "INVALID_IMAGE"

    status, payload = handle_ocr_request(FakeOCRProvider(), "image/png", str(MAX_OCR_BODY_BYTES + 1), b"")
    assert status == 413
    assert payload["code"] == "IMAGE_TOO_LARGE"
