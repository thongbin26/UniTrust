from fastapi.testclient import TestClient
from main import app

def test_evidence_api_list():
    with TestClient(app) as client:
        response = client.get("/evidence/notices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "has_structured_obligations" in data[0]
            assert "structured_coverage" in data[0]

def test_evidence_api_not_found():
    with TestClient(app) as client:
        response = client.get("/evidence/notices/999999")
        assert response.status_code == 404

def test_evidence_api_changes():
    with TestClient(app) as client:
        response = client.get("/evidence/notices/999999/changes")
        assert response.status_code == 200
        data = response.json()
        assert data["has_history"] is False
        assert data["changes"] == []
