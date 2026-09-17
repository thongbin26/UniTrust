import json
import uuid
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.obligation import CanonicalNoticeAnnotation

def build_deterministic_claim(audience, action, deadline, location, req_docs) -> tuple[str, list]:
    parts = []
    fields = []
    
    if audience and audience.raw_text:
        parts.append(audience.raw_text)
        fields.append("audience")
        
    if action and action.text:
        parts.append(action.text)
        fields.append("action")
        
    if deadline and deadline.raw_text:
        parts.append(deadline.raw_text)
        fields.append("deadline")
        
    if location and location.text:
        parts.append(f"tại {location.text}")
        fields.append("location")
        
    if req_docs:
        docs_text = " và ".join([doc.text for doc in req_docs])
        parts.append(docs_text)
        fields.append("required_documents")
        
    return " ".join(parts), fields

def apply_wrong_deadline(deadline_obj) -> str:
    # Use normalized date to add 4 days
    norm = deadline_obj.normalized
    # Try parsing datetime or date
    try:
        if "T" in norm:
            dt = datetime.fromisoformat(norm)
            mutated = dt + timedelta(days=4)
            time_part = mutated.strftime("%H:%M")
            date_part = mutated.strftime("%d/%m/%Y")
            return f"{time_part} ngày {date_part}"
        else:
            dt = datetime.strptime(norm, "%Y-%m-%d")
            mutated = dt + timedelta(days=4)
            date_part = mutated.strftime("%d/%m/%Y")
            return f"ngày {date_part}"
    except Exception:
        # Fallback if isoformat parsing fails (shouldn't)
        return "ngày 31/12/2099"

def apply_wrong_location(location_obj) -> str:
    return "Tầng 2 Thư viện mới"

def main():
    annotations_dir = Path("data/annotations/batch_001")
    out_dir = Path("data/benchmark/step13")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    controlled_cases = []
    source_derived_cases = []
    
    for file_path in sorted(annotations_dir.glob("*.json")):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            annotation = CanonicalNoticeAnnotation(**data)
            
            n_id = annotation.notice_id
            v_id = annotation.version_id
            
            for obl in annotation.obligations:
                o_id = obl.obligation_id
                
                # 1. EXACT_SUPPORTED
                exact_text, exact_fields = build_deterministic_claim(
                    obl.audience, obl.action, obl.deadline, obl.location, obl.required_documents
                )
                
                if exact_text.strip():
                    exact_case = {
                        "benchmark_case_id": f"n{n_id}_v{v_id}_{o_id}_exact",
                        "notice_id": n_id,
                        "version_id": v_id,
                        "obligation_id": o_id,
                        "claim_text": exact_text,
                        "claim_fields": exact_fields,
                        "expected_trust_state": "VERIFIED",
                        "mutation_type": "EXACT_SUPPORTED",
                        "mutated_field": None,
                        "original_value": None,
                        "mutated_value": None,
                        "synthetic": False,
                        "generation_rule": "concat_raw_fields"
                    }
                    controlled_cases.append(exact_case)
                    source_derived_cases.append(exact_case)
                    
                # 2. WRONG_DEADLINE
                if obl.deadline and obl.deadline.raw_text:
                    mutated_dl_text = apply_wrong_deadline(obl.deadline)
                    parts, fields = build_deterministic_claim(
                        obl.audience, obl.action, None, obl.location, obl.required_documents
                    )
                    mutated_claim = f"{parts} trước {mutated_dl_text}" if parts else f"trước {mutated_dl_text}"
                    fields.append("deadline")
                    
                    wd_case = {
                        "benchmark_case_id": f"n{n_id}_v{v_id}_{o_id}_wrong_deadline",
                        "notice_id": n_id,
                        "version_id": v_id,
                        "obligation_id": o_id,
                        "claim_text": mutated_claim,
                        "claim_fields": fields,
                        "expected_trust_state": "CONFLICT",
                        "mutation_type": "WRONG_DEADLINE",
                        "mutated_field": "deadline",
                        "original_value": obl.deadline.raw_text,
                        "mutated_value": mutated_dl_text,
                        "synthetic": True,
                        "generation_rule": "offset_+4_days"
                    }
                    controlled_cases.append(wd_case)
                    
                # 3. WRONG_LOCATION
                if obl.location and obl.location.text and "http" not in obl.location.text.lower():
                    mutated_loc_text = apply_wrong_location(obl.location)
                    parts, fields = build_deterministic_claim(
                        obl.audience, obl.action, obl.deadline, None, obl.required_documents
                    )
                    mutated_claim = f"{parts} tại {mutated_loc_text}" if parts else f"tại {mutated_loc_text}"
                    fields.append("location")
                    
                    wl_case = {
                        "benchmark_case_id": f"n{n_id}_v{v_id}_{o_id}_wrong_location",
                        "notice_id": n_id,
                        "version_id": v_id,
                        "obligation_id": o_id,
                        "claim_text": mutated_claim,
                        "claim_fields": fields,
                        "expected_trust_state": "CONFLICT",
                        "mutation_type": "WRONG_LOCATION",
                        "mutated_field": "location",
                        "original_value": obl.location.text,
                        "mutated_value": mutated_loc_text,
                        "synthetic": True,
                        "generation_rule": "replace_physical_location_fixed"
                    }
                    controlled_cases.append(wl_case)
                    
            # 4. UNSUPPORTED_CLAIM per notice
            unsupp_case = {
                "benchmark_case_id": f"n{n_id}_v{v_id}_unsupported",
                "notice_id": n_id,
                "version_id": v_id,
                "obligation_id": None,
                "claim_text": "Sinh viên được nghỉ hè 6 tháng",
                "claim_fields": [],
                "expected_trust_state": "INSUFFICIENT_EVIDENCE",
                "mutation_type": "UNSUPPORTED_CLAIM",
                "mutated_field": None,
                "original_value": None,
                "mutated_value": None,
                "synthetic": True,
                "generation_rule": "fixed_unsupported_claim"
            }
            controlled_cases.append(unsupp_case)
            
    with open(out_dir / "controlled_verification.jsonl", "w", encoding="utf-8") as f:
        for c in controlled_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
            
    with open(out_dir / "source_derived_supported.jsonl", "w", encoding="utf-8") as f:
        for c in source_derived_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Generated {len(controlled_cases)} controlled synthetic cases.")
    print(f"Generated {len(source_derived_cases)} source-derived supported cases.")

if __name__ == "__main__":
    main()
