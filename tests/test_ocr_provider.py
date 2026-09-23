import json

import pytest

from app.ocr.models import OCRProcessingError
from app.ocr.paddle_provider import PaddleOCRProvider, normalize_ocr_text


class JsonPropertyResult:
    def __init__(self, payload):
        self.json = payload


class JsonMethodResult:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return json.dumps({"res": self._payload})


def test_provider_parses_ordered_vietnamese_lines_and_confidence():
    result = PaddleOCRProvider.parse_results(JsonPropertyResult({
        "rec_texts": ["THÔNG BÁO HỌC PHÍ", "Sinh viên K26 đóng học phí 450.000 đồng.", "Hạn cuối: 30/09/2026"],
        "rec_scores": [0.99, 1.0, 0.98],
    }))

    assert result.text == "THÔNG BÁO HỌC PHÍ\nSinh viên K26 đóng học phí 450.000 đồng.\nHạn cuối: 30/09/2026"
    assert result.mean_confidence == pytest.approx(0.99)


def test_provider_accepts_callable_json_and_missing_scores():
    result = PaddleOCRProvider.parse_results(JsonMethodResult({"rec_texts": ["Dòng một", "Dòng hai"], "rec_scores": []}))

    assert result.text == "Dòng một\nDòng hai"
    assert result.mean_confidence is None


def test_safe_text_normalization_preserves_vietnamese_unicode_and_newlines():
    text = "\r\nTHÔNG BÁO HỌC PHÍ\r\n\r\n\r\nSinh viên K26 đóng học phí 450.000 đồng.\rHạn cuối: 30/09/2026\r\n"

    assert normalize_ocr_text(text) == (
        "THÔNG BÁO HỌC PHÍ\n\nSinh viên K26 đóng học phí 450.000 đồng.\nHạn cuối: 30/09/2026"
    )


def test_provider_is_unavailable_without_local_models_before_importing_paddle(tmp_path):
    provider = PaddleOCRProvider(model_root=tmp_path)

    with pytest.raises(OCRProcessingError) as raised:
        provider._build_engine()

    assert raised.value.code == "OCR_UNAVAILABLE"


def test_malformed_paddle_payload_is_not_silently_transcribed():
    with pytest.raises(ValueError):
        PaddleOCRProvider.parse_results(JsonPropertyResult({"rec_texts": "not a list", "rec_scores": []}))
