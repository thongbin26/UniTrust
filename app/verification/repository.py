import json
from pathlib import Path
from typing import List

from app.models.obligation import AnnotationStatus, CanonicalNoticeAnnotation, StudentObligation
from app.verification.draft_lifecycle import ObligationDraftRecord

class OfficialStructuredRepository:
    def __init__(
        self,
        annotations_dir: str = "data/annotations/batch_001",
        promotion_dir: str | None = None,
    ):
        self.annotations_dir = annotations_dir
        self.promotion_dir = promotion_dir
        self.cache: dict[tuple[int, int], CanonicalNoticeAnnotation] = {}
        self._load_reviewed_annotations()
        self._load_promoted_drafts()

    def _load_reviewed_annotations(self):
        # Load all reviewed JSON files
        p = Path(self.annotations_dir)
        if not p.exists():
            return
            
        for fpath in p.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    annotation = CanonicalNoticeAnnotation(**data)
                    self.cache[(annotation.notice_id, annotation.version_id)] = annotation
            except Exception:
                pass

    def _load_promoted_drafts(self):
        """Load only explicitly promoted, version-bound lifecycle records.

        Existing accepted annotations win for a key.  This prevents a future
        promotion artifact from silently replacing established reviewed data.
        """
        if self.promotion_dir is None:
            return
        directory = Path(self.promotion_dir)
        if not directory.exists():
            return
        for path in directory.glob("*.json"):
            try:
                record = ObligationDraftRecord.model_validate_json(path.read_text(encoding="utf-8"))
                annotation = record.as_reviewed_annotation()
                if annotation is not None:
                    self.cache.setdefault((annotation.notice_id, annotation.version_id), annotation)
            except Exception:
                # A malformed or unreviewed draft must never become evidence.
                continue

    def get_official_obligations(self, notice_id: int, version_id: int) -> List[StudentObligation]:
        """
        1. Human-reviewed canonical annotation
        2. Machine extracted (not implemented)
        3. Returns empty list if missing.
        """
        annotation = self.cache.get((notice_id, version_id))
        if annotation:
            return annotation.obligations
        return []

    def get_reviewed_official_obligations(
        self,
        notice_id: int,
        version_id: int,
    ) -> List[StudentObligation]:
        """Return only human-reviewed or gold structured evidence."""
        annotation = self.cache.get((notice_id, version_id))
        if annotation and annotation.annotation_status in {
            AnnotationStatus.REVIEWED,
            AnnotationStatus.GOLD,
        }:
            return annotation.obligations
        return []
