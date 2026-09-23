from __future__ import annotations

from io import BytesIO
import json
import os
from urllib.parse import urlparse

import httpx

from app.ocr.models import OCRProcessingError, OCRResult


DEFAULT_SIDECAR_URL = "http://127.0.0.1:8765"
SIDECAR_URL_ENV = "UNITRUST_OCR_SIDECAR_URL"
SIDECAR_TIMEOUT_SECONDS = 60.0
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


class LocalOCRSidecarProvider:
    """Send already-sanitized RGB images to the local, isolated OCR runtime."""

    def __init__(self, sidecar_url: str | None = None, timeout_seconds: float = SIDECAR_TIMEOUT_SECONDS):
        self.sidecar_url = (sidecar_url or os.getenv(SIDECAR_URL_ENV) or DEFAULT_SIDECAR_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._validate_loopback_url()

    def _validate_loopback_url(self) -> None:
        parsed = urlparse(self.sidecar_url)
        if parsed.scheme != "http" or parsed.hostname not in _LOOPBACK_HOSTS:
            raise OCRProcessingError(
                "OCR_UNAVAILABLE",
                "OCR sidecar must use a local loopback HTTP address.",
            )

    @staticmethod
    def _serialize_png(image) -> bytes:
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _parse_response(payload: object) -> OCRResult:
        if not isinstance(payload, dict):
            raise ValueError("OCR sidecar response is not an object.")
        text = payload.get("text")
        engine = payload.get("engine")
        warnings = payload.get("warnings", [])
        confidence = payload.get("mean_confidence")
        if not isinstance(text, str) or not isinstance(engine, str):
            raise ValueError("OCR sidecar response has invalid text or engine.")
        if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
            raise ValueError("OCR sidecar response has invalid warnings.")
        if confidence is not None:
            if isinstance(confidence, bool):
                raise ValueError("OCR sidecar response has invalid confidence.")
            confidence = float(confidence)
        return OCRResult(text=text, engine=engine, warnings=warnings, mean_confidence=confidence)

    def extract_text(self, image) -> OCRResult:
        try:
            response = httpx.post(
                f"{self.sidecar_url}/ocr",
                content=self._serialize_png(image),
                headers={"Content-Type": "image/png"},
                timeout=self.timeout_seconds,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as exc:
            raise OCRProcessingError("OCR_UNAVAILABLE", "Local OCR sidecar is unavailable.") from exc
        except httpx.HTTPError as exc:
            raise OCRProcessingError("OCR_UNAVAILABLE", "Local OCR sidecar is unavailable.") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise OCRProcessingError("OCR_FAILED", "Local OCR sidecar could not process the image.")
        try:
            return self._parse_response(response.json())
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise OCRProcessingError("OCR_FAILED", "Local OCR sidecar returned an invalid response.") from exc
