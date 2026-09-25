import hashlib
from pathlib import Path

from evaluation.ai_generalization_v1 import build_pack, run_evaluation


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "evaluation" / "ai_generalization_v1"
QUALIFICATION = ROOT / "evaluation" / "v22a_ai_qualification" / "dataset_draft.jsonl"
QUALIFICATION_POLICY = ROOT / "evaluation" / "v22a_ai_qualification" / "QUALIFICATION_POLICY.md"


def test_pack_strictly_separates_reviewed_gold_from_candidates():
    records = run_evaluation.load_jsonl(PACK / "dataset.jsonl")
    accepted = run_evaluation.accepted_records(records)
    assert len(records) == 49
    assert len(accepted) == 18
    assert all(record["gold_provenance"] == "REUSED_REVIEWED_ANNOTATION" for record in accepted)
    assert all(record["gold_claim"] is not None for record in accepted)
    assert all(record["gold_claim"] is None for record in records if record["review_status"] == "CANDIDATE_UNREVIEWED")


def test_builder_is_reproducible_and_does_not_touch_qualification_dataset(tmp_path):
    before = hashlib.sha256(QUALIFICATION.read_bytes()).hexdigest()
    policy_before = hashlib.sha256(QUALIFICATION_POLICY.read_bytes()).hexdigest()
    records = build_pack.build_records(ROOT / "unitrust.db")
    build_pack.write_pack(records, tmp_path)
    rebuilt = run_evaluation.load_jsonl(tmp_path / "dataset.jsonl")
    assert rebuilt == records
    assert hashlib.sha256(QUALIFICATION.read_bytes()).hexdigest() == before
    assert hashlib.sha256(QUALIFICATION_POLICY.read_bytes()).hexdigest() == policy_before
    assert all(record["source"]["current_version_at_pack_generation"] for record in rebuilt)


def test_retrieval_metrics_rejects_stale_results_even_when_identity_matches():
    class Chunk:
        def __init__(self, latest):
            self.notice_id = 1
            self.version_id = 1
            self.is_latest_version = latest

    class Result:
        def __init__(self, latest):
            self.chunk = Chunk(latest)

    class StaleRetriever:
        def search_current(self, *_args, **_kwargs):
            return [Result(False)]

    record = {
        "record_id": "AGV1-X",
        "source_text": "nộp hồ sơ",
        "source": {"notice_id": 1, "version_id": 1},
        "gold_claim": {"action": {"text": "nộp", "action_type": "submit"}},
    }
    metrics, traces = run_evaluation.retrieval_metrics([record], StaleRetriever())
    assert metrics["stale_version_retrieval_violations"] == 1
    assert traces[0]["rank"] is None


def test_future_provider_contract_remains_offline_and_accepted_only():
    records = run_evaluation.load_jsonl(PACK / "dataset.jsonl")
    contract = run_evaluation.evaluate_provider_output(run_evaluation.accepted_records(records), {})
    assert contract["evaluation_population"] == "HUMAN_ACCEPTED_ONLY"
    assert contract["runtime_authorization"] == "NOT_GRANTED_BY_THIS_PACK"
