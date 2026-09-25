"""Provider-free safety tests for current evidence and draft promotion."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.obligation import ActionType, ActionValue, SourceReference, StudentObligation
from app.retrieval.base import RetrievalChunk, RetrievalResult, Retriever
from app.retrieval.hybrid import HybridRetriever
from app.temporal.models import TemporalValidity
from app.verification.abstention import AbstentionPolicy
from app.verification.decomposer import ClaimDecomposer
from app.verification.draft_lifecycle import (
    DraftLifecycleStatus,
    ExtractionProvenance,
    ObligationDraftRecord,
    ReviewerDecision,
)
from app.verification.repository import OfficialStructuredRepository
from app.verification.service import VerificationService


class FixedRankRetriever(Retriever):
    """Return an intentionally stale-first ranking to exercise the filter."""

    def __init__(self, results: list[RetrievalResult]):
        self.results = results

    def index(self, chunks):
        return None

    def search(self, query: str, top_k: int = 5):
        return self.results[:top_k]


def _chunk(version_id: int, *, latest: bool) -> RetrievalChunk:
    return RetrievalChunk(
        chunk_id=f"freshness-{version_id}",
        notice_id=980_001,
        version_id=version_id,
        source_id="synthetic-official",
        start_char=0,
        end_char=50,
        text=f"Official registration version {version_id}",
        title="Synthetic current evidence",
        canonical_url="https://dut.udn.vn/Thongbao/id/980001",
        is_latest_version=latest,
    )


def _draft(status: DraftLifecycleStatus, version_id: int, *, reviewer: bool = False) -> ObligationDraftRecord:
    decision = (
        ReviewerDecision(
            reviewer_id="reviewer-1",
            decided_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
            note="Synthetic fixture approval only.",
        )
        if reviewer
        else None
    )
    return ObligationDraftRecord(
        lifecycle_status=status,
        notice_id=980_001,
        version_id=version_id,
        source=SourceReference(source_id="synthetic-official", name="Synthetic official source"),
        title="Synthetic current evidence",
        raw_text="Sinh viên đăng ký.",
        observed_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
        canonical_url="https://dut.udn.vn/Thongbao/id/980001",
        content_hash=f"fixture-{version_id}",
        extraction=ExtractionProvenance(
            provider_id="fixture-provider",
            model_id="fixture-model",
            extracted_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
        ),
        reviewer_decision=decision,
        obligations=[
            StudentObligation(
                obligation_id=f"fixture-obligation-{version_id}",
                action=ActionValue(action_type=ActionType.REGISTER, text="đăng ký"),
            )
        ],
    )


def _write_record(directory, name: str, record: ObligationDraftRecord) -> None:
    directory.mkdir(exist_ok=True)
    (directory / name).write_text(record.model_dump_json(), encoding="utf-8")


def test_current_verification_view_excludes_stale_versions_but_generic_history_remains():
    historical = _chunk(1, latest=False)
    current = _chunk(2, latest=True)
    ranked = [
        RetrievalResult(chunk=historical, rank=1, score=1.0, retrieval_method="fixture"),
        RetrievalResult(chunk=current, rank=2, score=0.9, retrieval_method="fixture"),
    ]
    hybrid = HybridRetriever([FixedRankRetriever(ranked)])
    hybrid.index([historical, current])

    assert [item.chunk.version_id for item in hybrid.search("registration", top_k=2)] == [1, 2]
    current_results = hybrid.search_current("registration", top_k=1)
    assert [item.chunk.version_id for item in current_results] == [2]
    assert current_results[0].chunk.is_latest_version is True


def test_draft_rejected_and_stale_promotions_are_not_reviewed_evidence(tmp_path):
    draft_dir = tmp_path / "lifecycle"
    _write_record(draft_dir, "draft.json", _draft(DraftLifecycleStatus.DRAFT, 2))
    _write_record(draft_dir, "rejected.json", _draft(DraftLifecycleStatus.REJECTED, 3, reviewer=True))
    _write_record(draft_dir, "promoted-v1.json", _draft(DraftLifecycleStatus.PROMOTED, 1, reviewer=True))
    repository = OfficialStructuredRepository(annotations_dir=str(tmp_path / "accepted"), promotion_dir=str(draft_dir))

    assert repository.get_reviewed_official_obligations(980_001, 2) == []
    assert repository.get_reviewed_official_obligations(980_001, 3) == []
    assert len(repository.get_reviewed_official_obligations(980_001, 1)) == 1
    # A decision about version 1 cannot authorize later version 2.
    assert repository.get_reviewed_official_obligations(980_001, 2) == []


def test_promoted_current_version_can_flow_through_existing_verification_boundary(tmp_path, monkeypatch):
    draft_dir = tmp_path / "lifecycle"
    _write_record(draft_dir, "promoted-v2.json", _draft(DraftLifecycleStatus.PROMOTED, 2, reviewer=True))
    repository = OfficialStructuredRepository(annotations_dir=str(tmp_path / "accepted"), promotion_dir=str(draft_dir))
    historical = _chunk(1, latest=False)
    current = _chunk(2, latest=True)
    ranked = [
        RetrievalResult(chunk=historical, rank=1, score=1.0, retrieval_method="fixture"),
        RetrievalResult(chunk=current, rank=2, score=0.9, retrieval_method="fixture"),
    ]
    retriever = HybridRetriever([FixedRankRetriever(ranked)])
    retriever.index([historical, current])
    service = VerificationService(retriever, ClaimDecomposer(), repository, AbstentionPolicy())
    monkeypatch.setattr(service.temporal_resolver, "resolve_validity", lambda *_: TemporalValidity.CURRENT)

    result = service.verify("Sinh viên cần đăng ký.")[0]

    assert result.verdict.name == "VERIFIED"
    assert result.primary_provenance.version_id == 2
