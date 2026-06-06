import asyncio
import json
from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

import src.main as main_module
import src.weebarr.services as services_module
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


def authenticated_client(
    tmp_path, *, base_url: str = "http://testserver", **settings_overrides
):
    base = {
        "config_path": str(tmp_path / "weebarr.json"),
        "auth_mode": "local",
        "auth_username": "adminuser",
        "auth_password": "example-password",
        "session_secret": "example-session-secret",
    }
    base.update(settings_overrides)
    client = TestClient(create_app(Settings(**base)), base_url=base_url)
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


def test_configured_auth_requires_explicit_session_secret(tmp_path):
    with pytest.raises(
        RuntimeError,
        match="A session secret is required when Weebarr authentication is enabled.",
    ):
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                auth_mode="local",
                auth_username="adminuser",
                auth_password="example-password",
            )
        )


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
    assert "Force Series Type" in response.text
    assert "Quality Profile" in response.text
    assert "Weebarr Admin Token" not in response.text
    assert 'data-settings-tab="weebarr"' in response.text
    assert 'data-settings-tab="automation"' in response.text
    assert 'data-settings-tab="authentication"' in response.text
    assert 'data-settings-tab="connections"' in response.text
    assert "Season Auto-Requests" in response.text
    assert "Named Theme" in response.text
    assert 'data-ui-select="settingsRequestSeasons"' in response.text
    assert 'data-ui-select="settingsContentFilterMode"' in response.text
    assert 'data-ui-select="settingsSeriesType"' in response.text
    assert 'data-ui-select="settingsActiveThemeId"' in response.text


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


def test_settings_store_persists_automation_and_theme_overrides(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(Settings(config_path=str(config_path)))

    updated = store.save_weebarr(
        {
            "automation_enabled_buckets": {
                "s_tier": True,
                "canon": True,
                "bingeable": False,
                "filler": False,
            },
            "automation_scan_interval_days": 14,
            "automation_scan_interval_hours": 6,
            "active_theme_id": "color-picker",
            "color_picker_tokens": {
                "dark": {
                    "bg": "#111111",
                    "bg2": "#121212",
                    "pageTail": "#000000",
                    "pageGlowA": "#ffffff14",
                    "pageGlowB": "#99999914",
                    "pageGlowC": "#77777714",
                    "panel": "#181818ee",
                    "panel2": "#222222dd",
                    "panel3": "#141414f0",
                    "mediaScrim": "#090909aa",
                    "line": "#ffffff20",
                    "lineStrong": "#ffffff40",
                    "text": "#f5f5f5",
                    "muted": "#d0d0d0",
                    "subtle": "#909090",
                    "cyan": "#ffffff",
                    "pink": "#cccccc",
                    "purple": "#bbbbbb",
                    "green": "#eeeeee",
                    "warning": "#fafafa",
                },
                "light": {
                    "bg": "#fafafa",
                    "bg2": "#f1f1f1",
                    "pageTail": "#ededed",
                    "pageGlowA": "#11111110",
                    "pageGlowB": "#33333310",
                    "pageGlowC": "#55555510",
                    "panel": "#ffffffff",
                    "panel2": "#f6f6f6e8",
                    "panel3": "#ffffffee",
                    "mediaScrim": "#f4f4f4cc",
                    "line": "#11111120",
                    "lineStrong": "#11111140",
                    "text": "#111111",
                    "muted": "#444444",
                    "subtle": "#666666",
                    "cyan": "#111111",
                    "pink": "#2d2d2d",
                    "purple": "#444444",
                    "green": "#1d1d1d",
                    "warning": "#111111",
                },
            },
        }
    )

    assert updated.automation_enabled is True
    assert updated.automation_scan_interval_days == 14
    assert updated.automation_scan_interval_hours == 6
    assert updated.active_theme_id == "color-picker"
    assert updated.color_picker_tokens["dark"]["cyan"] == "#ffffff"


def test_settings_store_backfills_legacy_automation_hours(tmp_path):
    config_path = tmp_path / "weebarr.json"
    config_path.write_text(
        json.dumps(
            {
                "weebarr": {
                    "automation_enabled_buckets": {
                        "s_tier": True,
                        "canon": False,
                        "bingeable": False,
                        "filler": False,
                    },
                    "automation_scan_interval_days": 9,
                }
            }
        ),
        encoding="utf-8",
    )

    store = SettingsStore(Settings(config_path=str(config_path)))
    current = store.get()

    assert current.automation_scan_interval_days == 9
    assert current.automation_scan_interval_hours == 0


def test_settings_endpoint_saves_connection(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/seerr",
        json={
            "baseUrl": "https://seerr.example.test",
            "apiKey": "abc123",
            "requestSeasons": "first",
            "forceQualityProfile": True,
            "profileId": 22,
            "seriesType": "standard",
            "tags": [9, 11],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["connection"]["baseUrl"] == "https://seerr.example.test"
    assert payload["connection"]["hasApiKey"] is True
    assert payload["connection"]["requestSeasons"] == "first"
    assert payload["connection"]["forceQualityProfile"] is True
    assert payload["connection"]["profileId"] == 22
    assert payload["connection"]["seriesType"] == "standard"
    assert payload["connection"]["tags"] == [9, 11]


def test_settings_endpoint_can_clear_saved_request_overrides(tmp_path):
    client = authenticated_client(
        tmp_path,
        seerr_base_url="https://seerr.example.test",
        seerr_api_key="abc123",
    )

    seeded = client.put(
        "/api/settings/seerr",
        json={
            "sonarrServerId": 8,
            "profileId": 22,
            "forceQualityProfile": True,
            "seriesType": "anime",
            "tags": [9, 11],
        },
    )
    assert seeded.status_code == 200

    response = client.put(
        "/api/settings/seerr",
        json={
            "sonarrServerId": None,
            "profileId": None,
            "forceQualityProfile": False,
            "seriesType": "default",
            "tags": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["connection"]["sonarrServerId"] is None
    assert payload["connection"]["profileId"] is None
    assert payload["connection"]["forceQualityProfile"] is False
    assert payload["connection"]["seriesType"] == "default"
    assert payload["connection"]["tags"] == []


def test_settings_endpoint_rejects_forced_quality_profile_without_id(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/seerr",
        json={
            "forceQualityProfile": True,
            "profileId": None,
        },
    )

    assert response.status_code == 400
    assert "Quality Profile ID is required" in response.json()["detail"]


def test_weebarr_settings_endpoint_saves_app_preferences(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/weebarr",
        json={
            "contentFilterMode": "show_all",
            "strictMonitoring": True,
            "automation": {
                "enabledBuckets": {
                    "s_tier": True,
                    "canon": False,
                    "bingeable": True,
                    "filler": False,
                },
                "scanIntervalDays": 21,
                "scanIntervalHours": 8,
            },
            "theme": {
                "activeThemeId": "monochrome",
                "colorPickerTokens": {
                    "dark": {
                        "bg": "#111111",
                        "bg2": "#1a1a1a",
                        "pageTail": "#050505",
                        "pageGlowA": "#ffffff17",
                        "pageGlowB": "#ffffff0d",
                        "pageGlowC": "#ffffff0a",
                        "panel": "#1b1b1bd9",
                        "panel2": "#242424ba",
                        "panel3": "#141414ec",
                        "mediaScrim": "#09090994",
                        "line": "#ffffff2e",
                        "lineStrong": "#ffffff55",
                        "text": "#f7f7f7",
                        "muted": "#d0d0d0",
                        "subtle": "#a4a4a4",
                        "cyan": "#f7f7f7",
                        "pink": "#d7d7d7",
                        "purple": "#bfbfbf",
                        "green": "#ededed",
                        "warning": "#ffffff",
                    },
                    "light": {
                        "bg": "#fbfbfb",
                        "bg2": "#efefef",
                        "pageTail": "#e4e4e4",
                        "pageGlowA": "#11111114",
                        "pageGlowB": "#1111110a",
                        "pageGlowC": "#11111108",
                        "panel": "#ffffffff",
                        "panel2": "#f6f6f6d9",
                        "panel3": "#ffffffef",
                        "mediaScrim": "#f4f4f4bd",
                        "line": "#11111124",
                        "lineStrong": "#11111142",
                        "text": "#111111",
                        "muted": "#3f3f3f",
                        "subtle": "#5b5b5b",
                        "cyan": "#111111",
                        "pink": "#2f2f2f",
                        "purple": "#4a4a4a",
                        "green": "#1f1f1f",
                        "warning": "#111111",
                    },
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["weebarr"]["contentFilterMode"] == "show_all"
    assert payload["weebarr"]["strictMonitoring"] is True
    assert payload["weebarr"]["automation"]["enabledBuckets"]["s_tier"] is True
    assert payload["weebarr"]["automation"]["enabledBuckets"]["bingeable"] is True
    assert payload["weebarr"]["automation"]["scanIntervalDays"] == 21
    assert payload["weebarr"]["automation"]["scanIntervalHours"] == 8
    assert payload["weebarr"]["theme"]["activeThemeId"] == "monochrome"


def test_weebarr_settings_rejects_zero_day_zero_hour_automation(tmp_path):
    client = authenticated_client(tmp_path)

    response = client.put(
        "/api/settings/weebarr",
        json={
            "automation": {
                "enabledBuckets": {
                    "s_tier": True,
                    "canon": False,
                    "bingeable": False,
                    "filler": False,
                },
                "scanIntervalDays": 0,
                "scanIntervalHours": 0,
            }
        },
    )

    assert response.status_code == 400
    assert "at least 1 hour" in response.json()["detail"]


def test_theme_import_from_url_updates_theme_catalog(tmp_path, monkeypatch):
    client = authenticated_client(tmp_path)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "aurora-spark",
                "name": "Aurora Spark",
                "description": "Imported test theme",
                "tokens": {
                    "dark": {
                        "bg": "#0a0c12",
                        "bg2": "#111520",
                        "pageTail": "#05070b",
                        "pageGlowA": "#28c7ff21",
                        "pageGlowB": "#8b5cf61f",
                        "pageGlowC": "#ff3c7d14",
                        "panel": "#121925e0",
                        "panel2": "#171f2cb8",
                        "panel3": "#0d121ae8",
                        "mediaScrim": "#05091194",
                        "line": "#7a97b333",
                        "lineStrong": "#7ebfe161",
                        "text": "#f5f7fb",
                        "muted": "#99a8bb",
                        "subtle": "#6f7e90",
                        "cyan": "#28c7ff",
                        "pink": "#ff3c7d",
                        "purple": "#8b5cf6",
                        "green": "#55e18d",
                        "warning": "#ffd166",
                    },
                    "light": {
                        "bg": "#edf6ff",
                        "bg2": "#f8fbff",
                        "pageTail": "#e9f4ff",
                        "pageGlowA": "#28c7ff33",
                        "pageGlowB": "#8b5cf629",
                        "pageGlowC": "#ff3c7d14",
                        "panel": "#ffffffd1",
                        "panel2": "#ffffffb3",
                        "panel3": "#ffffffe8",
                        "mediaScrim": "#edf6ffbd",
                        "line": "#425d7c33",
                        "lineStrong": "#28a1da6b",
                        "text": "#121c2b",
                        "muted": "#5d6e82",
                        "subtle": "#778699",
                        "cyan": "#28c7ff",
                        "pink": "#ff3c7d",
                        "purple": "#8b5cf6",
                        "green": "#55e18d",
                        "warning": "#ffd166",
                    },
                },
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            assert url == "https://example.test/aurora-spark.json"
            return FakeResponse()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        "/api/themes/import/url",
        json={"url": "https://example.test/aurora-spark.json"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["activeThemeId"] == "aurora-spark"
    assert any(
        theme["id"] == "aurora-spark" for theme in payload["weebarr"]["theme"]["themes"]
    )


def test_theme_import_from_zip_updates_theme_catalog(tmp_path):
    client = authenticated_client(tmp_path)
    archive_bytes = BytesIO()
    with ZipFile(archive_bytes, "w") as archive:
        archive.writestr(
            "theme.json",
            json.dumps(
                {
                    "id": "zip-theme",
                    "name": "Zip Theme",
                    "description": "Theme imported from zip",
                    "tokens": {
                        "dark": {
                            "bg": "#050911",
                            "bg2": "#08111b",
                            "pageTail": "#03060b",
                            "pageGlowA": "#28c7ff21",
                            "pageGlowB": "#ff3c7d1f",
                            "pageGlowC": "#502aff14",
                            "panel": "#101720db",
                            "panel2": "#141c27b8",
                            "panel3": "#0d121ae6",
                            "mediaScrim": "#05091194",
                            "line": "#7a97b333",
                            "lineStrong": "#7ebfe161",
                            "text": "#f5f7fb",
                            "muted": "#99a8bb",
                            "subtle": "#6f7e90",
                            "cyan": "#28c7ff",
                            "pink": "#ff3c7d",
                            "purple": "#b466ff",
                            "green": "#55e18d",
                            "warning": "#ffd166",
                        },
                        "light": {
                            "bg": "#edf6ff",
                            "bg2": "#f8fbff",
                            "pageTail": "#e9f4ff",
                            "pageGlowA": "#28c7ff33",
                            "pageGlowB": "#ff3c7d29",
                            "pageGlowC": "#502aff14",
                            "panel": "#ffffffd1",
                            "panel2": "#ffffffb3",
                            "panel3": "#ffffffe8",
                            "mediaScrim": "#edf6ffbd",
                            "line": "#425d7c33",
                            "lineStrong": "#28a1da6b",
                            "text": "#121c2b",
                            "muted": "#5d6e82",
                            "subtle": "#778699",
                            "cyan": "#28c7ff",
                            "pink": "#ff3c7d",
                            "purple": "#b466ff",
                            "green": "#55e18d",
                            "warning": "#ffd166",
                        },
                    },
                }
            ),
        )
    archive_bytes.seek(0)

    response = client.post(
        "/api/themes/import/zip",
        files={"file": ("zip-theme.zip", archive_bytes.getvalue(), "application/zip")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["activeThemeId"] == "zip-theme"
    assert any(
        theme["id"] == "zip-theme" for theme in payload["weebarr"]["theme"]["themes"]
    )


def test_manual_automation_scan_requests_enabled_missing_buckets(tmp_path, monkeypatch):
    calls = []

    async def fake_seasonal_anime(self, season, year, per_page=48):
        assert season == "SPRING"
        assert year == 2026
        return {
            "items": [
                {
                    "id": 101,
                    "title": "Witch Hat Atelier",
                    "bucket": "S-Tier",
                    "seerr": {
                        "state": "missing",
                        "label": "Missing",
                        "requestable": True,
                        "tmdbId": 196950,
                    },
                },
                {
                    "id": 202,
                    "title": "Re:ZERO Season 4",
                    "bucket": "Canon",
                    "seerr": {
                        "state": "season_missing",
                        "label": "Season Missing",
                        "requestable": True,
                        "tmdbId": 65942,
                        "requestSeasons": [4],
                    },
                },
                {
                    "id": 303,
                    "title": "Already Requested",
                    "bucket": "Canon",
                    "seerr": {
                        "state": "requested",
                        "label": "Requested",
                        "requestable": False,
                        "tmdbId": 777,
                    },
                },
                {
                    "id": 404,
                    "title": "Filler Pick",
                    "bucket": "Filler",
                    "seerr": {
                        "state": "missing",
                        "label": "Missing",
                        "requestable": True,
                        "tmdbId": 888,
                    },
                },
            ],
            "stats": {
                "total": 4,
                "requestable": 3,
                "requested": 1,
            },
        }

    def fake_current_season(self):
        return ("SPRING", 2026)

    async def fake_request_in_seerr(self, media_id, title, tvdb_id=None, seasons=None):
        calls.append({"media_id": media_id, "title": title, "seasons": seasons})
        return {"success": True, "sentSeasons": seasons or []}

    monkeypatch.setattr(
        services_module.WeebarrService, "seasonal_anime", fake_seasonal_anime
    )
    monkeypatch.setattr(
        services_module.WeebarrService, "current_season", fake_current_season
    )
    monkeypatch.setattr(
        services_module.WeebarrService, "request_in_seerr", fake_request_in_seerr
    )

    client = authenticated_client(
        tmp_path,
        seerr_base_url="https://seerr.example.test",
        seerr_api_key="abc123",
        automation_enabled_buckets={
            "s_tier": True,
            "canon": True,
            "bingeable": False,
            "filler": False,
        },
    )

    response = client.post(
        "/api/automation/scan", json={"season": "SPRING", "year": 2026}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] == 3
    assert payload["eligible"] == 2
    assert payload["requested"] == 2
    assert payload["skipped"] == 1
    assert payload["failed"] == 0
    assert {call["title"] for call in calls} == {
        "Witch Hat Atelier",
        "Re:ZERO Season 4",
    }
    assert calls[1]["seasons"] == [4]


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
    assert service._source_audio(shaped["countryOfOrigin"])["fallbackLabel"] == "EN Sub"


def test_resolve_audio_uses_en_sub_fallback_when_jikan_lookup_fails(monkeypatch):
    service = WeebarrService(Settings(audio_lookup_enabled=True))

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            raise services_module.httpx.RequestError("rate limited", request=None)

    monkeypatch.setattr(services_module.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(service._resolve_audio({"malId": 2, "countryOfOrigin": "JP"}))

    assert result["label"] == "EN Sub"
    assert result["state"] == "ja_only"
    assert result["confidence"] == "lookup_failed"


def test_anime_characters_returns_shaped_payload(monkeypatch):
    service = WeebarrService(Settings())

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "Media": {
                        "siteUrl": "https://anilist.co/anime/178701",
                        "characters": {
                            "pageInfo": {"total": 28, "hasNextPage": True},
                            "edges": [
                                {
                                    "role": "MAIN",
                                    "node": {
                                        "id": 1,
                                        "siteUrl": "https://anilist.co/character/1",
                                        "name": {
                                            "full": "Natsuki Subaru",
                                            "native": "ナツキ・スバル",
                                        },
                                        "image": {
                                            "large": "https://img.example/subaru.jpg"
                                        },
                                    },
                                    "voiceActors": [
                                        {
                                            "id": 11,
                                            "siteUrl": "https://anilist.co/staff/11",
                                            "languageV2": "Japanese",
                                            "name": {
                                                "full": "Yusuke Kobayashi",
                                                "native": "小林 裕介",
                                            },
                                            "image": {
                                                "large": "https://img.example/yusuke.jpg"
                                            },
                                        },
                                        {
                                            "id": 12,
                                            "siteUrl": "https://anilist.co/staff/12",
                                            "languageV2": "English",
                                            "name": {
                                                "full": "Sean Chiplock",
                                                "native": "",
                                            },
                                            "image": {
                                                "medium": "https://img.example/sean.jpg"
                                            },
                                        },
                                    ],
                                }
                            ],
                        },
                    }
                }
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            assert url == services_module.ANILIST_URL
            assert json["variables"]["id"] == 178701
            return FakeResponse()

    monkeypatch.setattr(services_module.httpx, "AsyncClient", FakeAsyncClient)

    payload = asyncio.run(service.anime_characters(178701))

    assert payload["shown"] == 1
    assert payload["total"] == 28
    assert payload["hasMore"] is True
    assert payload["siteUrl"] == "https://anilist.co/anime/178701"
    assert payload["characters"][0]["role"] == "Main"
    assert payload["characters"][0]["voiceActors"][1]["language"] == "English"
    assert (
        payload["characters"][0]["voiceActors"][1]["image"]
        == "https://img.example/sean.jpg"
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

    new_client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                public_url="https://weebarr.example.test",
            )
        )
    )
    unauthorized = new_client.get("/api/config")
    assert unauthorized.status_code == 401


def test_anime_characters_endpoint_returns_payload(tmp_path, monkeypatch):
    client = authenticated_client(tmp_path)

    async def fake_anime_characters(self, anime_id):
        assert anime_id == 178701
        return {
            "characters": [
                {
                    "id": 1,
                    "name": "Natsuki Subaru",
                    "nativeName": "ナツキ・スバル",
                    "role": "Main",
                    "siteUrl": "https://anilist.co/character/1",
                    "image": "https://img.example/subaru.jpg",
                    "voiceActors": [],
                }
            ],
            "shown": 1,
            "total": 1,
            "hasMore": False,
            "siteUrl": "https://anilist.co/anime/178701",
        }

    monkeypatch.setattr(WeebarrService, "anime_characters", fake_anime_characters)

    response = client.get("/api/anime/178701/characters")

    assert response.status_code == 200
    payload = response.json()
    assert payload["shown"] == 1
    assert payload["characters"][0]["name"] == "Natsuki Subaru"


def test_setup_rate_limit_returns_429(tmp_path):
    client = TestClient(
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                setup_rate_limit_attempts=1,
                setup_rate_limit_window_seconds=300,
            )
        )
    )

    first = client.post(
        "/api/setup/access",
        json={
            "username": "",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )
    second = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )

    assert first.status_code == 400
    assert second.status_code == 429
    assert second.headers["retry-after"]


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


def test_local_login_rate_limit_returns_429(tmp_path):
    client = TestClient(
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                auth_mode="local",
                auth_username="adminuser",
                auth_password="example-password",
                session_secret="example-session-secret",
                login_rate_limit_attempts=2,
                login_rate_limit_window_seconds=300,
            )
        )
    )

    first = client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "wrong-password",
            "next": "/seasonal",
        },
    )
    second = client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "wrong-password",
            "next": "/seasonal",
        },
    )
    third = client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "wrong-password",
            "next": "/seasonal",
        },
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429
    assert third.headers["retry-after"]


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
    store = SettingsStore(
        Settings(
            config_path=str(config_path),
            public_url="https://weebarr.example.test",
        )
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
                public_url="https://weebarr.example.test",
            )
        )
    )

    login_page = client.get("/login")

    assert login_page.status_code == 200
    assert "Continue with Plex" in login_page.text
    assert "Username" not in login_page.text
    assert "Password" not in login_page.text


def test_authenticated_session_can_add_local_account_and_offer_both_login_paths(
    tmp_path,
):
    client = authenticated_client(
        tmp_path,
        base_url="https://weebarr.example.test",
        public_url="https://weebarr.example.test",
        plex_allowed_users=["admin@example.invalid"],
    )

    response = client.put(
        "/api/settings/access/local",
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

    login_page = TestClient(
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                public_url="https://weebarr.example.test",
                plex_allowed_users=["admin@example.invalid"],
            )
        ),
        base_url="https://weebarr.example.test",
    ).get("/login")
    assert login_page.status_code == 200
    assert "Continue with Plex" in login_page.text
    assert "Username" in login_page.text
    assert "Password" in login_page.text


def test_automation_api_key_cannot_create_local_account(tmp_path):
    config_path = tmp_path / "weebarr.json"
    store = SettingsStore(
        Settings(
            config_path=str(config_path),
            app_api_key="example-automation-token",
            public_url="https://weebarr.example.test",
        )
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
                public_url="https://weebarr.example.test",
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

    assert response.status_code == 403
    assert (
        response.json()["detail"] == "Automation API keys cannot access this endpoint."
    )


def test_plex_auth_config_requires_public_url_at_startup(tmp_path):
    with pytest.raises(
        RuntimeError,
        match="WEEBARR_PUBLIC_URL is required when Plex authentication is enabled.",
    ):
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                session_secret="example-plex-session-secret",
                plex_allowed_users=["admin@example.invalid"],
            )
        )


def test_plex_setup_start_requires_explicit_public_url(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="http://localhost",
    )

    response = client.get("/auth/plex/start?setup=1", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/setup?error=plex_public_url_required"


def test_https_public_url_marks_session_cookie_secure(tmp_path):
    client = TestClient(
        create_app(
            Settings(
                config_path=str(tmp_path / "weebarr.json"),
                auth_mode="local",
                auth_username="adminuser",
                auth_password="example-password",
                session_secret="example-session-secret",
                public_url="https://weebarr.example.test",
            )
        ),
        base_url="https://weebarr.example.test",
    )

    response = client.post(
        "/api/auth/login",
        json={
            "username": "adminuser",
            "password": "example-password",
            "next": "/seasonal",
        },
    )

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_plex_setup_start_uses_explicit_public_url_for_callback(tmp_path, monkeypatch):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                public_url="https://weebarr.example.test",
            )
        ),
        base_url="https://localhost",
    )

    async def fake_create_plex_pin(_settings):
        return {"id": 123, "code": "example-pin-code"}

    monkeypatch.setattr(main_module, "create_plex_pin", fake_create_plex_pin)

    response = client.get("/auth/plex/start?setup=1", follow_redirects=False)

    assert response.status_code in {302, 307}
    location = response.headers["location"]
    assert location.startswith("https://app.plex.tv/auth#?")
    assert (
        "forwardUrl=https%3A%2F%2Fweebarr.example.test%2Fauth%2Fplex%2Fcallback"
        in location
    )
    assert "code=example-pin-code" in location


def test_plex_setup_claims_single_admin_account(tmp_path, monkeypatch):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                public_url="https://weebarr.example.test",
            )
        ),
        base_url="https://localhost",
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

    new_client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                public_url="https://weebarr.example.test",
            )
        )
    )
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
    assert "Setup is blocked from this address." in blocked_page.text

    blocked_api = client.get("/api/setup/status")
    assert blocked_api.status_code == 403
    assert "trusted bootstrap path" in blocked_api.json()["detail"]


def test_spoofed_forwarded_headers_cannot_bypass_setup_lock(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(Settings(config_path=str(config_path))),
        base_url="https://weebarr.example.test",
    )
    spoofed_headers = {
        "Host": "localhost",
        "X-Forwarded-Host": "localhost",
        "X-Forwarded-For": "127.0.0.1",
        "X-Real-IP": "127.0.0.1",
    }

    blocked_page = client.get("/setup", headers=spoofed_headers)
    blocked_setup = client.post(
        "/api/setup/access",
        headers=spoofed_headers,
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )
    blocked_plex_start = client.get(
        "/auth/plex/start?setup=1",
        headers=spoofed_headers,
        follow_redirects=False,
    )
    blocked_plex_callback = client.get(
        "/auth/plex/callback",
        headers=spoofed_headers,
        follow_redirects=False,
    )

    assert blocked_page.status_code == 403
    assert blocked_setup.status_code == 403
    assert blocked_plex_start.status_code == 403
    assert blocked_plex_callback.status_code == 403


def test_public_setup_requires_bootstrap_token_for_remote_claim(tmp_path):
    config_path = tmp_path / "weebarr.json"
    client = TestClient(
        create_app(
            Settings(
                config_path=str(config_path),
                bootstrap_token="claim-this-instance",
            )
        ),
        base_url="https://weebarr.example.test",
    )

    blocked = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )
    assert blocked.status_code == 403

    allowed_page = client.get("/setup?bootstrap=claim-this-instance")
    assert allowed_page.status_code == 200

    allowed_setup = client.post(
        "/api/setup/access",
        json={
            "username": "adminuser",
            "password": "example-password",
            "confirmPassword": "example-password",
        },
    )

    assert allowed_setup.status_code == 200
    assert allowed_setup.json()["mode"] == "local"


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


def test_request_in_seerr_uses_seerr_anime_defaults_when_no_force_overrides(
    monkeypatch,
):
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
            seerr_api_key="secret",
        )
    )
    captured: dict[str, object] = {}

    async def fake_resolve_request_seasons(_media_id: int, _seasons):
        return [1]

    async def fake_sonarr_defaults():
        return {
            "serverId": 0,
            "profileId": 7,
            "rootFolder": "P:\\Media\\3. Anime",
            "languageProfileId": 1,
            "tags": [2],
            "seriesType": "standard",
        }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers

            class Response:
                status_code = 201
                content = b"{}"

                @staticmethod
                def json():
                    return {"id": 1}

            return Response()

    service._resolve_request_seasons = fake_resolve_request_seasons  # type: ignore[method-assign]
    service._sonarr_defaults = fake_sonarr_defaults  # type: ignore[method-assign]
    monkeypatch.setattr(services_module.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        service.request_in_seerr(
            media_id=196950,
            title="Witch Hat Atelier",
            tvdb_id=418666,
            seasons="all",
        )
    )

    assert result["success"] is True
    payload = captured["json"]
    assert payload == {
        "mediaType": "tv",
        "mediaId": 196950,
        "is4k": False,
        "seasons": [1],
        "tvdbId": 418666,
        "profileId": 7,
        "rootFolder": "P:\\Media\\3. Anime",
        "languageProfileId": 1,
        "tags": [2],
    }


def test_request_in_seerr_can_force_series_type_and_quality_profile(monkeypatch):
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
            seerr_api_key="secret",
            seerr_force_quality_profile=True,
            seerr_profile_id=22,
            seerr_series_type="standard",
        )
    )
    captured: dict[str, object] = {}

    async def fake_resolve_request_seasons(_media_id: int, _seasons):
        return [1]

    async def fake_sonarr_servers(*_args, **_kwargs):
        return [
            {"id": 8, "name": "Anime Absolute", "animeSeriesType": "anime"},
            {
                "id": 4,
                "name": "Anime Standard",
                "animeSeriesType": "standard",
                "isDefault": True,
                "activeAnimeDirectory": "P:\\Media\\3. Anime",
                "activeAnimeLanguageProfileId": 1,
                "animeTags": [2],
            },
        ]

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["json"] = json

            class Response:
                status_code = 201
                content = b"{}"

                @staticmethod
                def json():
                    return {"id": 2}

            return Response()

    service._resolve_request_seasons = fake_resolve_request_seasons  # type: ignore[method-assign]
    service._sonarr_servers = fake_sonarr_servers  # type: ignore[method-assign]
    monkeypatch.setattr(services_module.httpx, "AsyncClient", FakeAsyncClient)

    asyncio.run(
        service.request_in_seerr(
            media_id=196950,
            title="Witch Hat Atelier",
            tvdb_id=418666,
            seasons="all",
        )
    )

    payload = captured["json"]
    assert payload["serverId"] == 4
    assert payload["profileId"] == 22
    assert payload["tvdbId"] == 418666
    assert payload["rootFolder"] == "P:\\Media\\3. Anime"
    assert payload["languageProfileId"] == 1
    assert payload["tags"] == [2]


def test_request_in_seerr_omits_default_server_id_zero_when_forcing_series_type(
    monkeypatch,
):
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
            seerr_api_key="secret",
            seerr_series_type="standard",
        )
    )
    captured: dict[str, object] = {}

    async def fake_resolve_request_seasons(_media_id: int, _seasons):
        return [1]

    async def fake_sonarr_servers(*_args, **_kwargs):
        return [
            {
                "id": 0,
                "name": "Default Sonarr",
                "animeSeriesType": "standard",
                "activeAnimeProfileId": 7,
                "activeAnimeDirectory": "P:\\Media\\3. Anime",
                "activeAnimeLanguageProfileId": 1,
                "animeTags": [2],
                "isDefault": True,
            }
        ]

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["json"] = json

            class Response:
                status_code = 201
                content = b"{}"

                @staticmethod
                def json():
                    return {"id": 3}

            return Response()

    service._resolve_request_seasons = fake_resolve_request_seasons  # type: ignore[method-assign]
    service._sonarr_servers = fake_sonarr_servers  # type: ignore[method-assign]
    monkeypatch.setattr(services_module.httpx, "AsyncClient", FakeAsyncClient)

    asyncio.run(
        service.request_in_seerr(
            media_id=196950,
            title="Witch Hat Atelier",
            tvdb_id=418666,
            seasons="all",
        )
    )

    payload = captured["json"]
    assert "serverId" not in payload
    assert payload["profileId"] == 7
    assert payload["rootFolder"] == "P:\\Media\\3. Anime"
    assert payload["languageProfileId"] == 1
    assert payload["tags"] == [2]


def test_request_in_seerr_rejects_mismatched_forced_server_series_type(monkeypatch):
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
            seerr_api_key="secret",
            seerr_sonarr_server_id=8,
            seerr_series_type="standard",
        )
    )

    async def fake_resolve_request_seasons(_media_id: int, _seasons):
        return [1]

    async def fake_sonarr_servers(*_args, **_kwargs):
        return [{"id": 8, "name": "Anime Absolute", "animeSeriesType": "anime"}]

    service._resolve_request_seasons = fake_resolve_request_seasons  # type: ignore[method-assign]
    service._sonarr_servers = fake_sonarr_servers  # type: ignore[method-assign]

    with pytest.raises(services_module.HTTPException) as exc:
        asyncio.run(
            service.request_in_seerr(
                media_id=196950,
                title="Witch Hat Atelier",
                tvdb_id=418666,
                seasons="all",
            )
        )

    assert exc.value.status_code == 400
    assert "uses anime series type 'anime', not 'standard'" in exc.value.detail


def test_request_in_seerr_rejects_forced_series_type_when_seerr_hides_it():
    service = WeebarrService(
        Settings(
            seerr_base_url="https://seerr.example.test",
            seerr_api_key="secret",
            seerr_series_type="standard",
        )
    )

    selected_server = {"id": 0, "name": "Default Sonarr", "isDefault": True}

    with pytest.raises(services_module.HTTPException) as exc:
        service._resolve_request_server([selected_server])

    assert exc.value.status_code == 400
    assert "does not expose an Anime Series Type" in exc.value.detail
