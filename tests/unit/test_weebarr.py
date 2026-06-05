import asyncio

from fastapi.testclient import TestClient

from src.main import create_app
from src.weebarr.services import (
    WeebarrService,
    candidate_score,
    compact_title,
    extract_installment_info,
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


def test_settings_summary_uses_explicit_base_settings():
    app = create_app(
        Settings(
            seerr_base_url="http://seerr.internal:5055",
            seerr_api_key="secret-value",
        )
    )
    client = TestClient(app)

    response = client.get("/api/settings/seerr")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["baseUrl"] == "http://seerr.internal:5055"
    assert payload["hasApiKey"] is True


def test_seasonal_page_renders():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/seasonal")

    assert response.status_code == 200
    assert "Weebarr" in response.text
    assert "Seasonal Anime" in response.text
    assert 'data-ui-select="season"' in response.text
    assert "ui-select-trigger" in response.text


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
    assert "Content Filter" in response.text


def test_settings_store_persists_overrides(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(Settings(config_path=str(config_path)))

    updated = store.save_seerr(
        {
            "base_url": "http://seerr.internal:5055",
            "api_key": "secret-value",
            "request_seasons": "latest",
            "tags": [12, 34],
            "content_filter_mode": "hide_nsfw",
        }
    )

    assert updated.seerr_base_url == "http://seerr.internal:5055"
    assert updated.seerr_request_seasons == "latest"
    assert updated.seerr_tags == [12, 34]
    assert updated.content_filter_mode == "hide_nsfw"
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
            "contentFilterMode": "show_all",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["connection"]["baseUrl"] == "http://seerr:5055"
    assert payload["connection"]["hasApiKey"] is True
    assert payload["connection"]["requestSeasons"] == "first"
    assert payload["connection"]["tags"] == [9, 11]
    assert payload["connection"]["contentFilterMode"] == "show_all"


def test_settings_store_persists_weebarr_request_history(tmp_path):
    store = SettingsStore(Settings(config_path=str(tmp_path / "weebarr.json")))

    saved = store.record_request(
        {
            "anilist_id": 120,
            "tmdb_id": 196950,
            "tvdb_id": 418666,
            "title": "Witch Hat Atelier",
            "season": "SPRING",
            "year": 2026,
            "requested_at": "2026-06-05T07:00:00+00:00",
            "request_seasons": [1],
        }
    )

    history = store.request_history(season="SPRING", year=2026)

    assert saved["anilist_id"] == 120
    assert len(history) == 1
    assert history[0]["title"] == "Witch Hat Atelier"
    assert history[0]["request_seasons"] == [1]


def test_title_normalization_and_candidate_score():
    candidate = {"name": "Witch Hat Atelier", "firstAirDate": "2026-04-06"}

    assert normalize_title("Witch Hat Atelier!!") == "witch hat atelier"
    assert compact_title("Marriage Toxin") == "marriagetoxin"
    assert candidate_score(["Witch Hat Atelier"], candidate, 2026) >= 100


def test_candidate_score_handles_collapsed_titles():
    candidate = {"name": "Marriage Toxin", "firstAirDate": "2026-04-07"}

    assert candidate_score(["MARRIAGETOXIN"], candidate, 2026) >= 100


def test_extract_installment_info_handles_suffixes():
    info = extract_installment_info(
        [
            "Re:ZERO -Starting Life in Another World- Season 4",
            "Re:ZERO kara Hajimeru Isekai Seikatsu 4th Season",
        ]
    )

    assert info["seasonNumber"] == 4
    assert info["label"] == "Season 4"
    assert info["baseTitle"] == "Re:ZERO -Starting Life in Another World"


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


def test_shape_anime_includes_installment_and_airing_labels():
    service = WeebarrService(Settings(audio_lookup_enabled=False))
    shaped = service._shape_anime(
        {
            "id": 1,
            "idMal": 2,
            "countryOfOrigin": "JP",
            "season": "SPRING",
            "seasonYear": 2026,
            "title": {"english": "Example Anime Season 2", "romaji": "Example Anime 2"},
            "coverImage": {},
            "studios": {"nodes": []},
        },
        rank=1,
    )

    assert shaped["installmentLabel"] == "Season 2"
    assert shaped["seasonLabel"] == "Spring 2026"


def test_content_filter_modes_hide_adult_and_nsfw_titles():
    adult_item = {
        "isAdult": True,
        "genres": ["Hentai"],
    }
    ecchi_item = {
        "isAdult": False,
        "genres": ["Ecchi"],
    }

    hide_nsfw_service = WeebarrService(
        Settings(audio_lookup_enabled=False, content_filter_mode="hide_nsfw")
    )
    show_all_service = WeebarrService(
        Settings(audio_lookup_enabled=False, content_filter_mode="show_all")
    )

    assert hide_nsfw_service._passes_content_filter(adult_item) is False
    assert hide_nsfw_service._passes_content_filter(ecchi_item) is True
    assert show_all_service._passes_content_filter(adult_item) is True


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


def test_classify_seerr_state_prefers_requested_target_season():
    service = WeebarrService(Settings())
    anime = {"installment": {"seasonNumber": None, "label": None}}
    best = {
        "id": 196950,
        "name": "Witch Hat Atelier",
        "mediaInfo": {
            "status": 4,
            "seasons": [{"seasonNumber": 1, "status": 4}],
            "requests": [{"status": 2, "seasons": [{"seasonNumber": 1, "status": 2}]}],
        },
    }
    details = {"seasons": [{"seasonNumber": 0}, {"seasonNumber": 1}]}

    result = service._classify_seerr_state(anime, best, details, best_score=110)

    assert result["state"] == "requested"
    assert result["requestable"] is False
    assert result["targetSeason"] == 1
    assert result["requestSeasons"] == [1]


def test_classify_seerr_state_treats_partial_target_season_as_tracked():
    service = WeebarrService(Settings())
    anime = {"installment": {"seasonNumber": 4, "label": "Season 4"}}
    best = {
        "id": 65942,
        "name": "Re:ZERO -Starting Life in Another World-",
        "mediaInfo": {
            "status": 4,
            "seasons": [
                {"seasonNumber": 1, "status": 5},
                {"seasonNumber": 4, "status": 4},
            ],
            "requests": [],
        },
    }
    details = {
        "seasons": [
            {"seasonNumber": 0},
            {"seasonNumber": 1},
            {"seasonNumber": 2},
            {"seasonNumber": 3},
            {"seasonNumber": 4},
        ]
    }

    result = service._classify_seerr_state(anime, best, details, best_score=95)

    assert result["state"] == "partial"
    assert result["requestable"] is False
    assert result["label"] == "Season 4 Partial"
    assert result["requestSeasons"] == [4]


def test_classify_seerr_state_marks_missing_target_season_when_absent():
    service = WeebarrService(Settings())
    anime = {"installment": {"seasonNumber": 4, "label": "Season 4"}}
    best = {
        "id": 65942,
        "name": "Re:ZERO -Starting Life in Another World-",
        "mediaInfo": {
            "status": 4,
            "seasons": [
                {"seasonNumber": 1, "status": 5},
            ],
            "requests": [],
        },
    }
    details = {
        "seasons": [
            {"seasonNumber": 0},
            {"seasonNumber": 1},
            {"seasonNumber": 2},
            {"seasonNumber": 3},
            {"seasonNumber": 4},
        ]
    }

    result = service._classify_seerr_state(anime, best, details, best_score=95)

    assert result["state"] == "requestable"
    assert result["requestable"] is True
    assert result["label"] == "Missing Season 4"
    assert result["requestSeasons"] == [4]


def test_resolve_seerr_prefers_ids_moe_mapping_before_title_search():
    service = WeebarrService(
        Settings(
            seerr_base_url="http://seerr.internal:5055",
            seerr_api_key="secret",
        )
    )
    anime = {
        "malId": 38959,
        "title": "Witch Hat Atelier",
        "englishTitle": "Witch Hat Atelier",
        "romajiTitle": "Tongari Boushi no Atelier",
        "nativeTitle": "とんがり帽子のアトリエ",
        "startYear": 2026,
        "installment": {"seasonNumber": 1, "label": "Season 1"},
    }

    async def fake_ids_moe(_mal_id: int) -> int | None:
        return 196950

    async def fake_details(_tmdb_id: int) -> dict[str, object]:
        return {
            "id": 196950,
            "name": "Witch Hat Atelier",
            "firstAirDate": "2026-04-06",
            "externalIds": {"tvdbId": 418666},
            "posterPath": "/poster.jpg",
            "backdropPath": "/backdrop.jpg",
            "mediaInfo": {
                "status": 4,
                "seasons": [{"seasonNumber": 1, "status": 4}],
                "requests": [{"status": 2, "seasons": [{"seasonNumber": 1}]}],
            },
            "seasons": [{"seasonNumber": 0}, {"seasonNumber": 1}],
        }

    async def fail_search(_query: str) -> list[dict]:
        raise AssertionError(
            "title search should not run when ids.moe resolves a tmdb id"
        )

    service._ids_moe_tmdb_id = fake_ids_moe  # type: ignore[method-assign]
    service._seerr_tv_details = fake_details  # type: ignore[method-assign]
    service._seerr_search = fail_search  # type: ignore[method-assign]

    result = asyncio.run(service._resolve_seerr(anime))

    assert result["tmdbId"] == 196950
    assert result["tvdbId"] == 418666
    assert result["state"] == "requested"
    assert result["requestable"] is False


def test_resolve_request_seasons_converts_string_modes():
    service = WeebarrService(Settings())

    async def fake_details(_tmdb_id: int) -> dict:
        return {
            "seasons": [
                {"seasonNumber": 0},
                {"seasonNumber": 1},
                {"seasonNumber": 2},
                {"seasonNumber": 4},
            ]
        }

    service._seerr_tv_details = fake_details  # type: ignore[method-assign]

    assert asyncio.run(service._resolve_request_seasons(1, "all")) == [1, 2, 4]
    assert asyncio.run(service._resolve_request_seasons(1, "first")) == [1]
    assert asyncio.run(service._resolve_request_seasons(1, "latest")) == [4]
