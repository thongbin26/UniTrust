import pytest
import os
import sys

# Ensure frontend is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.demo_cases import DEMO_CASES

def test_demo_cases_schema():
    assert isinstance(DEMO_CASES, list)
    assert len(DEMO_CASES) >= 3
    
    for case in DEMO_CASES:
        assert "case_id" in case
        assert "label" in case
        assert "claim_text" in case
        assert "purpose" in case
        assert "is_synthetic" in case
        assert "source_notice_id" in case
        assert "source_version_id" in case
        
        assert isinstance(case["label"], str)
        assert isinstance(case["claim_text"], str)
        assert isinstance(case["is_synthetic"], bool)

def test_demo_cases_content():
    # Verify Case A
    case_a = next(c for c in DEMO_CASES if c["case_id"] == "case_a_supported")
    assert not case_a["is_synthetic"]
    assert case_a["source_notice_id"] == 13
    
    # Verify Case B
    case_b = next(c for c in DEMO_CASES if c["case_id"] == "case_b_conflict")
    assert case_b["is_synthetic"]
    assert case_b["source_notice_id"] == 13
    assert "SYNTHETIC DEMO MUTATION" in case_b["label"]
    
    # Verify Case C
    case_c = next(c for c in DEMO_CASES if c["case_id"] == "case_c_unsupported")
    assert case_c["is_synthetic"]
    assert case_c["source_notice_id"] is None
