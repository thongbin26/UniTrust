from typing import List, Optional
from app.verification.claim_extractor import DeterministicTextClaimExtractor
from app.verification.models import DecomposedUserClaim

class ClaimDecomposer:
    def __init__(self, use_llm_fallback: bool = False):
        self.use_llm_fallback = use_llm_fallback
        self.extractor = DeterministicTextClaimExtractor()

    def decompose(self, text: str) -> List[DecomposedUserClaim]:
        claims = self.extractor.extract(text)

        # If LLM fallback is requested, we could invoke Qwen3 4B here.
        # Keeping it decoupled.
        if self.use_llm_fallback:
            try:
                # Step 18B deliberately keeps providers disconnected from Verify.
                # A future extractor may use the existing provider boundary.
                pass
            except Exception:
                pass # Fail gracefully without crashing

        return claims
