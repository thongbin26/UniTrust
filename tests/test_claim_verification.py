from app.verification.decomposer import ClaimDecomposer

def test_decomposer_multiple_claims():
    decomposer = ClaimDecomposer()
    text = "Sinh viên phải nộp học phí trước ngày 20/09/2026. Số tiền là 1.000.000 VNĐ."
    claims = decomposer.decompose(text)

    assert len(claims) == 2
    assert claims[0].action.text == "nộp"
    assert claims[0].deadline.text == "20/09/2026"
    assert claims[0].raw_claim_text == "Sinh viên phải nộp học phí trước ngày 20/09/2026"

    assert claims[1].amount.text == "1.000.000"

    # Check offsets
    original_extracted_1 = text[claims[0].start_char:claims[0].end_char]
    assert original_extracted_1 == claims[0].raw_claim_text

    original_extracted_2 = text[claims[1].start_char:claims[1].end_char]
    assert original_extracted_2 == claims[1].raw_claim_text

def test_diagnostic_verified_synthetic_fixture():
    # SYNTHETIC DIAGNOSTIC FIXTURE
    # This example explicitly uses mocked in-memory official evidence
    # It does NOT read from unitrust.db or represent real DUT notices
    from app.verification.service import VerificationService
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.base import RetrievalChunk
    from app.verification.repository import OfficialStructuredRepository
    from app.verification.abstention import AbstentionPolicy
    from app.models.obligation import StudentObligation, ActionValue, ActionType, DeadlineValue, TemporalPrecision

    class MockRetriever(HybridRetriever):
        def search(self, query: str, top_k: int = 5):
            from app.retrieval.base import RetrievalResult
            chunk = RetrievalChunk(
                chunk_id="synthetic_chunk_1", notice_id=99999, version_id=1, source_id="synthetic_src",
                start_char=0, end_char=100, text="Nộp học phí trước 20/09/2026",
                title="Synthetic Notice", canonical_url="http://synthetic.local", is_latest_version=True
            )
            return [RetrievalResult(chunk=chunk, score=1.0, rank=1, retrieval_method="hybrid")]
    class MockRepo(OfficialStructuredRepository):
        def get_official_obligations(self, notice_id, version_id):
            return [StudentObligation(
                obligation_id="synthetic_obl_1",
                action=ActionValue(action_type=ActionType.PAY, text="Nộp học phí"),
                deadline=DeadlineValue(raw_text="2026-09-20", precision=TemporalPrecision.DATE)
            )]

    service = VerificationService(MockRetriever(None, None), ClaimDecomposer(), MockRepo(), AbstentionPolicy())
    results = service.verify("Sinh viên đóng học phí trước ngày 20/09/2026.")
    assert results[0].verdict.name == "VERIFIED"

def test_diagnostic_conflict_synthetic_fixture():
    # SYNTHETIC DIAGNOSTIC FIXTURE
    # This example explicitly uses mocked in-memory official evidence
    # It does NOT read from unitrust.db or represent real DUT notices
    from app.verification.service import VerificationService
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.base import RetrievalChunk
    from app.verification.repository import OfficialStructuredRepository
    from app.verification.abstention import AbstentionPolicy
    from app.models.obligation import StudentObligation, ActionValue, ActionType, DeadlineValue, TemporalPrecision

    class MockRetriever(HybridRetriever):
        def search(self, query: str, top_k: int = 5):
            from app.retrieval.base import RetrievalResult
            chunk = RetrievalChunk(
                chunk_id="synthetic_chunk_1", notice_id=99999, version_id=1, source_id="synthetic_src",
                start_char=0, end_char=100, text="Nộp học phí trước 20/09/2026",
                title="Synthetic Notice", canonical_url="http://synthetic.local", is_latest_version=True
            )
            return [RetrievalResult(chunk=chunk, score=1.0, rank=1, retrieval_method="hybrid")]
    class MockRepo(OfficialStructuredRepository):
        def get_official_obligations(self, notice_id, version_id):
            return [StudentObligation(
                obligation_id="synthetic_obl_1",
                action=ActionValue(action_type=ActionType.PAY, text="Nộp học phí"),
                deadline=DeadlineValue(raw_text="2026-09-20", precision=TemporalPrecision.DATE)
            )]

    service = VerificationService(MockRetriever(None, None), ClaimDecomposer(), MockRepo(), AbstentionPolicy())
    results = service.verify("Sinh viên đóng học phí trước ngày 25/09/2026.")
    assert results[0].verdict.name == "CONFLICT"
