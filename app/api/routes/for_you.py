from fastapi import APIRouter, Depends
import sqlite3

from app.api.schemas import StudentProfile, ForYouResponse, ForYouObligationItem, ObligationApplicability
from app.api.deps import get_db_connection, get_structured_repository
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
        
    missing_dimensions = []
    mismatched_dimensions = []
    dimensions = (
        ("faculty", profile.faculty, aud.faculties),
        ("major", profile.major, aud.majors),
        ("cohort", profile.cohort, aud.cohorts),
        ("program", profile.program, aud.programs),
    )
    for name, profile_value, required_values in dimensions:
        if not required_values:
            continue
        if profile_value is None:
            missing_dimensions.append(name)
        elif profile_value not in required_values:
            mismatched_dimensions.append(name)

    # A known mismatch is sufficient even when another dimension is unknown.
    if mismatched_dimensions:
        return ObligationApplicability(
            status="DOES_NOT_APPLY",
            explanation=f"Profile does not match: {', '.join(mismatched_dimensions)}",
        )
    if missing_dimensions:
        return ObligationApplicability(
            status="UNKNOWN",
            explanation=f"Profile is missing: {', '.join(missing_dimensions)}",
        )

    return ObligationApplicability(status="APPLIES", explanation="Profile explicitly matches all required dimensions")

@router.post("", response_model=ForYouResponse)
def get_for_you(
    profile: StudentProfile,
    repo: OfficialStructuredRepository = Depends(get_structured_repository),
    conn: sqlite3.Connection = Depends(get_db_connection),
):
    obligations_out = []
    temp_resolver = TemporalResolver()
    notice_ids = sorted({notice_id for notice_id, _ in repo.cache})
    canonical_urls = {}
    if notice_ids:
        placeholders = ",".join("?" for _ in notice_ids)
        rows = conn.execute(
            f"SELECT notice_id, canonical_url FROM notices WHERE notice_id IN ({placeholders})",
            notice_ids,
        ).fetchall()
        canonical_urls = {row["notice_id"]: row["canonical_url"] for row in rows}
    
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
                canonical_url=canonical_urls.get(notice_id),
            ))
            
    # Sort by deadline availability (those with deadlines first), then by APPLIES first
    # For now, just sort by APPLIES first.
    def sort_key(item: ForYouObligationItem):
        app_score = 0 if item.applicability.status == "APPLIES" else 1
        deadline_score = 0 if item.deadline else 1
        return (app_score, deadline_score)
        
    obligations_out.sort(key=sort_key)
    
    return ForYouResponse(obligations=obligations_out)
