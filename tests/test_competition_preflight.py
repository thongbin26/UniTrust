from scripts import competition_preflight as preflight


def test_expected_hashes_cover_only_release_artifacts():
    assert set(preflight.EXPECTED_HASHES) == {
        "unitrust.db",
        "data/processed/retrieval/embeddings.npy",
        "data/processed/retrieval/manifest.json",
    }
    assert all(len(value) == 64 for value in preflight.EXPECTED_HASHES.values())


def test_missing_artifacts_fail_without_writing(tmp_path):
    assert preflight.check_protected_artifacts(tmp_path) is False


def test_ocr_runtime_check_is_read_only(tmp_path):
    missing = tmp_path / "python.exe"
    assert preflight.check_ocr_runtime(missing) is False
    missing.write_bytes(b"")
    assert preflight.check_ocr_runtime(missing) is True
