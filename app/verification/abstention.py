from dataclasses import dataclass
from typing import Optional
from app.verification.models import AbstentionReason

@dataclass
class AbstentionConfig:
    enabled: bool = False
    min_score_threshold: Optional[float] = None # explicitly uncalibrated/disabled by default

class AbstentionPolicy:
    def __init__(self, config: AbstentionConfig = AbstentionConfig()):
        self.config = config

    def check_retrieval(self, chunks: list) -> Optional[AbstentionReason]:
        if not chunks:
            return AbstentionReason.NO_RETRIEVAL_EVIDENCE
        return None

    def check_official_obligation(self, obligations: list) -> Optional[AbstentionReason]:
        if not obligations:
            return AbstentionReason.NO_OFFICIAL_FIELD
        return None

    def check_thresholds(self, score: float) -> Optional[AbstentionReason]:
        if self.config.enabled and self.config.min_score_threshold is not None:
            if score < self.config.min_score_threshold:
                return AbstentionReason.INSUFFICIENT_FIELD_COVERAGE
        return None
