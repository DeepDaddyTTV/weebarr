from fastapi.testclient import TestClient

from src.main import create_app
from src.weebarr.services import WeebarrService, candidate_score, normalize_title
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


def test_shape_anime_includes_audio_origin_fallback():
    service = WeebarrService(Settings(audio_lookup_enabled=False))
    shaped = service._shape_anime(
        {
            "id": 1,
            "idMal": 2,
            "countryOfOrigin": "JP",
            "title": {"romaji": "Example Anime"},
            "coverImage": {},
            "studios": {"nodes": []},
        },
        rank=1,
    )

    assert shaped["countryOfOrigin"] == "JP"
    assert (
        service._source_audio(shaped["countryOfOrigin"])["fallbackLabel"] == "JA only"
    )
