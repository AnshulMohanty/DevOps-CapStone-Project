def test_root_reports_service_and_version(client):
    body = client.get("/").json()
    assert body["service"] == "FoundIt API"
    assert body["version"]


def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}


def test_ready_checks_the_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/api/items")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "foundit_items_reported_total" in response.text
    assert "http_requests_total" in response.text
