from app.verification.comparator import FieldComparator
from app.verification.models import FieldMatchState
from app.models.obligation import ActionType

def test_compare_deadline():
    assert FieldComparator.compare_deadline("20/09/2026", "2026-09-20").state == FieldMatchState.MATCH
    assert FieldComparator.compare_deadline("25/09/2026", "2026-09-20").state == FieldMatchState.CONFLICT

def test_compare_amount():
    assert FieldComparator.compare_amount("1.000.000 vnd", "1000000").state == FieldMatchState.MATCH
    assert FieldComparator.compare_amount("500.000", "1000000").state == FieldMatchState.CONFLICT

def test_compare_action():
    assert FieldComparator.compare_action("đóng tiền", ActionType.PAY).state == FieldMatchState.MATCH
    assert FieldComparator.compare_action("đóng tiền", ActionType.REGISTER).state == FieldMatchState.CONFLICT
    
def test_compare_location():
    assert FieldComparator.compare_location("http://example.com", "Phòng Đào tạo").state == FieldMatchState.CONFLICT

def test_compare_audience():
    assert FieldComparator.compare_audience("all", True, []).state == FieldMatchState.MATCH
    assert FieldComparator.compare_audience("all", False, ["CNTT"]).state == FieldMatchState.INSUFFICIENT_EVIDENCE
