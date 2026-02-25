from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "versions" in payload


def test_ready_shape() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert "checks" in payload
    assert "postgres" in payload["checks"]
    assert "qdrant" in payload["checks"]


def test_metrics() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
