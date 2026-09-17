import json
import glob
from pathlib import Path
from typing import Optional, List
from app.models.obligation import CanonicalNoticeAnnotation, StudentObligation

class OfficialStructuredRepository:
    def __init__(self, annotations_dir: str = "data/annotations/batch_001"):
        self.annotations_dir = annotations_dir
        self.cache: dict[tuple[int, int], CanonicalNoticeAnnotation] = {}
        self._load_reviewed_annotations()

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
