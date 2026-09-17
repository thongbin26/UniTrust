import re
from typing import List, Optional
import uuid
from app.verification.models import DecomposedUserClaim, TypedUserField

class ClaimDecomposer:
    def __init__(self, use_llm_fallback: bool = False):
        self.use_llm_fallback = use_llm_fallback

    def decompose(self, text: str) -> List[DecomposedUserClaim]:
        # Basic deterministic segmenter
        claims = []
        # Split by . followed by space, or !, or ? or newline
        sentences = [s.strip() for s in re.split(r'(?:\.\s+|[!?\n]+)', text) if s.strip()]
        
        offset = 0
        for sentence in sentences:
            start_char = text.find(sentence, offset)
            end_char = start_char + len(sentence)
            offset = end_char
            
            claim = DecomposedUserClaim(
                claim_id=str(uuid.uuid4()),
                raw_claim_text=sentence,
                start_char=start_char,
                end_char=end_char
            )
            
            # Very simple deterministic extraction for tests
            # Action
            action_match = re.search(r'\b(nộp|đăng ký|đóng|tham gia|nhận)\b', sentence.lower())
            if action_match:
                m_start = start_char + action_match.start()
                m_end = start_char + action_match.end()
                claim.action = TypedUserField(text=action_match.group(1), start_char=m_start, end_char=m_end)

            # Deadline (e.g. 25/09/2026 or ISO)
            date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', sentence)
            if date_match:
                m_start = start_char + date_match.start()
                m_end = start_char + date_match.end()
                claim.deadline = TypedUserField(text=date_match.group(1), start_char=m_start, end_char=m_end)

            # Amount (e.g. 1.000.000 or 1000000)
            amount_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*|\d+)\s*(?:vnd|vnđ|đồng)\b', sentence.lower())
            if amount_match:
                m_start = start_char + amount_match.start(1)
                m_end = start_char + amount_match.end(1)
                claim.amount = TypedUserField(text=amount_match.group(1), start_char=m_start, end_char=m_end)

            claims.append(claim)

        # If LLM fallback is requested, we could invoke Qwen3 4B here.
        # Keeping it decoupled.
        if self.use_llm_fallback:
            try:
                from app.extraction.providers.factory import get_provider
                provider = get_provider("ollama")
                # ... would call provider.generate_json(...) here.
            except Exception:
                pass # Fail gracefully without crashing

        return claims
