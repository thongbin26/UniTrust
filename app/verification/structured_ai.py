"""Provider-neutral optional structured extraction boundary.

No provider is enabled by V2.2A. Implementations must return validated claim
models and may never supply a verification verdict.
"""
from typing import Protocol

from app.verification.models import DecomposedUserClaim


class StructuredClaimExtractor(Protocol):
    def extract(self, text: str) -> list[DecomposedUserClaim]: ...


class OptionalAIExtractorUnavailable:
    """Offline-safe placeholder used until a real provider is configured."""

    def extract(self, text: str) -> list[DecomposedUserClaim]:
        raise RuntimeError("AI_UNAVAILABLE")


class HybridStructuredClaimExtractor:
    """Provider-neutral orchestration: deterministic output is always safe fallback."""
    def __init__(self, deterministic: StructuredClaimExtractor, optional_ai: StructuredClaimExtractor | None = None):
        self.deterministic = deterministic
        self.optional_ai = optional_ai

    def extract(self, text: str) -> list[DecomposedUserClaim]:
        claims = self.deterministic.extract(text)
        if self.optional_ai is None:
            return claims
        try:
            # Provider results are intentionally ignored until an explicit,
            # field-level merge policy is reviewed; they cannot override facts.
            self.optional_ai.extract(text)
        except Exception:
            pass
        return claims
