from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_verification_service
from app.api.routes.verify import router
from app.models.obligation import (
    ActionType,
    ActionValue,
    AudienceCondition,
    DeadlineValue,
    MoneyValue,
    StudentObligation,
    TemporalPrecision,
    EvidenceBackedText,
)
from app.retrieval.base import RetrievalChunk, RetrievalResult
from app.verification.abstention import AbstentionPolicy
from app.verification.decomposer import ClaimDecomposer
from app.verification.repository import OfficialStructuredRepository
from app.verification.service import VerificationService


class RecordingRetriever:
    def __init__(self):
        self.calls = []
        self.chunk = RetrievalChunk(
            chunk_id="structured-test-chunk",
            notice_id=999_001,
            version_id=1,
            source_id="synthetic",
            start_char=0,
            end_char=100,
            text="Synthetic official obligation.",
            title="Synthetic notice",
            canonical_url="https://example.test/notice",
            is_latest_version=True,
        )

    def search(self, query: str, top_k: int = 5):
        self.calls.append((query, top_k))
        return [RetrievalResult(chunk=self.chunk, score=1.0, rank=1, retrieval_method="hybrid")]


class StructuredRepository(OfficialStructuredRepository):
    def __init__(self):
        pass

    def get_official_obligations(self, notice_id: int, version_id: int):
        return [
            StudentObligation(
                obligation_id="structured-obligation",
                action=ActionValue(action_type=ActionType.PAY, text="Đóng học phí"),
                deadline=DeadlineValue(
                    raw_text="2026-09-30",
                    normalized="2026-09-30",
                    precision=TemporalPrecision.DATE,
                ),
                amount=MoneyValue(raw_text="450.000 đồng", value_vnd=450_000),
                audience=AudienceCondition(applies_to_all_students=True),
                location=EvidenceBackedText(text="Phòng Công tác Sinh viên"),
            )
        ]


def build_service():
    retriever = RecordingRetriever()
    service = VerificationService(
        retriever,
        ClaimDecomposer(),
        StructuredRepository(),
        AbstentionPolicy(),
    )
    return service, retriever


def assert_received_span(text, provenance, expected_text, expected_normalized):
    assert provenance.text == expected_text
    assert text[provenance.start_char:provenance.end_char] == expected_text
    assert provenance.normalized_value == expected_normalized
    assert provenance.extraction_method == "deterministic"


def test_service_uses_default_top_k_and_raw_claim_fallback():
    service, retriever = build_service()
    text = "Thông tin chưa thuộc mẫu trích xuất hiện tại"

    service.verify(text)

    assert retriever.calls == [(text, 5)]


def test_service_passes_top_k_and_returns_absolute_received_provenance():
    service, retriever = build_service()
    text = "Sinh viên K26 cần đóng học phí\ntrước ngày 30/09/2026\nvới mức 450k."

    result = service.verify(text, top_k=7)[0]

    assert retriever.calls == [(text, 7)]
    assert_received_span(text, result.field_results["action"].received_provenance, "đóng", "pay")
    assert_received_span(text, result.field_results["deadline"].received_provenance, "30/09/2026", "2026-09-30")
    assert_received_span(text, result.field_results["amount"].received_provenance, "450k", 450_000)
    assert result.field_results["amount"].claimed_text == "450k"


def test_api_forwards_top_k_and_preserves_additive_received_provenance():
    service, retriever = build_service()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_verification_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/verify",
            json={"text": "Sinh viên cần đóng học phí trước ngày 30/09/2026 với mức 450k.", "top_k": 3, "use_llm": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert retriever.calls == [(payload["original_input"], 3)]
    amount = payload["results"][0]["field_results"]["amount"]
    assert amount["claimed_text"] == "450k"
    assert_received_span(payload["original_input"], type("P", (), amount["received_provenance"])(), "450k", 450_000)


def test_audience_and_location_are_extracted_but_not_verdict_bearing():
    service, _ = build_service()
    text = "Sinh viên K26 cần đóng học phí tại Phòng CTSV trước ngày 30/09/2026 với mức 450k."

    result = service.verify(text)[0]

    assert "audience" not in result.field_results
    assert "location" not in result.field_results
    assert result.verdict.name == "VERIFIED"


def test_amount_conflict_remains_verdict_bearing():
    service, _ = build_service()
    result = service.verify("Sinh viên cần đóng học phí trước ngày 30/09/2026 với mức 650k.")[0]

    assert result.field_results["amount"].state.name == "CONFLICT"
    assert result.verdict.name == "CONFLICT"
