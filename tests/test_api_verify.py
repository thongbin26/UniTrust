def test_verify_api_valid_deterministic(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "Sinh viên đóng học phí trước ngày 20/09/2026",
        "use_llm": False,
        "top_k": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["verdict"] in ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE"]

def test_verify_api_partially_verified(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "Sinh viên đóng học phí và mặc áo màu đỏ",
        "use_llm": False,
        "top_k": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["verdict"] in ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE"]

def test_verify_api_empty_text(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "",
        "use_llm": False,
    })
    assert response.status_code == 422

def test_verify_api_top_k_validation(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "Hello",
        "use_llm": False,
        "top_k": 0,
    })
    assert response.status_code == 422

    response = isolated_app_client.post("/verify", json={
        "text": "Hello",
        "use_llm": False,
        "top_k": 50,
    })
    assert response.status_code == 422

def test_verify_api_insufficient_evidence_reason(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "Sinh viên được nghỉ hè 6 tháng",
        "use_llm": False,
        "top_k": 5,
    })
    assert response.status_code == 200
    data = response.json()
    result = data["results"][0]
    assert result["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert result["abstention_reason"] == "UNSUPPORTED_CLAIM_FIELD"


def test_verify_api_preserves_understood_payment_without_official_comparison(isolated_app_client):
    response = isolated_app_client.post("/verify", json={
        "text": "đóng 450.000 đồng",
        "use_llm": False,
        "top_k": 5,
    })
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["understood_fields"]["action"]["normalized_value"] == "pay"
    assert result["understood_fields"]["amount"]["normalized_value"] == 450000
    # Understanding received input does not fabricate an official comparison.
    assert "amount" not in result["field_results"]
