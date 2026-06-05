from fastapi.testclient import TestClient

from src.main import create_app
from src.weebarr.services import (
    WeebarrService,
    candidate_score,
    normalize_title,
    tmdb_image_url,
)
from src.weebarr.settings import Settings, SettingsStore


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


def test_requests_page_renders():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/requests")

    assert response.status_code == 200
    assert "Requested Anime" in response.text
    assert "Hide Requested" not in response.text


def test_settings_page_renders():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/settings")

    assert response.status_code == 200
    assert "Manage Seerr" in response.text


def test_settings_store_persists_overrides(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(Settings(config_path=str(config_path)))

    updated = store.save_seerr(
        {
            "base_url": "http://seerr.internal:5055",
            "api_key": "secret-value",
            "request_seasons": "latest",
            "tags": [12, 34],
        }
    )

    assert updated.seerr_base_url == "http://seerr.internal:5055"
    assert updated.seerr_request_seasons == "latest"
    assert updated.seerr_tags == [12, 34]
    assert config_path.exists()


def test_settings_endpoint_saves_connection(tmp_path):
    app = create_app(Settings(config_path=str(tmp_path / "weebarr.json")))
    client = TestClient(app)

    response = client.put(
        "/api/settings/seerr",
        json={
            "baseUrl": "http://seerr:5055",
            "apiKey": "abc123",
            "requestSeasons": "first",
            "tags": [9, 11],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["connection"]["baseUrl"] == "http://seerr:5055"
    assert payload["connection"]["hasApiKey"] is True
    assert payload["connection"]["requestSeasons"] == "first"
    assert payload["connection"]["tags"] == [9, 11]


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


def test_seasonal_page_includes_hide_requested_toggle():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/seasonal")

    assert response.status_code == 200
    assert "Hide Requested" in response.text


def test_tmdb_image_url_and_seerr_art_override():
    service = WeebarrService(Settings())
    shaped = {
        "cover": "https://anilist.example/cover.jpg",
        "banner": "https://anilist.example/banner.jpg",
        "seerr": {
            "posterUrl": tmdb_image_url("/poster.jpg", "w500"),
            "backdropUrl": tmdb_image_url("backdrop.jpg", "w780"),
        },
    }

    updated = service._apply_seerr_art(shaped)

    assert updated["cover"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert updated["banner"] == "https://image.tmdb.org/t/p/w780/backdrop.jpg"
    assert updated["coverSource"] == "tmdb"
    assert updated["bannerSource"] == "tmdb"
