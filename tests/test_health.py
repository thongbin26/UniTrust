def test_health_endpoint(isolated_app_client):
    response = isolated_app_client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "UniTrust"
    assert data["database"] == "ok"
