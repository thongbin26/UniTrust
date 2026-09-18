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

def test_api_client_for_you_method():
    from frontend.api_client import APIClient
    # Monkeypatch the internal _post method to avoid needing the real running server in this test
    client = APIClient()

    called_url = None
    called_json = None

    def fake_post(url, json):
        nonlocal called_url, called_json
        called_url = url
        called_json = json
        return {"status": "ok"}

    client._post = fake_post

    profile = {
        "faculty": "Khoa Điện tử và Trí tuệ nhân tạo",
        "major": "Khoa học dữ liệu và Trí tuệ nhân tạo",
        "cohort": "K26",
        "program": "Đại trà"
    }

    result = client.for_you(profile)

    assert called_url == "/for-you"
    assert called_json == profile
    assert result == {"status": "ok"}
