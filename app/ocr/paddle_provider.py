from __future__ import annotations

import json
import os
from pathlib import Path
import re
import unicodedata
from typing import Any

from app.ocr.models import OCRProcessingError, OCRResult


MODEL_ROOT_ENV = "UNITRUST_OCR_MODEL_ROOT"
DETECTION_MODEL = "PP-OCRv6_medium_det"
RECOGNITION_MODEL = "PP-OCRv6_medium_rec"


def normalize_ocr_text(text: str) -> str:
    """Perform only presentation-safe OCR cleanup; no semantic correction."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


class PaddleOCRProvider:
    engine_name = "paddleocr"

    def __init__(self, model_root: Path | None = None):
        configured_root = os.getenv(MODEL_ROOT_ENV)
        self.model_root = model_root or (
            Path(configured_root) if configured_root else Path.home() / ".paddlex" / "official_models"
        )
        self._engine: Any | None = None

    @property
    def detection_model_dir(self) -> Path:
        return self.model_root / DETECTION_MODEL

    @property
    def recognition_model_dir(self) -> Path:
        return self.model_root / RECOGNITION_MODEL

    def _build_engine(self) -> Any:
        if not self.detection_model_dir.is_dir() or not self.recognition_model_dir.is_dir():
            raise OCRProcessingError(
                "OCR_UNAVAILABLE",
                "OCR models are unavailable. Run scripts/prepare_ocr_models.py explicitly first.",
            )
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OCRProcessingError(
                "OCR_UNAVAILABLE",
                "Optional PaddleOCR runtime is not installed. Install requirements-ocr.txt first.",
            ) from exc
        return PaddleOCR(
            lang="vi",
            device="cpu",
            enable_mkldnn=False,
            cpu_threads=4,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_detection_model_dir=str(self.detection_model_dir),
            text_recognition_model_dir=str(self.recognition_model_dir),
        )

    @staticmethod
    def _payload(value: Any) -> Any:
        json_value = getattr(value, "json", value)
        if callable(json_value):
            json_value = json_value()
        if isinstance(json_value, str):
            json_value = json.loads(json_value)
        if isinstance(json_value, dict) and "res" in json_value:
            return json_value["res"]
        return json_value

    @classmethod
    def parse_results(cls, results: Any) -> OCRResult:
        texts: list[str] = []
        scores: list[float] = []
        iterable = results if isinstance(results, (list, tuple)) else [results]
        for result in iterable:
            payload = cls._payload(result)
            if not isinstance(payload, dict):
                raise ValueError("PaddleOCR result payload is not an object.")
            raw_texts = payload.get("rec_texts", [])
            raw_scores = payload.get("rec_scores", [])
            if not isinstance(raw_texts, list) or not isinstance(raw_scores, list):
                raise ValueError("PaddleOCR result payload has invalid recognition fields.")
            for index, raw_text in enumerate(raw_texts):
                if not isinstance(raw_text, str) or not raw_text.strip():
                    continue
                texts.append(raw_text)
                if index < len(raw_scores):
                    try:
                        scores.append(float(raw_scores[index]))
                    except (TypeError, ValueError):
                        pass
        return OCRResult(
            text=normalize_ocr_text("\n".join(texts)),
            engine=cls.engine_name,
            mean_confidence=(sum(scores) / len(scores)) if scores else None,
        )

    def extract_text(self, image) -> OCRResult:
        try:
            if self._engine is None:
                self._engine = self._build_engine()
            import numpy as np
            return self.parse_results(self._engine.predict(np.asarray(image)))
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError("OCR_FAILED", "The OCR engine could not process this image.") from exc
