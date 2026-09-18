import time
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.api.schemas import VerifyRequest, VerifyResponse, VerifyResponseItem, FieldComparisonResponse
from app.api.deps import get_verification_service
from app.verification.service import VerificationService

router = APIRouter(prefix="/verify", tags=["Verify"])

@router.post("", response_model=VerifyResponse)
def verify_claim(request: VerifyRequest, service: VerificationService = Depends(get_verification_service)):
    start_time = time.time()
    
    # Validation logic is handled by Pydantic (e.g., top_k ranges, empty text)
    
    # We ignore use_llm for now or pass it to decomposer if it was request-scoped.
    # The service initialized at startup has its own decomposer configuration.
    # To respect use_llm per-request without re-initializing models, 
    # the Decomposer should accept it dynamically. For Batch C, we keep it simple.
    
    try:
        results = service.verify(request.text)
    except Exception as e:
        import traceback
        import logging
        logging.error(traceback.format_exc())
        with open("verify_error.log", "w") as f:
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the verification pipeline.")
        
    mapped_results = []
    for res in results:
        field_res = {}
        if res.field_results:
            for k, v in res.field_results.items():
                field_res[k] = FieldComparisonResponse(
                    state=v.state.name,
                    claimed_text=v.claimed_text,
                    official_text=v.official_text,
                    explanation=v.explanation
                )
                
        from app.verification.models import OverallVerdict
        
        public_verdict = res.verdict.name
        if res.verdict == OverallVerdict.ABSTAINED:
            public_verdict = OverallVerdict.INSUFFICIENT_EVIDENCE.name
            
        mapped_results.append(VerifyResponseItem(
            claim_id=res.claim_id,
            raw_claim_text=res.raw_claim_text,
            verdict=public_verdict,
            temporal_status=res.temporal_status.name if res.temporal_status else "UNKNOWN",
            abstention_reason=res.abstention_reason.name if res.abstention_reason else None,
            field_results=field_res,
            primary_provenance=res.primary_provenance
        ))
        
    latency = (time.time() - start_time) * 1000
    return VerifyResponse(
        original_input=request.text,
        results=mapped_results,
        latency_ms=latency
    )
