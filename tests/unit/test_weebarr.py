from fastapi.testclient import TestClient

from src.main import create_app
from src.weebarr.services import candidate_score, normalize_title
from src.weebarr.settings import Settings


def test_health_endpoint_without_seerr():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["app"] == "weebarr"
    assert response.json()["seerr_configured"] is False


def test_seasonal_page_renders():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/seasonal")

    assert response.status_code == 200
    assert "Weebarr" in response.text
    assert "Seasonal Anime" in response.text


def test_title_normalization_and_candidate_score():
    candidate = {"name": "Witch Hat Atelier", "firstAirDate": "2026-04-06"}

    assert normalize_title("Witch Hat Atelier!!") == "witch hat atelier"
    assert candidate_score(["Witch Hat Atelier"], candidate, 2026) >= 100
