from __future__ import annotations

from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_WIDTH = 4096
MAX_HEIGHT = 4096
MAX_PIXELS = 16_000_000
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_FORMATS = {"PNG", "JPEG", "WEBP"}


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def validate_image_bytes(data: bytes, filename: str | None) -> Image.Image:
    """Decode a small supported image without retaining upload metadata."""
    suffix = Path(filename or "").suffix.casefold()
    if suffix and suffix not in SUPPORTED_EXTENSIONS:
        raise ImageValidationError(
            "UNSUPPORTED_IMAGE_FORMAT",
            "Only PNG, JPEG, and WEBP screenshots are supported.",
            422,
        )
    if len(data) > MAX_UPLOAD_BYTES:
        raise ImageValidationError("IMAGE_TOO_LARGE", "Image upload exceeds 8 MiB.", 413)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                image_format = source.format
                source.load()
                if image_format not in SUPPORTED_FORMATS:
                    raise ImageValidationError(
                        "UNSUPPORTED_IMAGE_FORMAT",
                        "Only PNG, JPEG, and WEBP screenshots are supported.",
                        422,
                    )
                if source.width > MAX_WIDTH or source.height > MAX_HEIGHT:
                    raise ImageValidationError("IMAGE_TOO_LARGE", "Image dimensions exceed 4096 pixels.", 413)
                if source.width * source.height > MAX_PIXELS:
                    raise ImageValidationError("IMAGE_TOO_LARGE", "Image exceeds 16 megapixels.", 413)
                image = ImageOps.exif_transpose(source)
                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    background = Image.new("RGBA", image.size, "white")
                    background.alpha_composite(image.convert("RGBA"))
                    image = background.convert("RGB")
                else:
                    image = image.convert("RGB")
                return image.copy()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageValidationError("INVALID_IMAGE", "The uploaded file is not a valid image.", 422) from exc
