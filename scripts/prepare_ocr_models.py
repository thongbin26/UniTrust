"""Explicit preparation for the isolated OCR Python runtime; never run by the main app.

Run from the repository root as ``<isolated-python> -m scripts.prepare_ocr_models``.
"""

from app.ocr.paddle_provider import PaddleOCRProvider


def main() -> None:
    provider = PaddleOCRProvider()
    try:
        # This is intentionally the only supported path that may initialise
        # PaddleOCR before local model directories exist.
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise SystemExit("Install requirements-ocr.txt before preparing OCR models.") from exc

    engine = PaddleOCR(
        lang="vi",
        device="cpu",
        enable_mkldnn=False,
        cpu_threads=4,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    del engine
    required = [provider.detection_model_dir, provider.recognition_model_dir]
    missing = [str(path) for path in required if not path.is_dir()]
    if missing:
        raise SystemExit(f"OCR model preparation did not create required directories: {missing}")
    print("OCR models ready:")
    for path in required:
        print(path)


if __name__ == "__main__":
    main()
