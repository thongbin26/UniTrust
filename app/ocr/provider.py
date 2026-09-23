from typing import Protocol, TYPE_CHECKING

from app.ocr.models import OCRResult

if TYPE_CHECKING:
    from PIL import Image


class OCRProvider(Protocol):
    def extract_text(self, image: "Image.Image") -> OCRResult:
        """Return ordered OCR text from an already validated in-memory image."""
