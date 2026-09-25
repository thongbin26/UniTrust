"""Static checks for the controlled, non-production Case B OCR fixture."""

from PIL import Image

from scripts.generate_demo_ocr_fixture import FIXTURE_PATH, LABEL, MESSAGE


def test_case_b_ocr_fixture_is_controlled_synthetic_message_card():
    """CONTROLLED_SYNTHETIC_DEMO_FIXTURE, never official or student content."""
    with Image.open(FIXTURE_PATH) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (1600, 720)
        assert image.info["fixture_provenance"] == "CONTROLLED_SYNTHETIC_DEMO_FIXTURE"
        assert image.info["visible_label"] == LABEL
        assert image.info["visible_message"] == MESSAGE
        assert "official" not in image.info["source"]
        assert "student" not in image.info["source"]
