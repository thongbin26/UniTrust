from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_verification_service
from app.api.routes.verify import router
from app.core.config import settings
from app.models.obligation import ActionType, ActionValue, DeadlineValue, StudentObligation, TemporalPrecision
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.base import RetrievalChunk, RetrievalResult
from app.retrieval.chunking import build_corpus
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.temporal.models import TemporalValidity
from app.verification.abstention import AbstentionPolicy
from app.verification.decomposer import ClaimDecomposer
from app.verification.repository import OfficialStructuredRepository
from app.verification.service import VerificationService
from frontend.demo_cases import DEMO_CASES, get_demo_case, selected_demo_text
from frontend.verification_presentation import should_render_official_evidence


class StaticRetriever:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, top_k=5):
        self.calls.append((query, top_k))
        return self.results


class StaticReviewedRepository:
    def __init__(self, obligations):
        self.obligations = obligations

    def get_reviewed_official_obligations(self, notice_id, version_id):
        return self.obligations


def _reviewed_result(notice_id=13, version_id=13):
    chunk = RetrievalChunk(
        chunk_id=f"demo-{notice_id}-{version_id}",
        notice_id=notice_id,
        version_id=version_id,
        source_id="dut_it_faculty",
        start_char=0,
        end_char=120,
        text="Nộp ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.",
        title="Thông báo nguồn chính thức đã xem xét",
        canonical_url=f"https://dut.udn.vn/Thongbao/id/{notice_id}",
        is_latest_version=True,
    )
    return RetrievalResult(chunk=chunk, rank=1, score=1.0, retrieval_method="static")


def _reviewed_obligation():
    return StudentObligation(
        obligation_id="demo-reviewed-13-13",
        action=ActionValue(action_type=ActionType.SUBMIT, text="nộp"),
        deadline=DeadlineValue(
            raw_text="trước 16h00 ngày 26/06/2026",
            normalized="2026-06-26",
            precision=TemporalPrecision.DATE,
        ),
    )


def _reviewed_registration_obligation():
    return StudentObligation(
        obligation_id="demo-reviewed-17-17-o1",
        action=ActionValue(action_type=ActionType.REGISTER, text="đăng ký tham gia VEDC 2026"),
        deadline=DeadlineValue(
            raw_text="Hạn nộp hồ sơ: 30/06/2026",
            normalized="2026-06-30",
            precision=TemporalPrecision.DATE,
        ),
    )


def _service(results, obligations):
    service = VerificationService(
        StaticRetriever(results),
        ClaimDecomposer(),
        StaticReviewedRepository(obligations),
        AbstentionPolicy(),
    )
    service.temporal_resolver.resolve_validity = lambda *_: TemporalValidity.CURRENT
    return service


def _verify_api(service, text):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_verification_service] = lambda: service
    with TestClient(app) as client:
        response = client.post("/verify", json={"text": text, "top_k": 5})
    assert response.status_code == 200
    return response.json()["results"]


def test_guided_demo_cases_are_selection_only_and_preserve_fixture_metadata():
    assert [case["case_id"] for case in DEMO_CASES] == [
        "case_a_supported",
        "case_b_conflict",
        "case_c_unsupported",
    ]
    for case in DEMO_CASES:
        assert selected_demo_text(case["case_id"]) == case["claim_text"]
        selected = get_demo_case(case["case_id"])
        assert selected["is_synthetic"] is case["is_synthetic"]
        assert selected["source_notice_id"] == case["source_notice_id"]
        assert "verdict" not in selected
        assert "primary_provenance" not in selected
        assert "field_results" not in selected
    assert selected_demo_text(None) == ""


def test_case_a_uses_normal_verify_path_and_renders_applicable_evidence():
    case = get_demo_case("case_a_supported")
    service = _service([_reviewed_result()], [_reviewed_obligation()])

    results = _verify_api(service, selected_demo_text(case["case_id"]))
    result = next(item for item in results if item["verdict"] == "VERIFIED")

    assert len(service.retriever.calls) == len(results)
    assert all(top_k == 5 for _, top_k in service.retriever.calls)
    assert result["verdict"] == "VERIFIED"
    assert result["primary_provenance"]["notice_id"] == 13
    assert result["primary_provenance"]["version_id"] == 13
    assert should_render_official_evidence(result)


def test_case_b_uses_normal_verify_path_and_shows_authoritative_deadline_conflict():
    case = get_demo_case("case_b_conflict")
    service = _service([_reviewed_result(17, 17)], [_reviewed_registration_obligation()])

    results = _verify_api(service, selected_demo_text(case["case_id"]))
    result = next(item for item in results if item["verdict"] == "CONFLICT")

    assert len(service.retriever.calls) == len(results)
    assert all(top_k == 5 for _, top_k in service.retriever.calls)
    assert result["verdict"] == "CONFLICT"
    assert result["field_results"]["deadline"]["state"] == "CONFLICT"
    assert result["field_results"]["deadline"]["claimed_text"] == "01/07/2026"
    assert result["field_results"]["deadline"]["official_text"] == "Hạn nộp hồ sơ: 30/06/2026"
    assert should_render_official_evidence(result)


def test_case_b_uses_real_retrieval_and_reviewed_evidence_without_ambiguity(isolated_runtime_artifacts):
    """The controlled deadline mutation must survive the ordinary production path.

    This deliberately uses the real corpus, hybrid retriever, canonical mapping,
    reviewed repository, and temporal resolver.  It does not relax the
    ambiguity guard or substitute an injected evidence source.
    """
    case = get_demo_case("case_b_conflict")
    chunks = build_corpus()
    bm25 = BM25Retriever()
    dense = DenseRetriever(cache_dir=settings.retrieval_cache_dir, local_files_only=True)
    retriever = HybridRetriever([bm25, dense])
    retriever.index(chunks)
    repository = OfficialStructuredRepository()
    service = VerificationService(
        retriever,
        ClaimDecomposer(),
        repository,
        AbstentionPolicy(),
    )

    retrieved = retriever.search(case["claim_text"], top_k=5)
    assert (retrieved[0].chunk.notice_id, retrieved[0].chunk.version_id) == (17, 17)
    obligations = repository.get_reviewed_official_obligations(17, 17)
    assert [obligation.obligation_id for obligation in obligations] == ["o1"]

    results = service.verify(case["claim_text"], top_k=5)
    assert len(results) == 1
    result = results[0]

    assert result.abstention_reason is None
    assert result.temporal_status == TemporalValidity.CURRENT
    assert result.primary_provenance is not None
    assert (result.primary_provenance.notice_id, result.primary_provenance.version_id) == (17, 17)
    assert result.field_results["deadline"].state.value == "CONFLICT"
    assert result.field_results["deadline"].claimed_text == "01/07/2026"
    assert result.field_results["deadline"].official_text == "Hạn nộp hồ sơ: 30/06/2026"
    assert result.verdict.value == "CONFLICT"
    assert should_render_official_evidence(result.model_dump(mode="json"))


def test_case_c_uses_normal_verify_path_and_suppresses_authoritative_evidence():
    case = get_demo_case("case_c_unsupported")
    service = _service([], [])

    results = _verify_api(service, selected_demo_text(case["case_id"]))
    assert len(results) == 1
    result = results[0]

    assert service.retriever.calls == [(case["claim_text"], 5)]
    assert result["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert result["primary_provenance"] is None
    assert not should_render_official_evidence(result)
