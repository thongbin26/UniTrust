"""Run the isolated, loopback-only PaddleOCR sidecar explicitly."""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json

from PIL import Image, UnidentifiedImageError

from app.ocr.models import OCRProcessingError
from app.ocr.paddle_provider import PaddleOCRProvider


HOST = "127.0.0.1"
PORT = 8765
MAX_OCR_BODY_BYTES = 20 * 1024 * 1024


def decode_normalized_png(data: bytes):
    """Decode worker input in memory; original upload validation stays in the main API."""
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format != "PNG":
                raise ValueError("OCR sidecar accepts normalized PNG only.")
            source.load()
            return source.convert("RGB").copy()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("OCR sidecar received an invalid normalized PNG.") from exc


def ocr_payload(provider: PaddleOCRProvider, body: bytes) -> dict:
    result = provider.extract_text(decode_normalized_png(body))
    return result.model_dump()


def health_payload(provider: PaddleOCRProvider) -> dict:
    return {"status": "ok", "engine": provider.engine_name}


def handle_ocr_request(
    provider: PaddleOCRProvider,
    content_type: str,
    content_length: str | None,
    body: bytes,
) -> tuple[HTTPStatus, dict]:
    """Pure sidecar protocol handler, kept separate from the endless server loop."""
    if content_length is None:
        return HTTPStatus.LENGTH_REQUIRED, {"code": "INVALID_IMAGE", "message": "Content-Length is required."}
    try:
        length = int(content_length)
    except ValueError:
        return HTTPStatus.BAD_REQUEST, {"code": "INVALID_IMAGE", "message": "Invalid Content-Length."}
    if length < 0 or length > MAX_OCR_BODY_BYTES:
        return HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"code": "IMAGE_TOO_LARGE", "message": "Image exceeds sidecar limit."}
    if len(body) != length:
        return HTTPStatus.BAD_REQUEST, {"code": "INVALID_IMAGE", "message": "Invalid request body length."}
    if content_type != "image/png":
        return HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"code": "UNSUPPORTED_IMAGE_FORMAT", "message": "OCR sidecar accepts PNG only."}
    try:
        return HTTPStatus.OK, ocr_payload(provider, body)
    except ValueError:
        return HTTPStatus.UNPROCESSABLE_ENTITY, {"code": "INVALID_IMAGE", "message": "Invalid normalized PNG."}
    except OCRProcessingError as exc:
        return HTTPStatus.SERVICE_UNAVAILABLE, {"code": exc.code, "message": exc.message}
    except Exception:
        return HTTPStatus.SERVICE_UNAVAILABLE, {"code": "OCR_FAILED", "message": "OCR processing failed."}


def make_handler(provider: PaddleOCRProvider):
    class OCRSidecarHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args) -> None:
            """Do not log request payloads or image-derived text."""

        def _write_json(self, status: HTTPStatus, payload: dict) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(HTTPStatus.OK, health_payload(provider))
            else:
                self._write_json(HTTPStatus.NOT_FOUND, {"code": "NOT_FOUND", "message": "Not found."})

        def do_POST(self) -> None:
            if self.path != "/ocr":
                self._write_json(HTTPStatus.NOT_FOUND, {"code": "NOT_FOUND", "message": "Not found."})
                return
            content_length = self.headers.get("Content-Length")
            try:
                length = int(content_length) if content_length is not None else 0
            except ValueError:
                length = 0
            body = self.rfile.read(length) if content_length is not None and length >= 0 else b""
            status, payload = handle_ocr_request(
                provider,
                self.headers.get_content_type(),
                content_length,
                body,
            )
            self._write_json(status, payload)

    return OCRSidecarHandler


def build_ready_provider() -> PaddleOCRProvider:
    provider = PaddleOCRProvider()
    provider._engine = provider._build_engine()
    return provider


def main() -> None:
    try:
        provider = build_ready_provider()
    except OCRProcessingError as exc:
        raise SystemExit(f"OCR sidecar startup failed: {exc.message}") from exc
    server = ThreadingHTTPServer((HOST, PORT), make_handler(provider))
    print(f"OCR sidecar ready at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
