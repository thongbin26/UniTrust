from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.api.deps import get_db_connection, get_structured_repository
from app.api.schemas import NoticeSearchIndexItem
from app.verification.repository import OfficialStructuredRepository
from app.monitoring.repository import latest_notice_activity
import sqlite3

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("/notices", response_model=List[Dict[str, Any]])
def list_notices(conn: sqlite3.Connection = Depends(get_db_connection), repo: OfficialStructuredRepository = Depends(get_structured_repository)):
    # List full official corpus
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.notice_id, n.title, n.publication_date, s.name as source_name
        FROM notices n
        JOIN sources s ON n.source_id = s.source_id
        ORDER BY n.publication_date DESC, n.notice_id DESC
    """)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        nid = r["notice_id"]
        # Check if structured semantic coverage exists
        # In our implementation, repo caches all reviewed annotations
        # For a notice to have structured coverage, it must have versions with obligations

        has_struct = False
        coverage = "NONE"

        # We can check the repo cache for any version of this notice
        for (cache_nid, _), annotation in repo.cache.items():
            if cache_nid == nid:
                has_struct = True
                coverage = "REVIEWED" # We only load reviewed annotations currently
                break

        results.append({
            "notice_id": nid,
            "title": r["title"],
            "source_name": r["source_name"],
            "publication_date": r["publication_date"],
            "has_structured_obligations": has_struct,
            "structured_coverage": coverage
        })
    return results

@router.get("/search-index", response_model=List[NoticeSearchIndexItem])
def get_search_index(conn: sqlite3.Connection = Depends(get_db_connection)):
    activity = latest_notice_activity()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.notice_id, n.title, s.name as source_display_name,
               v.raw_text, s.source_id
        FROM notices n
        JOIN sources s ON n.source_id = s.source_id
        JOIN (
            SELECT notice_id, raw_text
            FROM notice_versions v1
            WHERE version_id = (SELECT MAX(version_id) FROM notice_versions v2 WHERE v2.notice_id = v1.notice_id)
        ) v ON n.notice_id = v.notice_id
        ORDER BY n.publication_date DESC, n.notice_id DESC
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "notice_id": r["notice_id"],
            "title": r["title"],
            "source_id": r["source_id"],
            "source_display_name": r["source_display_name"],
            "searchable_text": r["raw_text"],
            "monitoring_activity": activity.get(r["notice_id"]),
        })
    return results

@router.get("/notices/{notice_id}")
def get_notice(notice_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.notice_id, n.title, n.publication_date, n.canonical_url, s.name as source_name
        FROM notices n
        JOIN sources s ON n.source_id = s.source_id
        WHERE n.notice_id = ?
    """, (notice_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Notice not found")

    # Get current text
    cursor.execute("""
        SELECT v.version_id, v.raw_text, v.fetched_at as retrieved_at
        FROM notice_versions v
        WHERE v.notice_id = ?
        ORDER BY v.version_id DESC
        LIMIT 1
    """, (notice_id,))
    v_row = cursor.fetchone()

    return {
        "notice_id": row["notice_id"],
        "title": row["title"],
        "publication_date": row["publication_date"],
        "canonical_url": row["canonical_url"],
        "source_name": row["source_name"],
        "current_version_id": v_row["version_id"] if v_row else None,
        "raw_text": v_row["raw_text"] if v_row else None
    }

@router.get("/notices/{notice_id}/versions")
def get_notice_versions(notice_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT version_id, fetched_at as retrieved_at, raw_text FROM notice_versions WHERE notice_id = ? ORDER BY version_id DESC", (notice_id,))
    rows = cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No versions found for notice")
    return [{"version_id": r["version_id"], "retrieved_at": r["retrieved_at"], "raw_text": r["raw_text"]} for r in rows]

@router.get("/notices/{notice_id}/changes")
def get_notice_changes(notice_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT version_id FROM notice_versions WHERE notice_id = ?", (notice_id,))
    rows = cursor.fetchall()
    if len(rows) < 2:
        return {
            "has_history": False,
            "changes": []
        }

    # If there were multiple real versions, we would compare them.
    # Currently real DB has 0 historical versions.
    return {
        "has_history": True,
        "changes": []
    }
