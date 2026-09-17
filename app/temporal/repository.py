import sqlite3
from typing import List
from app.db.database import get_connection
from app.models.obligation import TemporalRelation, TemporalRelationType, MaterialField
import json

from pydantic import BaseModel

class ConfirmedTemporalRelation(BaseModel):
    relation: TemporalRelation
    is_confirmed: bool

def get_temporal_relations_for_target(target_notice_id: int, target_version_id: int | None = None) -> List[ConfirmedTemporalRelation]:
    query = """
        SELECT relation_type, target_notice_id, target_version_id, changed_fields_json, evidence_span_ids_json, note, provenance
        FROM temporal_relations
        WHERE target_notice_id = ?
    """
    params = [target_notice_id]
    
    if target_version_id is not None:
        query += " AND (target_version_id = ? OR target_version_id IS NULL)"
        params.append(target_version_id)
        
    relations = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            changed_fields = json.loads(row["changed_fields_json"])
            evidence_span_ids = json.loads(row["evidence_span_ids_json"])
            
            # ASSUMPTION (Temporal Confirmation Logic):
            # We treat the following provenance values as confirmed/evidence-backed:
            # - manual, reviewed, gold, human
            # Unreviewed ML inferences (e.g. inferred, qwen, candidate) are unconfirmed
            # and must NOT trigger a definitive SUPERSEDED_OUTDATED status (they resolve to UNKNOWN).
            prov = row["provenance"].lower()
            is_confirmed = prov in ("manual", "reviewed", "gold", "human")
            
            relations.append(ConfirmedTemporalRelation(
                relation=TemporalRelation(
                    relation_type=TemporalRelationType(row["relation_type"]),
                    target_notice_id=row["target_notice_id"],
                    target_version_id=row["target_version_id"],
                    changed_fields=[MaterialField(f) for f in changed_fields],
                    evidence_span_ids=evidence_span_ids,
                    note=row["note"]
                ),
                is_confirmed=is_confirmed
            ))
    return relations

def is_latest_version(notice_id: int, version_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT (nv.content_hash = n.current_content_hash) as is_latest
            FROM notice_versions nv
            JOIN notices n ON nv.notice_id = n.notice_id
            WHERE nv.notice_id = ? AND nv.version_id = ?
        """, (notice_id, version_id))
        row = cursor.fetchone()
        if row:
            return bool(row["is_latest"])
    return False
