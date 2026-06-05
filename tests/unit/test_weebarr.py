import asyncio

from fastapi.testclient import TestClient

import src.main as main_module
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


def authenticated_client(tmp_path, **settings_overrides):
    base = {
        "config_path": str(tmp_path / "weebarr.json"),
        "auth_mode": "local",
        "auth_username": "adminuser",
        "auth_password": "example-password",
        "session_secret": "example-session-secret",
    }
    base.update(settings_overrides)
    client = TestClient(create_app(Settings(**base)))
    login = client.post(
        "/api/auth/login",
        json={
            "username": base["auth_username"],
            "password": base["auth_password"],
            "next": "/seasonal",
        },
    )
    assert login.status_code == 200
    return client


def test_health_endpoint_without_seerr():
    app = create_app(Settings())
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["app"] == "weebarr"
    assert response.json()["seerr_configured"] is False


def test_settings_summary_uses_explicit_base_settings(tmp_path):
    client = authenticated_client(
        tmp_path,
        seerr_base_url="https://seerr.example.test",
        seerr_api_key="secret-value",
    )

    response = client.get("/api/settings/seerr")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["baseUrl"] == "https://seerr.example.test"
    assert payload["hasApiKey"] is True


def test_seasonal_page_renders(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.get("/seasonal")

    assert response.status_code == 200
    assert "Weebarr" in response.text
    assert "Seasonal Anime" in response.text
    assert 'data-ui-select="season"' in response.text
    assert "ui-select-trigger" in response.text
    assert 'class="access-card"' not in response.text
    assert "Sign Out" in response.text


def test_requests_page_renders(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.get("/requests")

    assert response.status_code == 200
    assert "Requested Anime" in response.text
    assert "Hide Requested" not in response.text


def test_settings_page_renders(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.get("/settings")

    assert response.status_code == 200
    assert "App Behavior" in response.text
    assert "Single-Admin Access" in response.text
    assert "Seerr Integration" in response.text
    assert "Strict Monitoring" in response.text
    assert "Content Filter" in response.text
    assert "Weebarr Admin Token" not in response.text
    assert 'data-ui-select="settingsRequestSeasons"' in response.text
    assert 'data-ui-select="settingsContentFilterMode"' in response.text


def test_settings_store_persists_overrides(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(Settings(config_path=str(config_path)))

    updated = store.save_weebarr(
        {
            "content_filter_mode": "hide_nsfw",
            "strict_monitoring": True,
        }
    )

    assert updated.content_filter_mode == "hide_nsfw"
    assert updated.strict_monitoring is True
    assert config_path.exists()


def test_settings_endpoint_saves_connection(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/seerr",
        json={
            "baseUrl": "https://seerr.example.test",
            "apiKey": "abc123",
            "requestSeasons": "first",
            "tags": [9, 11],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["connection"]["baseUrl"] == "https://seerr.example.test"
    assert payload["connection"]["hasApiKey"] is True
    assert payload["connection"]["requestSeasons"] == "first"
    assert payload["connection"]["tags"] == [9, 11]


def test_weebarr_settings_endpoint_saves_app_preferences(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/weebarr",
        json={
            "contentFilterMode": "show_all",
            "strictMonitoring": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["weebarr"]["contentFilterMode"] == "show_all"
    assert payload["weebarr"]["strictMonitoring"] is True


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


def test_shape_anime_includes_embeddable_trailer_metadata():
    service = WeebarrService(Settings(audio_lookup_enabled=False))
    shaped = service._shape_anime(
        {
            "id": 1,
            "idMal": 2,
            "countryOfOrigin": "JP",
            "title": {"english": "Example Anime"},
            "trailer": {
                "id": "abc123",
                "site": "youtube",
                "thumbnail": "https://img.youtube.example/thumb.jpg",
            },
            "coverImage": {},
            "studios": {"nodes": []},
        },
        rank=1,
    )

    assert shaped["trailer"]["site"] == "youtube"
    assert shaped["trailer"]["siteLabel"] == "YouTube"
    assert shaped["trailer"]["embedUrl"].startswith(
        "https://www.youtube-nocookie.com/embed/abc123"
    )
    assert shaped["trailer"]["watchUrl"] == "https://www.youtube.com/watch?v=abc123"


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


def test_seasonal_page_includes_hide_requested_toggle(tmp_path):
    client = authenticated_client(tmp_path)

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


def test_classify_seerr_state_marks_all_required_seasons_available():
    service = WeebarrService(Settings())
    anime = {"installment": {"seasonNumber": 2, "label": "Season 2"}}
    best = {
        "id": 123,
        "name": "Example Show",
        "mediaInfo": {
            "status": 5,
            "seasons": [
                {"seasonNumber": 1, "status": 5},
                {"seasonNumber": 2, "status": 5},
            ],
            "requests": [],
        },
    }
    details = {
        "seasons": [{"seasonNumber": 0}, {"seasonNumber": 1}, {"seasonNumber": 2}]
    }

    result = service._classify_seerr_state(anime, best, details, best_score=105)

    assert result["state"] == "available"
    assert result["requestable"] is False


def test_classify_seerr_state_marks_first_season_missing_without_request_trace():
    service = WeebarrService(Settings())
    anime = {"installment": {"seasonNumber": 1, "label": "Season 1"}}
    best = {
        "id": 123,
        "name": "Example Show",
        "mediaInfo": {
            "status": 1,
            "seasons": [],
            "requests": [],
        },
    }
    details = {"seasons": [{"seasonNumber": 0}, {"seasonNumber": 1}]}

    result = service._classify_seerr_state(anime, best, details, best_score=70)

    assert result["state"] == "missing"
    assert result["requestable"] is True


def test_unconfigured_app_redirects_to_setup(tmp_path):
    app = create_app(Settings(config_path=str(tmp_path / "weebarr.json")))
    client = TestClient(app, follow_redirects=False)

    response = client.get("/seasonal")

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/setup"


def test_setup_page_renders(tmp_path):
    app = create_app(Settings(config_path=str(tmp_path / "weebarr.json")))
    client = TestClient(app)

    response = client.get("/setup")

    assert response.status_code == 200
    assert "Create Account" in response.text
    assert "Use Plex Auth" in response.text
    assert "Setup Token" not in response.text


def test_local_setup_persists_access_and_requires_session_auth(tmp_path):
    config_path = tmp_path / "weebarr.json"
    app = create_app(Settings(config_path=str(config_path)))
    client = TestClient(app)

    response = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "local"
    assert payload["redirectTo"] == "/login"
    assert "generatedApiKey" not in payload

    protected_page = client.get("/seasonal", follow_redirects=False)
    assert protected_page.status_code in {302, 307}
    assert protected_page.headers["location"].startswith("/login")

    new_client = TestClient(create_app(Settings(config_path=str(config_path))))
    unauthorized = new_client.get("/api/config")
    assert unauthorized.status_code == 401


def test_local_login_rejects_bad_password_and_accepts_good_password(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(create_app(Settings(config_path=str(config_path))))
    setup_response = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )
    assert setup_response.status_code == 200

    new_client = TestClient(create_app(Settings(config_path=str(config_path))))
    bad = new_client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "wrong-password",
            "next": "/seasonal",
        },
    )
    assert bad.status_code == 401

    good = new_client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "example-password",
            "next": "/seasonal",
        },
    )
    assert good.status_code == 200
    assert good.json()["redirectTo"] == "/seasonal"


def test_login_page_offers_only_local_sign_in_after_local_setup(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(create_app(Settings(config_path=str(config_path))))

    response = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )

    assert response.status_code == 200

    new_client = TestClient(create_app(Settings(config_path=str(config_path))))
    login_page = new_client.get("/login")
    assert login_page.status_code == 200
    assert "Username" in login_page.text
    assert "Password" in login_page.text
    assert "Continue with Plex" not in login_page.text


def test_plex_only_login_page_hides_local_form(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(Settings(config_path=str(config_path)))
    store.save_auth(
        {
            "mode": "plex",
            "session_secret": "example-plex-session-secret",
            "plex_allowed_users": ["admin@example.invalid"],
        }
    )
    client = TestClient(create_app(Settings(config_path=str(config_path))))

    login_page = client.get("/login")

    assert login_page.status_code == 200
    assert "Continue with Plex" in login_page.text
    assert "Username" not in login_page.text
    assert "Password" not in login_page.text


def test_plex_first_can_add_local_account_and_offer_both_login_paths(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(
        Settings(config_path=str(config_path), app_api_key="example-automation-token")
    )
    store.save_auth(
        {
            "mode": "plex",
            "session_secret": "example-plex-session-secret",
            "plex_allowed_users": ["admin@example.invalid"],
        }
    )
    client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                app_api_key="example-automation-token",
            )
        )
    )

    response = client.put(
        "/api/settings/access/local",
        headers={"X-API-Key": "example-automation-token"},
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["authMode"] == "both"
    assert payload["access"]["localAuthConfigured"] is True
    assert payload["access"]["plexLoginEnabled"] is True

    login_page = client.get("/login")
    assert login_page.status_code == 200
    assert "Continue with Plex" in login_page.text
    assert "Username" in login_page.text
    assert "Password" in login_page.text


def test_plex_setup_start_uses_current_request_origin_for_callback(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="http://localhost",
    )

    async def fake_create_plex_pin(_settings):
        return {"id": 123, "code": "example-pin-code"}

    monkeypatch.setattr(main_module, "create_plex_pin", fake_create_plex_pin)

    response = client.get("/auth/plex/start?setup=1", follow_redirects=False)

    assert response.status_code in {302, 307}
    location = response.headers["location"]
    assert location.startswith("https://app.plex.tv/auth#?")
    assert "forwardUrl=http%3A%2F%2Flocalhost%2Fauth%2Fplex%2Fcallback" in location
    assert "code=example-pin-code" in location


def test_plex_setup_claims_single_admin_account(tmp_path, monkeypatch):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="http://localhost",
    )

    async def fake_create_plex_pin(_settings):
        return {"id": 123, "code": "example-pin-code"}

    async def fake_fetch_plex_pin(_settings, *, pin_id: int, code: str):
        assert pin_id == 123
        assert code == "example-pin-code"
        return {"authToken": "example-plex-auth-token"}

    async def fake_fetch_plex_user(_settings, *, token: str):
        assert token == "example-plex-auth-token"
        return {
            "username": "adminuser",
            "email": "admin@example.invalid",
            "friendlyName": "Admin User",
        }

    monkeypatch.setattr(main_module, "create_plex_pin", fake_create_plex_pin)
    monkeypatch.setattr(main_module, "fetch_plex_pin", fake_fetch_plex_pin)
    monkeypatch.setattr(main_module, "fetch_plex_user", fake_fetch_plex_user)

    start = client.get("/auth/plex/start?setup=1", follow_redirects=False)
    assert start.status_code in {302, 307}

    callback = client.get("/auth/plex/callback", follow_redirects=False)
    assert callback.status_code in {302, 307}
    assert callback.headers["location"] == "/seasonal"

    seasonal = client.get("/seasonal")
    assert seasonal.status_code == 200

    access = client.get("/api/setup/status")
    payload = access.json()
    assert payload["setupRequired"] is False
    assert payload["authMode"] == "plex"
    assert payload["plexAllowedUsers"] == [
        "adminuser",
        "admin@example.invalid",
        "Admin User",
    ]

    new_client = TestClient(create_app(Settings(config_path=str(config_path))))
    login_page = new_client.get("/login")
    assert login_page.status_code == 200
    assert "Continue with Plex" in login_page.text
    assert "Username" not in login_page.text


def test_public_host_cannot_open_setup_routes(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="https://weebarr.example.test",
    )

    blocked_page = client.get("/setup")
    assert blocked_page.status_code == 403
    assert (
        "First-run setup is only available from a local or private-network address."
        in blocked_page.text
    )

    blocked_api = client.get("/api/setup/status")
    assert blocked_api.status_code == 403
    assert (
        "First-run setup is only available from a local or private-network address."
        in blocked_api.json()["detail"]
    )


def test_public_host_does_not_redirect_to_setup(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="https://weebarr.example.test",
        follow_redirects=False,
    )

    response = client.get("/seasonal")

    assert response.status_code == 403


def test_classify_seerr_state_marks_later_season_as_partial_when_monitored():
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

    assert result["state"] == "partial"
    assert result["requestable"] is False
    assert result["label"] == "Partially Available"
    assert result["requestSeasons"] == [4]


def test_classify_seerr_state_strict_monitoring_marks_later_season_missing():
    service = WeebarrService(Settings(strict_monitoring=True))
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

    assert result["state"] == "season_missing"
    assert result["requestable"] is True
    assert result["label"] == "Season Missing"
    assert result["requestSeasons"] == [4]


def test_resolve_seerr_prefers_ids_moe_mapping_before_title_search():
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
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
