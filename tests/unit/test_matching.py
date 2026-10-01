import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import create_app
from src.weebarr.services import WeebarrService
from src.weebarr.settings import Settings, SettingsStore, match_server_key


def matching_settings(tmp_path, backend="seerr", **overrides):
    values = {
        "config_path": str(tmp_path / "weebarr.json"),
        "auth_mode": "local",
        "auth_username": "match-admin",
        "auth_password": "example-password",
        "session_secret": "example-session-secret",
        "request_backend": backend,
        "request_backend_setup_complete": True,
        "seerr_base_url": "https://seerr.example.test/prefix",
        "seerr_api_key": "example-seerr-key",
        "sonarr_base_url": "https://sonarr.example.test/sonarr",
        "sonarr_api_key": "example-sonarr-key",
        "sonarr_root_folder_path": "/tv",
        "sonarr_quality_profile_id": 1,
        "sonarr_series_type": "anime",
    }
    values.update(overrides)
    return Settings(**values)


def matching_client(tmp_path, backend="seerr", **overrides):
    settings = matching_settings(tmp_path, backend, **overrides)
    client = TestClient(create_app(settings))
    login = client.post(
        "/api/auth/login",
        json={"username": settings.auth_username, "password": settings.auth_password},
    )
    assert login.status_code == 200
    return client


def match_anime():
    return {
        "id": 42,
        "malId": 123,
        "title": "Original anime season 2",
        "startYear": 2026,
        "installment": {"seasonNumber": 2, "label": "Season 2"},
    }


def seerr_details(media_id=777):
    return {
        "id": media_id,
        "name": "Canonical TV series",
        "seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}],
        "mediaInfo": {"status": 5, "seasons": [{"seasonNumber": 1, "status": 5}]},
    }


def test_external_links_preserve_base_paths_and_escape_segments(tmp_path):
    service = WeebarrService(matching_settings(tmp_path))
    assert (
        service._external_url("seerr", 777)
        == "https://seerr.example.test/prefix/tv/777"
    )
    assert service._external_url("sonarr", 888) == (
        "https://sonarr.example.test/sonarr/add/new?term=tvdb%3A888"
    )
    assert (
        service._external_url("sonarr", 888, title_slug="series /?&", in_library=True)
        == "https://sonarr.example.test/sonarr/series/series%20%2F%3F%26"
    )
    assert service._external_url("seerr", 0) is None


def test_external_links_omit_connection_credentials_and_queries(tmp_path):
    service = WeebarrService(
        matching_settings(
            tmp_path,
            seerr_base_url="https://user:password@seerr.example.test:8443/seerr/?token=private#fragment",
        )
    )
    assert service._external_url("seerr", 777) == (
        "https://seerr.example.test:8443/seerr/tv/777"
    )


def test_saved_matches_survive_restart_and_are_server_and_backend_specific(tmp_path):
    settings = matching_settings(tmp_path)
    store = SettingsStore(settings)
    store.save_manual_match("seerr", settings.seerr_base_url, 42, 777)
    store.save_manual_match("sonarr", settings.sonarr_base_url, 42, 888)
    restarted = SettingsStore(settings)
    service = WeebarrService(restarted.get)
    assert service._manual_match_id(match_anime(), "seerr") == 777
    assert service._manual_match_id(match_anime(), "sonarr") == 888
    changed_server = WeebarrService(
        replace(restarted.get(), seerr_base_url="https://different.example.test/prefix")
    )
    assert changed_server._manual_match_id(match_anime(), "seerr") is None
    assert changed_server._manual_match_id({"id": 43}, "sonarr") is None
    restarted.save_manual_match("seerr", settings.seerr_base_url, 42, None)
    assert service._manual_match_id(match_anime(), "seerr") is None
    assert service._manual_match_id(match_anime(), "sonarr") == 888
    payload = json.loads((tmp_path / "weebarr.json").read_text())
    assert (
        payload["manual_matches"]["sonarr"][match_server_key(settings.sonarr_base_url)][
            "42"
        ]
        == 888
    )


def test_server_identity_normalizes_host_default_port_and_trailing_slash():
    assert match_server_key("https://SEERR.example.test:443/path/") == match_server_key(
        "https://seerr.example.test/path"
    )
    assert match_server_key("https://seerr.example.test/path") != match_server_key(
        "https://seerr.example.test/other"
    )


def test_manual_match_precedes_automatic_ids_and_preserves_season_context(
    tmp_path, monkeypatch
):
    settings = matching_settings(tmp_path, strict_monitoring=True)
    store = SettingsStore(settings)
    store.save_manual_match("seerr", settings.seerr_base_url, 42, 777)
    service = WeebarrService(store.get)

    async def details(media_id):
        assert media_id == 777
        return seerr_details(media_id)

    async def forbidden(*args):
        pytest.fail("Automatic matching must not replace an explicit mapping")

    monkeypatch.setattr(service, "_seerr_tv_details", details)
    monkeypatch.setattr(service, "_ids_moe_tmdb_id", forbidden)
    monkeypatch.setattr(service, "_seerr_search", forbidden)
    state = asyncio.run(service.resolve_request_state(match_anime()))
    assert state["manualMatch"] is True
    assert state["tmdbId"] == 777
    assert state["state"] == "season_missing"
    assert state["requestSeasons"] == [2]
    assert state["externalUrl"].endswith("/prefix/tv/777")


@pytest.mark.parametrize("failure", ["missing", "unreachable", "malformed"])
def test_stale_manual_mapping_fails_closed(tmp_path, monkeypatch, failure):
    settings = matching_settings(tmp_path)
    store = SettingsStore(settings)
    store.save_manual_match("seerr", settings.seerr_base_url, 42, 777)
    service = WeebarrService(store.get)

    async def details(media_id):
        if failure == "unreachable":
            raise httpx.ConnectError("unavailable")
        if failure == "malformed":
            return {"id": media_id, "mediaInfo": "invalid metadata"}
        return {"id": 999, "name": "Different show"}

    async def forbidden(*args):
        pytest.fail("Stale mappings must not silently use automatic matches")

    monkeypatch.setattr(service, "_seerr_tv_details", details)
    monkeypatch.setattr(service, "_ids_moe_tmdb_id", forbidden)
    state = asyncio.run(service.resolve_request_state(match_anime()))
    assert state["state"] == "missing_mapping"
    assert state["manualMatch"] is True
    assert state["manualMatchStale"] is True
    assert state["requestable"] is False
    assert "tmdbId" not in state


def test_seerr_search_filters_movies_and_deduplicates_ids(tmp_path, monkeypatch):
    service = WeebarrService(matching_settings(tmp_path))

    async def search(query):
        assert query == "A title"
        return [
            {"id": 1, "mediaType": "movie", "title": "Movie"},
            {
                "id": 777,
                "mediaType": "tv",
                "name": "Series",
                "firstAirDate": "2026-01-01",
                "mediaInfo": {"status": 5},
            },
            {"id": 777, "mediaType": "tv", "name": "Duplicate"},
        ]

    monkeypatch.setattr(service, "_seerr_search", search)
    payload = asyncio.run(service.search_matches("seerr", "A title"))
    assert payload["backend"] == "seerr"
    assert len(payload["results"]) == 1
    assert payload["results"][0] == {
        "mediaId": 777,
        "title": "Series",
        "year": 2026,
        "overview": "",
        "posterUrl": None,
        "externalUrl": "https://seerr.example.test/prefix/tv/777",
        "inLibrary": True,
    }


def test_sonarr_search_and_exact_manual_selection_use_library_series(
    tmp_path, monkeypatch
):
    service = WeebarrService(matching_settings(tmp_path, "sonarr"))
    lookup_series = {
        "tvdbId": 888,
        "title": "Library series",
        "year": 2026,
        "seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}],
    }
    library_series = {
        **lookup_series,
        "id": 9,
        "titleSlug": "library-series",
        "images": [
            {
                "coverType": "poster",
                "remoteUrl": "https://images.example.test/poster.jpg",
            }
        ],
    }

    async def lookup(term):
        return [lookup_series, {"tvdbId": 889, "title": "Outside library"}]

    async def library():
        return [library_series]

    async def details(series_id):
        assert series_id == 9
        return library_series

    monkeypatch.setattr(service, "_sonarr_lookup", lookup)
    monkeypatch.setattr(service, "_sonarr_series", library)
    monkeypatch.setattr(service, "_sonarr_series_details", details)
    search = asyncio.run(service.search_matches("sonarr", "Series"))
    assert search["results"][0]["inLibrary"] is True
    assert search["results"][0]["externalUrl"].endswith("/sonarr/series/library-series")
    assert search["results"][1]["inLibrary"] is False
    assert search["results"][1]["externalUrl"].endswith("/add/new?term=tvdb%3A889")
    state = asyncio.run(service.match_candidate_state(match_anime(), "sonarr", 888))
    assert state["seriesId"] == 9
    assert state["tvdbId"] == 888
    assert state["manualMatch"] is True
    assert state["requestSeasons"] == [2]


def test_sonarr_exact_lookup_does_not_fall_back_to_wrong_title(tmp_path, monkeypatch):
    service = WeebarrService(matching_settings(tmp_path, "sonarr"))
    terms = []

    async def lookup(term):
        terms.append(term)
        return [{"tvdbId": 999, "title": "Exact title but wrong show"}]

    async def library():
        return []

    monkeypatch.setattr(service, "_sonarr_lookup", lookup)
    monkeypatch.setattr(service, "_sonarr_series", library)
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.match_candidate_state(match_anime(), "sonarr", 888))
    assert error.value.status_code == 404
    candidate, score = asyncio.run(
        service._lookup_sonarr_series("Exact title but wrong show", 888)
    )
    assert candidate is None
    assert score == 0
    assert terms == ["tvdb:888", "tvdb:888"]


def test_sonarr_internal_id_collision_does_not_override_tvdb_selection(
    tmp_path, monkeypatch
):
    service = WeebarrService(matching_settings(tmp_path, "sonarr"))

    async def library():
        return [{"id": 888, "tvdbId": 999}, {"id": 9, "tvdbId": 888}]

    monkeypatch.setattr(service, "_sonarr_series", library)
    selected = asyncio.run(service._find_existing_sonarr_series(888, 888))
    assert selected == {"id": 9, "tvdbId": 888}


def test_selection_endpoints_validate_and_persist_canonical_match(
    tmp_path, monkeypatch
):
    calls = []

    async def canonical(self, anime_id):
        assert anime_id == 42
        calls.append("canonical")
        return match_anime()

    async def details(self, media_id):
        calls.append(media_id)
        return seerr_details(media_id)

    async def automatic(self, anime):
        assert self._manual_match_id(anime, "seerr") is None
        return {"backend": "seerr", "state": "missing_mapping", "requestable": False}

    monkeypatch.setattr(WeebarrService, "anime_match_context", canonical)
    monkeypatch.setattr(WeebarrService, "_seerr_tv_details", details)
    monkeypatch.setattr(WeebarrService, "resolve_request_state", automatic)
    client = matching_client(tmp_path)
    saved = client.put("/api/anime/42/match", json={"backend": "seerr", "mediaId": 777})
    assert saved.status_code == 200
    state = saved.json()["requestState"]
    assert state["title"] == "Canonical TV series"
    assert state["manualMatch"] is True
    assert state["targetSeason"] == 2
    store = SettingsStore(matching_settings(tmp_path))
    assert WeebarrService(store.get)._manual_match_id(match_anime(), "seerr") == 777
    cleared = client.delete("/api/anime/42/match?backend=seerr")
    assert cleared.status_code == 200
    assert cleared.json()["requestState"]["state"] == "missing_mapping"
    assert "manualMatch" not in cleared.json()["requestState"]
    assert calls == ["canonical", 777, "canonical"]
    assert SettingsStore(matching_settings(tmp_path)).get().manual_matches == {}


@pytest.mark.parametrize("media_id", [0, -1, True, "777"])
def test_save_rejects_invalid_media_ids(tmp_path, media_id):
    client = matching_client(tmp_path)
    assert (
        client.put(
            "/api/anime/42/match", json={"backend": "seerr", "mediaId": media_id}
        ).status_code
        == 422
    )
    assert not (tmp_path / "weebarr.json").exists()


def test_match_endpoints_reject_stale_backend_and_unconfigured_server(tmp_path):
    client = matching_client(tmp_path)
    assert (
        client.get("/api/matches/search?query=Series&backend=sonarr").status_code == 409
    )
    assert (
        client.put(
            "/api/anime/42/match", json={"backend": "sonarr", "mediaId": 888}
        ).status_code
        == 409
    )
    assert client.delete("/api/anime/42/match?backend=sonarr").status_code == 409
    assert (
        client.get("/api/matches/search?query=%20%20&backend=seerr").status_code == 400
    )
    client = matching_client(tmp_path, seerr_api_key="")
    assert (
        client.get("/api/matches/search?query=Series&backend=seerr").status_code == 503
    )


@pytest.mark.parametrize(
    "method,url,body",
    [
        ("get", "/api/matches/search?query=Series&backend=seerr", None),
        ("put", "/api/anime/42/match", {"backend": "seerr", "mediaId": 777}),
        ("delete", "/api/anime/42/match?backend=seerr", None),
    ],
)
def test_match_endpoints_require_session_and_reject_automation_api_keys(
    tmp_path, method, url, body
):
    settings = matching_settings(tmp_path, app_api_key="example-automation-key")
    client = TestClient(create_app(settings))
    kwargs = {"json": body} if body else {}
    assert getattr(client, method)(url, **kwargs).status_code == 401
    rejected = getattr(client, method)(
        url, headers={"X-Api-Key": settings.app_api_key}, **kwargs
    )
    assert rejected.status_code == 403


def test_failed_selection_does_not_replace_existing_saved_match(tmp_path, monkeypatch):
    settings = matching_settings(tmp_path)
    store = SettingsStore(settings)
    store.save_manual_match("seerr", settings.seerr_base_url, 42, 777)

    async def canonical(self, anime_id):
        return match_anime()

    async def details(self, media_id):
        return {"id": 999, "name": "Wrong backend item"}

    monkeypatch.setattr(WeebarrService, "anime_match_context", canonical)
    monkeypatch.setattr(WeebarrService, "_seerr_tv_details", details)
    client = matching_client(tmp_path)
    assert (
        client.put(
            "/api/anime/42/match", json={"backend": "seerr", "mediaId": 888}
        ).status_code
        == 404
    )
    store.reload()
    assert WeebarrService(store.get)._manual_match_id(match_anime(), "seerr") == 777


def test_manual_request_rejects_stale_browser_selection(tmp_path, monkeypatch):
    settings = matching_settings(tmp_path)
    SettingsStore(settings).save_manual_match("seerr", settings.seerr_base_url, 42, 777)

    async def forbidden(*args, **kwargs):
        pytest.fail("Stale selected IDs must not reach the request backend")

    monkeypatch.setattr(WeebarrService, "request_title", forbidden)
    client = matching_client(tmp_path)
    response = client.post(
        "/api/request", json={"animeId": 42, "mediaId": 888, "title": "Old selection"}
    )
    assert response.status_code == 409
