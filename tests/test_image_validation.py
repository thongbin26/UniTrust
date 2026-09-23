from io import BytesIO

import pytest
from PIL import Image

from app.ocr.image_validation import (
    ImageValidationError,
    MAX_UPLOAD_BYTES,
    MAX_WIDTH,
    validate_image_bytes,
)


def encoded_image(image: Image.Image, image_format: str) -> bytes:
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


@pytest.mark.parametrize(
    ("image_format", "filename"),
    [("PNG", "notice.png"), ("JPEG", "notice.jpg"), ("WEBP", "notice.webp")],
)
def test_valid_supported_images_decode_to_rgb(image_format, filename):
    image = validate_image_bytes(encoded_image(Image.new("RGB", (16, 12), "white"), image_format), filename)

    assert image.mode == "RGB"
    assert image.size == (16, 12)


def test_invalid_bytes_are_rejected():
    with pytest.raises(ImageValidationError, match="valid image") as raised:
        validate_image_bytes(b"not an image", "notice.png")

    assert raised.value.code == "INVALID_IMAGE"


def test_actual_unsupported_decoded_format_is_rejected():
    gif = encoded_image(Image.new("RGB", (2, 2), "white"), "GIF")

    with pytest.raises(ImageValidationError) as raised:
        validate_image_bytes(gif, "notice.png")

    assert raised.value.code == "UNSUPPORTED_IMAGE_FORMAT"


def test_byte_limit_is_rejected_before_decode():
    with pytest.raises(ImageValidationError) as raised:
        validate_image_bytes(b"x" * (MAX_UPLOAD_BYTES + 1), "notice.png")

    assert raised.value.code == "IMAGE_TOO_LARGE"


def test_dimension_limit_is_rejected_without_allocating_a_large_payload(monkeypatch):
    class FakeSource:
        format = "PNG"
        width = MAX_WIDTH + 1
        height = 1

        def load(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr("app.ocr.image_validation.Image.open", lambda _: FakeSource())
    with pytest.raises(ImageValidationError) as raised:
        validate_image_bytes(b"small", "notice.png")

    assert raised.value.code == "IMAGE_TOO_LARGE"


def test_pixel_limit_is_rejected_without_allocating_a_large_payload(monkeypatch):
    class FakeSource:
        format = "PNG"
        width = 4000
        height = 4001

        def load(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr("app.ocr.image_validation.Image.open", lambda _: FakeSource())
    with pytest.raises(ImageValidationError) as raised:
        validate_image_bytes(b"small", "notice.png")

    assert raised.value.code == "IMAGE_TOO_LARGE"


def test_exif_orientation_is_normalized():
    source = Image.new("RGB", (10, 20), "white")
    source.getexif()[274] = 6
    output = BytesIO()
    source.save(output, format="JPEG", exif=source.getexif())

    image = validate_image_bytes(output.getvalue(), "notice.jpg")

    assert image.size == (20, 10)


def test_transparent_images_are_flattened_to_rgb():
    image = validate_image_bytes(
        encoded_image(Image.new("RGBA", (4, 4), (0, 0, 0, 0)), "PNG"),
        "notice.png",
    )

    assert image.mode == "RGB"
    assert image.getpixel((0, 0)) == (255, 255, 255)
