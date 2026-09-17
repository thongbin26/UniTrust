from fastapi.testclient import TestClient
from main import app

def test_for_you_api():
    with TestClient(app) as client:
        response = client.post("/for-you", json={
            "faculty": "CNTT",
            "major": "Kỹ thuật phần mềm",
            "cohort": "K21",
            "program": "CLC"
        })
        assert response.status_code == 200
        data = response.json()
        assert "obligations" in data
        if len(data["obligations"]) > 0:
            obs = data["obligations"][0]
            assert obs["applicability"]["status"] in ["APPLIES", "DOES_NOT_APPLY", "UNKNOWN"]
            assert obs["temporal_status"] in ["CURRENT", "SUPERSEDED_OUTDATED", "UNKNOWN"]
