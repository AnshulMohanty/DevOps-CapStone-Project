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


def test_ready_returns_503_when_the_database_fails(client):
    from sqlalchemy.exc import OperationalError

    from app.db import get_db
    from app.main import app

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("password authentication failed"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = client.get("/ready")
        assert response.status_code == 503
        assert client.get("/health").status_code == 200  # liveness stays green: no restart loop
    finally:
        app.dependency_overrides.clear()


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/api/items")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "foundit_items_reported_total" in response.text
    assert "http_requests_total" in response.text
