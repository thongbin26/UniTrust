from fastapi import APIRouter, Depends
from typing import List

from app.api.schemas import StudentProfile, ForYouResponse, ForYouObligationItem, ObligationApplicability
from app.api.deps import get_structured_repository
from app.verification.repository import OfficialStructuredRepository
from app.temporal.resolver import TemporalResolver
from app.models.obligation import StudentObligation

router = APIRouter(prefix="/for-you", tags=["For You"])

def evaluate_applicability(profile: StudentProfile, obligation: StudentObligation) -> ObligationApplicability:
    aud = obligation.audience
    if not aud:
        return ObligationApplicability(status="UNKNOWN", explanation="No audience information available")
        
    if aud.applies_to_all_students:
        return ObligationApplicability(status="APPLIES", explanation="Applies to all students")
        
    # If not applies to all, and no specific filters exist
    if not aud.faculties and not aud.cohorts and not aud.programs and not aud.majors:
        return ObligationApplicability(status="UNKNOWN", explanation="Ambiguous audience targets")
        
    # Check explicitly required dimensions. A dimension is required if its list is non-empty.
    # The profile must match ALL non-empty dimensions.
    
    # Track if we found any mismatch
    if aud.faculties:
        if not profile.faculty or profile.faculty not in aud.faculties:
            return ObligationApplicability(status="DOES_NOT_APPLY", explanation="Faculty mismatch or missing")
            
    if aud.majors:
        if not profile.major or profile.major not in aud.majors:
            return ObligationApplicability(status="DOES_NOT_APPLY", explanation="Major mismatch or missing")
            
    if aud.cohorts:
        if not profile.cohort or profile.cohort not in aud.cohorts:
            return ObligationApplicability(status="DOES_NOT_APPLY", explanation="Cohort mismatch or missing")
            
    if aud.programs:
        if not profile.program or profile.program not in aud.programs:
            return ObligationApplicability(status="DOES_NOT_APPLY", explanation="Program mismatch or missing")
            
    # If we haven't failed any explicit dimension, and there were explicit dimensions, it applies.
    return ObligationApplicability(status="APPLIES", explanation="Profile explicitly matches all required dimensions")

@router.post("", response_model=ForYouResponse)
def get_for_you(profile: StudentProfile, repo: OfficialStructuredRepository = Depends(get_structured_repository)):
    obligations_out = []
    temp_resolver = TemporalResolver()
    
    # We iterate over all known reviewed annotations
    for (notice_id, version_id), annotation in repo.cache.items():
        # Get temporal status for the notice
        temporal_validity = temp_resolver.resolve_validity(notice_id, version_id)
        
        for obs in annotation.obligations:
            applicability = evaluate_applicability(profile, obs)
            
            obligations_out.append(ForYouObligationItem(
                obligation_id=obs.obligation_id,
                action_text=obs.action.text if obs.action else "Unknown",
                deadline=obs.deadline.raw_text if obs.deadline else None,
                required_documents=[doc.text for doc in obs.required_documents],
                location=obs.location.text if obs.location else None,
                applicability=applicability,
                temporal_status=temporal_validity.name,
                notice_id=notice_id,
                version_id=version_id,
                title=annotation.title or f"Notice {notice_id}",
                canonical_url=None # Retrieve from DB if needed, but ForYou response can omit it or use None
            ))
            
    # Sort by deadline availability (those with deadlines first), then by APPLIES first
    # For now, just sort by APPLIES first.
    def sort_key(item: ForYouObligationItem):
        app_score = 0 if item.applicability.status == "APPLIES" else 1
        deadline_score = 0 if item.deadline else 1
        return (app_score, deadline_score)
        
    obligations_out.sort(key=sort_key)
    
    return ForYouResponse(obligations=obligations_out)
