"""Generate the controlled synthetic OCR fixture used by the Case B demo.

This image is deliberately not an official DUT notice, a student message, or
production OCR gold. It is a stable, locally generated presentation fixture.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests/fixtures/ocr/demo_case_b_conflict.png"
FONT_PATH = Path(r"C:\Windows\Fonts\segoeui.ttf")
WIDTH = 1600
HEIGHT = 720
LABEL = "Tình huống mô phỏng"
MESSAGE = "Sinh viên đăng ký tham gia VEDC 2026 trước ngày 01/07/2026."


def build_fixture() -> Path:
    """Write a high-contrast, controlled screenshot-style message card."""
    if not FONT_PATH.is_file():
        raise SystemExit(f"Required local Vietnamese-capable font is unavailable: {FONT_PATH}")

    image = Image.new("RGB", (WIDTH, HEIGHT), "#eef4fb")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((80, 72, WIDTH - 80, HEIGHT - 72), radius=34, fill="white", outline="#c8d8ea", width=3)

    label_font = ImageFont.truetype(str(FONT_PATH), 42)
    message_font = ImageFont.truetype(str(FONT_PATH), 50)
    draw.text((150, 145), LABEL, font=label_font, fill="#175ea8")
    draw.line((150, 220, WIDTH - 150, 220), fill="#d7e3f0", width=3)
    draw.text((150, 315), MESSAGE, font=message_font, fill="#102a43")

    metadata = PngInfo()
    metadata.add_text("fixture_provenance", "CONTROLLED_SYNTHETIC_DEMO_FIXTURE")
    metadata.add_text("source", "accepted Case B demo text; controlled synthetic presentation content")
    metadata.add_text("visible_label", LABEL)
    metadata.add_text("visible_message", MESSAGE)
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(FIXTURE_PATH, format="PNG", pnginfo=metadata, optimize=False)
    return FIXTURE_PATH


if __name__ == "__main__":
    print(build_fixture())
