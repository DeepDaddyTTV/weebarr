#!/usr/bin/env python3
"""Weebarr entry point."""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import json
import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from threading import RLock
from time import time
from typing import Any, Optional, Union
from urllib.parse import quote
from zipfile import BadZipFile, ZipFile

import httpx
import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.version import __version__
from src.weebarr.auth import (
    DEFAULT_REDIRECT_PATH,
    AuthUser,
    build_plex_auth_url,
    build_session_user_payload,
    create_plex_pin,
    fetch_plex_pin,
    fetch_plex_user,
    generate_api_key,
    generate_session_secret,
    hash_secret,
    masked_preview,
    plex_auth_user,
    plex_user_allowed,
    verify_api_key,
    verify_bootstrap_token,
    verify_local_credentials,
)
from src.weebarr.services import WeebarrService
from src.weebarr.settings import (
    AUTOMATION_BUCKET_KEYS,
    DEFAULT_AUTOMATION_BUCKETS,
    DEFAULT_AUTOMATION_SCAN_INTERVAL_DAYS,
    DEFAULT_AUTOMATION_SCAN_INTERVAL_HOURS,
    DEFAULT_THEME_LIBRARY,
    Settings,
    SettingsStore,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("weebarr")

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))

SETUP_PROXY_INDICATOR_HEADERS = (
    "CF-Connecting-IP",
    "Forwarded",
    "X-Forwarded-For",
    "X-Forwarded-Host",
    "X-Forwarded-Port",
    "X-Forwarded-Proto",
    "X-Real-IP",
)
API_KEY_ALLOWED_PATHS = {
    "/api/health",
    "/api/seasonal",
    "/api/request",
}


class RequestPayload(BaseModel):
    """Payload accepted by Weebarr before forwarding to Seerr."""

    model_config = ConfigDict(populate_by_name=True)

    media_id: int = Field(..., alias="mediaId")
    anime_id: Optional[int] = Field(default=None, alias="animeId")
    title: str
    tvdb_id: Optional[int] = Field(default=None, alias="tvdbId")
    season: Optional[str] = None
    year: Optional[int] = None
    seasons: Optional[Union[list[int], str]] = None
    options: Optional["SonarrRequestOptionsPayload"] = None


class SonarrRequestOptionsPayload(BaseModel):
    """Optional Sonarr Direct request controls."""

    model_config = ConfigDict(populate_by_name=True)

    selected_seasons: Optional[list[int]] = Field(
        default=None,
        alias="selectedSeasons",
    )
    monitor_mode: Optional[str] = Field(default=None, alias="monitorMode")
    search_on_add: Optional[bool] = Field(default=None, alias="searchOnAdd")
    season_folder: Optional[bool] = Field(default=None, alias="seasonFolder")


class ConnectionPayload(BaseModel):
    """Editable Seerr connection settings."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: Optional[str] = Field(default=None, alias="baseUrl")
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    request_seasons: Optional[str] = Field(default=None, alias="requestSeasons")
    sonarr_server_id: Optional[int] = Field(default=None, alias="sonarrServerId")
    profile_id: Optional[int] = Field(default=None, alias="profileId")
    force_quality_profile: Optional[bool] = Field(
        default=None,
        alias="forceQualityProfile",
    )
    series_type: Optional[str] = Field(default=None, alias="seriesType")
    root_folder: Optional[str] = Field(default=None, alias="rootFolder")
    language_profile_id: Optional[int] = Field(default=None, alias="languageProfileId")
    request_user_id: Optional[int] = Field(default=None, alias="requestUserId")
    tags: Optional[list[int]] = None


class SonarrConnectionPayload(BaseModel):
    """Editable Sonarr Direct settings."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: Optional[str] = Field(default=None, alias="baseUrl")
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    root_folder_path: Optional[str] = Field(default=None, alias="rootFolderPath")
    quality_profile_id: Optional[int] = Field(
        default=None,
        alias="qualityProfileId",
    )
    series_type: Optional[str] = Field(default=None, alias="seriesType")
    default_monitor_mode: Optional[str] = Field(
        default=None,
        alias="defaultMonitorMode",
    )
    default_search_on_add: Optional[bool] = Field(
        default=None,
        alias="defaultSearchOnAdd",
    )
    default_season_folder: Optional[bool] = Field(
        default=None,
        alias="defaultSeasonFolder",
    )
    language_profile_id: Optional[int] = Field(default=None, alias="languageProfileId")
    tags: Optional[list[int]] = None


class RequestSettingsPayload(BaseModel):
    """Editable request backend settings."""

    model_config = ConfigDict(populate_by_name=True)

    request_backend: Optional[str] = Field(default=None, alias="requestBackend")
    seerr: Optional[ConnectionPayload] = None
    sonarr: Optional[SonarrConnectionPayload] = None


class RequestBackendSelectionPayload(BaseModel):
    """First-run backend selection payload."""

    model_config = ConfigDict(populate_by_name=True)

    request_backend: Optional[str] = Field(default=None, alias="requestBackend")


class WeebarrSettingsPayload(BaseModel):
    """Editable Weebarr-local settings."""

    model_config = ConfigDict(populate_by_name=True)

    content_filter_mode: Optional[str] = Field(default=None, alias="contentFilterMode")
    strict_monitoring: Optional[bool] = Field(default=None, alias="strictMonitoring")
    automation: Optional[dict[str, Any]] = None
    theme: Optional[dict[str, Any]] = None
    automation_start_current_season: Optional[bool] = Field(
        default=None,
        alias="automationStartCurrentSeason",
    )


class AutomationScanPayload(BaseModel):
    """Manual automation scan payload."""

    model_config = ConfigDict(populate_by_name=True)

    season: Optional[str] = None
    year: Optional[int] = None
    force: bool = False


class ThemeImportUrlPayload(BaseModel):
    """Theme import from a direct URL."""

    url: str = ""


class LocalLoginPayload(BaseModel):
    """Username/password login payload for local auth mode."""

    username: str = ""
    password: str = ""
    next: Optional[str] = None


class AccessSetupPayload(BaseModel):
    """First-run access configuration payload."""

    model_config = ConfigDict(populate_by_name=True)

    username: str = ""
    password: str = ""
    confirm_password: str = Field(default="", alias="confirmPassword")


class LocalAccountPayload(BaseModel):
    """Payload for creating or updating the local account from Settings."""

    model_config = ConfigDict(populate_by_name=True)

    username: str = ""
    password: str = ""
    confirm_password: str = Field(default="", alias="confirmPassword")


class RateLimiter:
    """Minimal in-memory fixed-window limiter for sensitive auth/setup paths."""

    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._lock = RLock()
        self._windows: dict[str, tuple[float, int]] = {}

    def consume(self, key: str) -> int | None:
        """Record an attempt and return retry-after seconds when blocked."""

        now = time()
        with self._lock:
            window_started, count = self._windows.get(key, (now, 0))
            if now - window_started >= self.window_seconds:
                window_started, count = now, 0
            if count >= self.limit:
                retry_after = max(
                    1, int(self.window_seconds - max(0, now - window_started))
                )
                self._windows[key] = (window_started, count)
                return retry_after
            self._windows[key] = (window_started, count + 1)
        return None

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI app."""

    base_settings = settings or Settings.from_env()
    settings_store = SettingsStore(base_settings)
    initial_settings = settings_store.get()
    if (
        initial_settings.auth_enabled
        and not initial_settings.session_secret
        and not initial_settings.setup_required
    ):
        raise RuntimeError(
            "A session secret is required when Weebarr authentication is enabled."
        )
    if initial_settings.uses_plex_auth and not initial_settings.public_url:
        raise RuntimeError(
            "WEEBARR_PUBLIC_URL is required when Plex authentication is enabled."
        )
    service = WeebarrService(settings_store.get)
    asset_version = str(int(time()))
    session_secret = initial_settings.session_secret or generate_session_secret()
    login_rate_limiter = RateLimiter(
        limit=initial_settings.login_rate_limit_attempts,
        window_seconds=initial_settings.login_rate_limit_window_seconds,
    )
    setup_rate_limiter = RateLimiter(
        limit=initial_settings.setup_rate_limit_attempts,
        window_seconds=initial_settings.setup_rate_limit_window_seconds,
    )
    plex_rate_limiter = RateLimiter(
        limit=initial_settings.plex_rate_limit_attempts,
        window_seconds=initial_settings.plex_rate_limit_window_seconds,
    )

    @contextlib.asynccontextmanager
    async def automation_lifespan(app: FastAPI):
        async def automation_daemon() -> None:
            while True:
                await maybe_run_scheduled_automation()
                await asyncio.sleep(3600)

        app.state.automation_task = asyncio.create_task(automation_daemon())
        try:
            yield
        finally:
            task = getattr(app.state, "automation_task", None)
            app.state.automation_task = None
            if task is None:
                return
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="Weebarr",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        lifespan=automation_lifespan,
    )
    app.state.automation_lock = asyncio.Lock()
    app.state.automation_task = None

    app.mount(
        "/static",
        StaticFiles(directory=str(WEB_ROOT / "static")),
        name="static",
    )

    def current_settings() -> Settings:
        return settings_store.get()

    def sanitize_next_path(value: str | None) -> str:
        candidate = (value or "").strip()
        if not candidate.startswith("/") or candidate.startswith("//"):
            return DEFAULT_REDIRECT_PATH
        return candidate

    def current_auth_user(request: Request) -> AuthUser | None:
        return AuthUser.from_session(request.session.get("auth_user"))

    def set_auth_user(request: Request, user: AuthUser) -> None:
        request.session["auth_user"] = build_session_user_payload(user)
        request.session.pop("plex_pending", None)
        request.state.auth_user = user

    def clear_auth_session(request: Request) -> None:
        request.session.pop("auth_user", None)
        request.session.pop("plex_pending", None)
        request.state.auth_user = None

    def api_key_authorized(request: Request) -> bool:
        header_key = request.headers.get("X-API-Key", "").strip()
        bearer = request.headers.get("Authorization", "").strip()
        bearer_key = bearer[7:].strip() if bearer.lower().startswith("bearer ") else ""
        return verify_api_key(current_settings(), header_key) or verify_api_key(
            current_settings(), bearer_key
        )

    def bootstrap_token_authorized(request: Request) -> bool:
        if request.session.get("bootstrap_authorized") is True:
            return True

        settings_now = current_settings()
        if not settings_now.bootstrap_token_enabled:
            return False

        header_value = request.headers.get("X-Weebarr-Bootstrap-Token", "")
        bearer = request.headers.get("Authorization", "").strip()
        bearer_token = (
            bearer[7:].strip() if bearer.lower().startswith("bearer ") else ""
        )
        query_value = request.query_params.get("bootstrap", "")
        candidate = header_value or query_value or bearer_token
        if not verify_bootstrap_token(settings_now, candidate):
            return False
        request.session["bootstrap_authorized"] = True
        return True

    def api_key_path_allowed(path: str) -> bool:
        if path in API_KEY_ALLOWED_PATHS:
            return True
        if path.startswith("/api/anime/") and path.endswith("/characters"):
            parts = path.strip("/").split("/")
            return (
                len(parts) == 4
                and parts[0] == "api"
                and parts[1] == "anime"
                and parts[2].isdigit()
                and parts[3] == "characters"
            )
        return False

    def connection_summary() -> dict[str, Any]:
        return settings_store.connection_summary()

    def request_settings_summary() -> dict[str, Any]:
        return settings_store.request_settings_summary()

    def weebarr_summary() -> dict[str, Any]:
        return settings_store.weebarr_summary()

    def access_summary() -> dict[str, Any]:
        return settings_store.access_summary()

    def missing_request_backend_fields(settings_now: Settings) -> list[str]:
        if settings_now.active_request_backend == "sonarr":
            missing: list[str] = []
            if not settings_now.sonarr_base_url:
                missing.append("Sonarr Host")
            if not settings_now.sonarr_api_key:
                missing.append("API Key")
            if not settings_now.sonarr_root_folder_path:
                missing.append("Root Folder Path")
            if settings_now.sonarr_quality_profile_id is None:
                missing.append("Quality Profile ID")
            if settings_now.sonarr_series_type is None:
                missing.append("Series Type")
            return missing

        seerr_missing: list[str] = []
        if not settings_now.seerr_base_url:
            seerr_missing.append("Seerr Base URL")
        if not settings_now.seerr_api_key:
            seerr_missing.append("API Key")
        return seerr_missing

    def auth_summary(request: Request) -> dict[str, Any]:
        user = current_auth_user(request)
        settings_now = current_settings()
        if settings_now.uses_local_auth and settings_now.uses_plex_auth:
            access_copy = (
                "Single-admin access allows either the configured local account or "
                "the claimed Plex account."
            )
            signin_copy = "Username/password or Plex"
        elif settings_now.uses_plex_auth:
            access_copy = "Single-admin access is locked to the claimed Plex account."
            signin_copy = "Plex only"
        elif settings_now.uses_local_auth:
            access_copy = (
                "Single-admin access uses the configured local username and password."
            )
            signin_copy = "Username/password"
        else:
            access_copy = "Authentication has not been configured yet."
            signin_copy = "Setup required"
        return {
            "auth_enabled": settings_now.auth_enabled,
            "auth_mode": settings_now.effective_auth_mode,
            "plex_login_enabled": settings_now.plex_login_enabled,
            "local_login_enabled": settings_now.uses_local_auth,
            "auth_user_name": user.display_name if user else None,
            "auth_user_mode": user.mode if user else None,
            "auth_access_copy": access_copy,
            "auth_signin_copy": signin_copy,
        }

    def bucket_label_map() -> dict[str, str]:
        return {
            "s_tier": "S-Tier",
            "canon": "Canon",
            "bingeable": "Bingeable",
            "filler": "Filler",
        }

    def current_theme_summary() -> dict[str, Any]:
        theme_summary = weebarr_summary().get("theme")
        return theme_summary if isinstance(theme_summary, dict) else {}

    def save_imported_theme(manifest: dict[str, Any]) -> Settings:
        theme_id = str(manifest.get("id") or "").strip().lower()
        if not theme_id:
            raise HTTPException(
                status_code=400, detail="Theme manifest must include an id."
            )
        imported = dict(current_settings().theme_imports or {})
        imported[theme_id] = manifest
        try:
            return settings_store.save_weebarr(
                {
                    "theme_imports": imported,
                    "active_theme_id": theme_id,
                }
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def automation_due(settings_now: Settings) -> bool:
        if not settings_now.automation_enabled:
            return False
        last_scan = parse_timestamp(settings_now.automation_last_scan_at)
        if last_scan is None:
            return True
        return datetime.now(timezone.utc) - last_scan >= timedelta(
            days=settings_now.automation_scan_interval_days,
            hours=settings_now.automation_scan_interval_hours,
        )

    async def run_automation_scan(
        *,
        season: str | None = None,
        year: int | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        async with app.state.automation_lock:
            settings_now = current_settings()
            target_season, target_year = (
                (season.upper(), year)
                if season and year is not None
                else service.current_season()
            )
            enabled_buckets = settings_now.automation_enabled_buckets or dict(
                DEFAULT_AUTOMATION_BUCKETS
            )
            bucket_labels = bucket_label_map()
            active_labels = {
                bucket_labels[key]
                for key, enabled in enabled_buckets.items()
                if enabled and key in bucket_labels
            }
            matched = 0
            eligible = 0
            requested = 0
            skipped = 0
            failed = 0
            message = ""
            requested_titles: list[str] = []

            def build_result() -> dict[str, Any]:
                return {
                    "success": True,
                    "season": target_season,
                    "year": target_year,
                    "matched": matched,
                    "eligible": eligible,
                    "requested": requested,
                    "skipped": skipped,
                    "failed": failed,
                    "message": message,
                    "requestedTitles": requested_titles,
                }

            if not settings_now.request_backend_configured:
                backend_name = (
                    "Sonarr Direct"
                    if settings_now.active_request_backend == "sonarr"
                    else "Seerr"
                )
                message = f"{backend_name} is not configured."
                return build_result()
            if not active_labels:
                message = "Enable at least one automation bucket first."
                return build_result()
            if not force and not automation_due(settings_now):
                message = "Automation scan is not due yet."
                return build_result()

            payload = annotate_weebarr_requests(
                await service.seasonal_anime(
                    season=target_season,
                    year=target_year,
                    per_page=48,
                ),
                season=target_season,
                year=target_year,
            )
            now_iso = datetime.now(timezone.utc).isoformat()
            items = payload.get("items")
            payload_items = items if isinstance(items, list) else []
            for item_raw in payload_items:
                if not isinstance(item_raw, dict):
                    continue
                item = item_raw
                if item.get("bucket") not in active_labels:
                    continue
                matched += 1
                request_state = dict(item.get("request") or item.get("seerr") or {})
                if not request_state.get("requestable"):
                    skipped += 1
                    continue
                media_id = request_state.get("tmdbId") or request_state.get("seriesId")
                if media_id is None:
                    media_id = request_state.get("tvdbId")
                if media_id is None:
                    skipped += 1
                    continue
                eligible += 1
                try:
                    request_options = None
                    if settings_now.active_request_backend == "sonarr":
                        sent_seasons = request_state.get("requestSeasons") or []
                        if sent_seasons:
                            request_options = {"selectedSeasons": sent_seasons}
                    request_result = await service.request_title(
                        media_id=int(media_id),
                        title=str(item.get("title") or "Unknown"),
                        tvdb_id=request_state.get("tvdbId"),
                        seasons=request_state.get("requestSeasons")
                        or settings_now.seerr_request_seasons,
                        options=request_options,
                    )
                    record = settings_store.record_request(
                        {
                            "anilist_id": item.get("id"),
                            "backend": settings_now.active_request_backend,
                            "tmdb_id": request_state.get("tmdbId"),
                            "tvdb_id": request_state.get("tvdbId"),
                            "sonarr_series_id": request_result.get("seriesId")
                            or request_state.get("seriesId"),
                            "title": item.get("title"),
                            "season": target_season,
                            "year": target_year,
                            "requested_at": now_iso,
                            "request_seasons": request_result.get("sentSeasons", []),
                            "request_state": (
                                (request_result.get("requestState") or {}).get("state")
                            ),
                            "request_label": (
                                (request_result.get("requestState") or {}).get("label")
                            ),
                        }
                    )
                    requested += 1
                    requested_titles.append(str(record["title"]))
                except Exception:
                    logger.exception(
                        "Automation request failed for %s",
                        item.get("title") or item.get("id"),
                    )
                    failed += 1

            settings_store.save_weebarr(
                {
                    "automation_last_scan_at": now_iso,
                    "automation_last_processed_season": target_season,
                    "automation_last_processed_year": target_year,
                }
            )
            service.clear_cache()
            message = f"Processed {matched} titles across enabled buckets."
            return build_result()

    async def maybe_run_scheduled_automation() -> None:
        settings_now = current_settings()
        if not settings_now.automation_enabled or not automation_due(settings_now):
            return
        try:
            await run_automation_scan(force=True)
        except Exception:
            logger.exception("Scheduled automation scan failed")

    def annotate_weebarr_requests(
        payload: dict[str, Any],
        *,
        season: str,
        year: int,
    ) -> dict[str, Any]:
        history = settings_store.request_history(season=season, year=year)
        history_by_anilist = {
            str(record["anilist_id"]): {
                "backend": record["backend"],
                "requestedAt": record["requested_at"],
                "requestSeasons": record["request_seasons"],
                "tmdbId": record["tmdb_id"],
                "tvdbId": record["tvdb_id"],
                "sonarrSeriesId": record["sonarr_series_id"],
                "title": record["title"],
                "requestState": record["request_state"],
                "requestLabel": record["request_label"],
            }
            for record in history
        }
        items = []
        for item in payload.get("items", []):
            enriched = dict(item)
            weebarr_request = history_by_anilist.get(str(item.get("id")))
            enriched["weebarrRequest"] = weebarr_request
            if weebarr_request and weebarr_request.get("backend") == "seerr":
                request_state = dict(
                    enriched.get("request") or enriched.get("seerr") or {}
                )
                if request_state.get("state") in {
                    "missing",
                    "season_missing",
                    "missing_mapping",
                }:
                    request_state["state"] = "requested"
                    request_state["label"] = "Requested"
                    request_state["requestable"] = False
                enriched["request"] = request_state
                enriched["seerr"] = request_state
            items.append(enriched)
        return {**payload, "items": items}

    def is_local_ip(value: str) -> bool:
        candidate = value.strip()
        if not candidate:
            return False
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            return False
        return address.is_private or address.is_loopback or address.is_link_local

    def normalize_host(value: str) -> str:
        host = value.strip().lower()
        if not host:
            return ""
        if "://" in host:
            host = host.split("://", 1)[1]
        host = host.split("/", 1)[0]
        if host.startswith("[") and "]" in host:
            host = host[1 : host.index("]")]
        elif ":" in host:
            host = host.rsplit(":", 1)[0]
        return host

    def is_local_host(value: str) -> bool:
        host = normalize_host(value)
        if not host:
            return False
        if host in {
            "localhost",
            "127.0.0.1",
            "::1",
            "0.0.0.0",
            "testserver",
            "host.docker.internal",
        }:
            return True
        if host.endswith(".local"):
            return True
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return False
        return address.is_private or address.is_loopback or address.is_link_local

    def request_uses_proxy_headers(request: Request) -> bool:
        return any(
            request.headers.get(header_name, "").strip()
            for header_name in SETUP_PROXY_INDICATOR_HEADERS
        )

    def direct_client_ip(request: Request) -> str:
        return request.client.host if request.client and request.client.host else ""

    def request_is_direct_local(request: Request) -> bool:
        client_host = direct_client_ip(request)
        if client_host == "testclient":
            return is_local_host(request.url.hostname or "")
        return is_local_ip(client_host)

    def setup_request_allowed(request: Request) -> bool:
        if bootstrap_token_authorized(request):
            return True
        if request_uses_proxy_headers(request):
            return False
        return request_is_direct_local(request)

    def rate_limit_key(scope: str, request: Request) -> str:
        return f"{scope}:{direct_client_ip(request) or 'unknown'}"

    def enforce_rate_limit(
        request: Request,
        limiter: RateLimiter,
        *,
        scope: str,
        detail: str,
    ) -> None:
        retry_after = limiter.consume(rate_limit_key(scope, request))
        if retry_after is None:
            return
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )

    def setup_blocked_response(request: Request) -> HTMLResponse:
        settings_now = current_settings()
        if settings_now.bootstrap_token_enabled:
            hint_html = "<p class='auth-alt-copy'>Finish first-run setup from a direct local/private-network address, or supply the configured bootstrap token for an intentional remote claim.</p>"
        else:
            hint_html = "<p class='auth-alt-copy'>Finish first-run setup from a direct local/private-network address. Setup requests forwarded through a proxy or tunnel are blocked until the app is claimed.</p>"
        content = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Weebarr - Setup Locked</title>
    <link rel="icon" href="/static/img/weebarr-mark.svg?v={asset_version}" type="image/svg+xml" />
    <link rel="apple-touch-icon" href="/static/img/weebarr-mark.png?v={asset_version}" />
    <link rel="stylesheet" href="/static/css/weebarr.css?v={asset_version}" />
  </head>
  <body data-theme="dark" data-page="setup">
    <main class="auth-screen">
      <section class="auth-panel auth-panel-setup">
        <div class="auth-brand">
          <img class="auth-wordmark" src="/static/img/weebarr-wordmark.svg?v={asset_version}" alt="Weebarr" />
          <p>First-run setup is only available from a trusted bootstrap path.</p>
        </div>
        <div class="auth-banner" data-tone="error">Setup is blocked from this address.</div>
        {hint_html}
      </section>
    </main>
  </body>
</html>"""
        return HTMLResponse(status_code=403, content=content)

    def plex_allowed_user_values(user: dict[str, Any]) -> list[str]:
        candidates = [
            str(user.get("username") or "").strip(),
            str(user.get("email") or "").strip(),
            str(user.get("title") or "").strip(),
            str(user.get("friendlyName") or "").strip(),
        ]
        seen: set[str] = set()
        normalized: list[str] = []
        for candidate in candidates:
            folded = candidate.casefold()
            if not candidate or folded in seen:
                continue
            seen.add(folded)
            normalized.append(candidate)
        return normalized

    def login_error_message(error: str | None) -> str | None:
        return {
            "invalid_credentials": "That username or password did not match this Weebarr instance.",
            "plex_pending": "The Plex sign-in session expired. Start the Plex auth flow again.",
            "plex_incomplete": "Plex did not finish the sign-in handoff in time. Try again.",
            "plex_not_allowed": "That Plex account is not allowed to access this Weebarr instance.",
            "plex_failed": "Plex sign-in could not be completed. Try again.",
            "plex_public_url_required": "Set WEEBARR_PUBLIC_URL before using Plex sign-in so Weebarr can send Plex a trusted callback URL.",
            "rate_limited": "Too many recent sign-in attempts. Wait a moment and try again.",
        }.get((error or "").strip().lower())

    def setup_error_message(error: str | None) -> str | None:
        return {
            "plex_public_url_required": "Set WEEBARR_PUBLIC_URL before using Plex setup so Weebarr can send Plex a trusted callback URL.",
            "rate_limited": "Too many recent setup attempts. Wait a moment and try again.",
        }.get((error or "").strip().lower())

    def dashboard_context(
        request: Request,
        *,
        page_name: str,
        page_title: str,
        page_subtitle: str,
        initial_filter: str,
    ) -> dict[str, Any]:
        request_summary = request_settings_summary()
        seerr_summary = connection_summary()
        season, year = service.current_season()
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "default_season": season,
            "default_year": year,
            "seerr_configured": seerr_summary["configured"],
            "seerr_base_url": seerr_summary["baseUrl"],
            "request_settings": request_summary,
            "request_backend": request_summary["requestBackend"],
            "request_backend_configured": request_summary["requestBackendConfigured"],
            "page_name": page_name,
            "page_title": page_title,
            "page_subtitle": page_subtitle,
            "initial_filter": initial_filter,
            "weebarr": weebarr_summary(),
            "access": access_summary(),
            **auth_summary(request),
        }

    def login_context(request: Request) -> dict[str, Any]:
        settings_now = current_settings()
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "auth_mode": settings_now.effective_auth_mode,
            "local_login_enabled": settings_now.uses_local_auth,
            "plex_login_enabled": settings_now.plex_login_enabled,
            "next_path": sanitize_next_path(request.query_params.get("next")),
            "error_message": login_error_message(request.query_params.get("error")),
            "theme_context": current_theme_summary(),
        }

    def setup_context(request: Request) -> dict[str, Any]:
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "setup_required": current_settings().setup_required,
            "error_message": setup_error_message(request.query_params.get("error")),
            "theme_context": current_theme_summary(),
        }

    def backend_setup_context(request: Request) -> dict[str, Any]:
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "request_settings": request_settings_summary(),
            "access": access_summary(),
            "theme_context": current_theme_summary(),
        }

    class AuthGateMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.auth_user = current_auth_user(request)
            settings_now = current_settings()
            path = request.url.path

            if settings_now.setup_required:
                if path.startswith("/static") or path in {
                    "/api/health",
                }:
                    return await call_next(request)
                if path in {
                    "/setup",
                    "/api/setup/status",
                    "/api/setup/access",
                    "/auth/plex/start",
                    "/auth/plex/callback",
                }:
                    if setup_request_allowed(request):
                        return await call_next(request)
                    if path.startswith("/api/"):
                        return JSONResponse(
                            status_code=403,
                            content={
                                "detail": "First-run setup is only available from a trusted bootstrap path."
                            },
                        )
                    return setup_blocked_response(request)
                if path.startswith("/api/"):
                    return JSONResponse(
                        status_code=409,
                        content={
                            "detail": "Weebarr setup is required before using the API."
                        },
                    )
                if setup_request_allowed(request):
                    return RedirectResponse(url="/setup")
                return setup_blocked_response(request)

            if not settings_now.auth_enabled:
                return await call_next(request)

            if path.startswith("/static") or path in {
                "/api/health",
                "/login",
                "/logout",
                "/api/auth/login",
                "/auth/plex/start",
                "/auth/plex/callback",
            }:
                return await call_next(request)

            if path.startswith("/api/") and api_key_authorized(request):
                if api_key_path_allowed(path):
                    return await call_next(request)
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Automation API keys cannot access this endpoint."
                    },
                )

            if request.state.auth_user is not None:
                return await call_next(request)

            if path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"},
                )

            next_path = request.url.path
            if request.url.query:
                next_path = f"{next_path}?{request.url.query}"
            return RedirectResponse(
                url=f"/login?next={quote(sanitize_next_path(next_path), safe='/%?=&')}"
            )

    app.add_middleware(AuthGateMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        session_cookie=initial_settings.session_cookie_name,
        max_age=initial_settings.session_max_age_seconds,
        same_site="lax",
        https_only=bool(
            initial_settings.public_url
            and initial_settings.public_url.startswith("https://")
        ),
    )

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        if current_settings().setup_required:
            return RedirectResponse(url="/setup")
        return RedirectResponse(url="/seasonal")

    @app.get("/setup", response_class=HTMLResponse, include_in_schema=False)
    async def setup_page(request: Request):
        settings_now = current_settings()
        if not settings_now.setup_required:
            if settings_now.request_backend_required and current_auth_user(request):
                return RedirectResponse(url="/setup/backend")
            if current_auth_user(request):
                return RedirectResponse(url=DEFAULT_REDIRECT_PATH)
            return RedirectResponse(url="/login")
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context=setup_context(request),
        )

    @app.get("/setup/backend", response_class=HTMLResponse, include_in_schema=False)
    async def backend_setup_page(request: Request):
        settings_now = current_settings()
        if settings_now.setup_required:
            return RedirectResponse(url="/setup")
        if not current_auth_user(request):
            return RedirectResponse(url="/login?next=/setup/backend")
        if not settings_now.request_backend_required:
            return RedirectResponse(url=DEFAULT_REDIRECT_PATH)
        return templates.TemplateResponse(
            request=request,
            name="setup-backend.html",
            context=backend_setup_context(request),
        )

    @app.get("/api/setup/status")
    async def setup_status() -> dict[str, Any]:
        return access_summary()

    @app.post("/api/setup/access")
    async def complete_setup(
        request: Request,
        payload: AccessSetupPayload,
    ) -> dict[str, Any]:
        if not current_settings().setup_required:
            raise HTTPException(
                status_code=409, detail="Weebarr access is already configured."
            )
        enforce_rate_limit(
            request,
            setup_rate_limiter,
            scope="setup",
            detail="Too many recent setup attempts. Try again shortly.",
        )
        username = payload.username.strip()
        password = payload.password
        if not username:
            raise HTTPException(status_code=400, detail="Username is required.")
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters.",
            )
        if password != payload.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        updated = settings_store.save_auth(
            {
                "mode": "local",
                "username": username,
                "password_hash": hash_secret(password),
                "session_secret": current_settings().session_secret
                or generate_session_secret(),
                "plex_allowed_users": None,
            }
        )
        set_auth_user(
            request,
            AuthUser(
                mode="local",
                username=username,
                display_name=username,
            ),
        )
        setup_rate_limiter.reset(rate_limit_key("setup", request))
        request.session.pop("bootstrap_authorized", None)
        return {
            "success": True,
            "mode": updated.effective_auth_mode,
            "redirectTo": (
                "/setup/backend"
                if updated.request_backend_required
                else DEFAULT_REDIRECT_PATH
            ),
        }

    @app.get("/login", response_class=HTMLResponse, include_in_schema=False)
    async def login_page(request: Request):
        settings_now = current_settings()
        if settings_now.setup_required:
            return RedirectResponse(url="/setup")
        if not settings_now.auth_enabled:
            return RedirectResponse(url=DEFAULT_REDIRECT_PATH)
        if current_auth_user(request):
            if settings_now.request_backend_required:
                return RedirectResponse(url="/setup/backend")
            return RedirectResponse(
                url=sanitize_next_path(request.query_params.get("next"))
            )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=login_context(request),
        )

    @app.post("/api/auth/login")
    async def local_login(
        request: Request,
        payload: LocalLoginPayload,
    ) -> dict[str, Any]:
        settings_now = current_settings()
        if not settings_now.local_auth_configured:
            raise HTTPException(
                status_code=404, detail="Local sign-in is not configured."
            )
        limit_key = rate_limit_key("login", request)
        retry_after = login_rate_limiter.consume(limit_key)
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail="Too many recent sign-in attempts. Try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

        if not verify_local_credentials(
            settings_now,
            username=payload.username,
            password=payload.password,
        ):
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        login_rate_limiter.reset(limit_key)
        user = AuthUser(
            mode="local",
            username=settings_now.auth_username,
            display_name=settings_now.auth_username,
        )
        set_auth_user(request, user)
        return {
            "success": True,
            "redirectTo": (
                "/setup/backend"
                if settings_now.request_backend_required
                else sanitize_next_path(payload.next)
            ),
        }

    @app.get("/auth/plex/start", include_in_schema=False)
    async def plex_auth_start(
        request: Request,
        next: str | None = None,
        setup: bool = False,
    ) -> RedirectResponse:
        settings_now = current_settings()
        setup_claim = settings_now.setup_required or setup
        if not setup_claim and not settings_now.plex_login_enabled:
            return RedirectResponse(url="/login")
        if not settings_now.public_url:
            error_redirect = "/setup?error=plex_public_url_required"
            if not setup_claim:
                error_redirect = "/login?error=plex_public_url_required"
            return RedirectResponse(url=error_redirect)
        enforce_rate_limit(
            request,
            plex_rate_limiter,
            scope="plex",
            detail="Too many recent Plex sign-in attempts. Try again shortly.",
        )

        pin = await create_plex_pin(settings_now)
        request.session["plex_pending"] = {
            "id": pin.get("id"),
            "code": pin.get("code"),
            "next": sanitize_next_path(next),
            "setup": setup_claim,
        }
        forward_url = f"{settings_now.public_url.rstrip('/')}/auth/plex/callback"
        auth_url = build_plex_auth_url(
            settings_now,
            code=str(pin.get("code") or ""),
            forward_url=forward_url,
        )
        return RedirectResponse(url=auth_url)

    @app.get("/auth/plex/callback", include_in_schema=False)
    async def plex_auth_callback(request: Request) -> RedirectResponse:
        settings_now = current_settings()
        pending = request.session.get("plex_pending")
        setup_claim = bool(isinstance(pending, dict) and pending.get("setup")) or (
            settings_now.setup_required
        )
        if setup_claim and not setup_request_allowed(request):
            request.session.pop("plex_pending", None)
            return RedirectResponse(url="/setup")
        if not setup_claim and not settings_now.plex_login_enabled:
            return RedirectResponse(url="/login")

        if (
            not isinstance(pending, dict)
            or not pending.get("id")
            or not pending.get("code")
        ):
            return RedirectResponse(url="/login?error=plex_pending")

        auth_token = None
        for _ in range(8):
            pin_state = await fetch_plex_pin(
                settings_now,
                pin_id=int(pending["id"]),
                code=str(pending["code"]),
            )
            auth_token = pin_state.get("authToken")
            if auth_token:
                break
            await asyncio.sleep(1)

        if not auth_token:
            request.session.pop("plex_pending", None)
            return RedirectResponse(url="/login?error=plex_incomplete")

        user_payload = await fetch_plex_user(settings_now, token=str(auth_token))
        if setup_claim:
            updated = settings_store.save_auth(
                {
                    "mode": "plex",
                    "username": None,
                    "password_hash": None,
                    "session_secret": settings_now.session_secret
                    or generate_session_secret(),
                    "plex_allowed_users": plex_allowed_user_values(user_payload),
                }
            )
            settings_now = updated
            request.session.pop("bootstrap_authorized", None)
        if not plex_user_allowed(settings_now, user_payload):
            request.session.pop("plex_pending", None)
            return RedirectResponse(url="/login?error=plex_not_allowed")

        set_auth_user(request, plex_auth_user(user_payload))
        if settings_now.request_backend_required:
            return RedirectResponse(url="/setup/backend")
        return RedirectResponse(
            url=sanitize_next_path(str(pending.get("next") or DEFAULT_REDIRECT_PATH))
        )

    @app.get("/logout", include_in_schema=False)
    async def logout(request: Request) -> RedirectResponse:
        clear_auth_session(request)
        return RedirectResponse(url="/login")

    @app.get("/seasonal", response_class=HTMLResponse, include_in_schema=False)
    async def seasonal_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context=dashboard_context(
                request,
                page_name="seasonal",
                page_title="Seasonal Anime",
                page_subtitle=(
                    "Track each anime season by popularity, dub signal, airing "
                    "cadence, and request-backend status."
                ),
                initial_filter="all",
            ),
        )

    @app.get("/requests", response_class=HTMLResponse, include_in_schema=False)
    async def requests_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context=dashboard_context(
                request,
                page_name="requests",
                page_title="Requested Anime",
                page_subtitle=(
                    "Review the titles this season that Weebarr has already sent "
                    "through the active request backend."
                ),
                initial_filter="all",
            ),
        )

    @app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
    async def settings_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="settings.html",
            context={
                "request": request,
                "version": __version__,
                "asset_version": asset_version,
                "weebarr": weebarr_summary(),
                "connection": connection_summary(),
                "request_settings": request_settings_summary(),
                "access": access_summary(),
                **auth_summary(request),
            },
        )

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        settings_now = current_settings()
        return {
            "status": "healthy",
            "app": "weebarr",
            "version": __version__,
            "requestBackend": settings_now.active_request_backend,
            "requestBackendConfigured": settings_now.request_backend_configured,
            "seerr_configured": settings_now.seerr_configured,
        }

    @app.get("/api/config")
    async def public_config() -> dict[str, Any]:
        season, year = service.current_season()
        summary = connection_summary()
        request_summary = request_settings_summary()
        return {
            "version": __version__,
            "defaultSeason": season,
            "defaultYear": year,
            "seasonOptions": service.season_options(year),
            "requestBackend": request_summary["requestBackend"],
            "requestBackendConfigured": request_summary["requestBackendConfigured"],
            "seerrConfigured": summary["configured"],
            "seerrBaseUrl": summary["baseUrl"],
            "hasApiKey": summary["hasApiKey"],
            "apiKeyPreview": summary["apiKeyPreview"],
            "requestSeasons": summary["requestSeasons"],
            "requestSettings": request_summary,
            "weebarr": weebarr_summary(),
            "access": access_summary(),
        }

    def build_seerr_overrides(
        payload: ConnectionPayload,
        current: Settings,
    ) -> dict[str, Any]:
        submitted = payload.model_dump(exclude_unset=True)
        overrides: dict[str, Any] = {}
        if "base_url" in submitted:
            overrides["base_url"] = (
                payload.base_url.strip().rstrip("/")
                if payload.base_url is not None and payload.base_url.strip()
                else None
            )
        if "api_key" in submitted:
            overrides["api_key"] = (
                payload.api_key.strip()
                if payload.api_key is not None and payload.api_key.strip()
                else None
            )
        if "request_seasons" in submitted:
            overrides["request_seasons"] = (
                payload.request_seasons.strip()
                if payload.request_seasons is not None
                and payload.request_seasons.strip()
                else None
            )
        if "sonarr_server_id" in submitted:
            overrides["sonarr_server_id"] = payload.sonarr_server_id
        if "profile_id" in submitted:
            overrides["profile_id"] = payload.profile_id
        if "force_quality_profile" in submitted:
            overrides["force_quality_profile"] = bool(payload.force_quality_profile)
        if "series_type" in submitted:
            overrides["series_type"] = (
                payload.series_type.strip()
                if payload.series_type is not None and payload.series_type.strip()
                else None
            )
        if "root_folder" in submitted:
            overrides["root_folder"] = (
                payload.root_folder.strip() if payload.root_folder is not None else None
            ) or None
        if "language_profile_id" in submitted:
            overrides["language_profile_id"] = payload.language_profile_id
        if "request_user_id" in submitted:
            overrides["request_user_id"] = payload.request_user_id
        if "tags" in submitted:
            overrides["tags"] = payload.tags or None

        effective_force_quality_profile = (
            bool(payload.force_quality_profile)
            if "force_quality_profile" in submitted
            else current.seerr_force_quality_profile
        )
        effective_series_type = (
            payload.series_type.strip().lower()
            if "series_type" in submitted
            and payload.series_type is not None
            and payload.series_type.strip()
            else current.seerr_series_type
        )
        if effective_series_type == "default":
            effective_series_type = None
        effective_profile_id = (
            payload.profile_id
            if "profile_id" in submitted
            else current.seerr_profile_id
        )
        if effective_series_type not in (None, "standard", "daily", "anime"):
            raise HTTPException(
                status_code=400,
                detail="Series Type must be one of Seerr default, Standard, Anime / Absolute, or Daily.",
            )
        if effective_force_quality_profile and effective_profile_id is None:
            raise HTTPException(
                status_code=400,
                detail="Quality Profile ID is required when Force Quality Profile is enabled.",
            )
        return overrides

    def build_sonarr_overrides(payload: SonarrConnectionPayload) -> dict[str, Any]:
        submitted = payload.model_dump(exclude_unset=True)
        overrides: dict[str, Any] = {}
        if "base_url" in submitted:
            overrides["sonarr_base_url"] = (
                payload.base_url.strip().rstrip("/")
                if payload.base_url is not None and payload.base_url.strip()
                else None
            )
        if "api_key" in submitted:
            overrides["sonarr_api_key"] = (
                payload.api_key.strip()
                if payload.api_key is not None and payload.api_key.strip()
                else None
            )
        if "root_folder_path" in submitted:
            overrides["sonarr_root_folder_path"] = (
                payload.root_folder_path.strip()
                if payload.root_folder_path is not None
                and payload.root_folder_path.strip()
                else None
            )
        if "quality_profile_id" in submitted:
            overrides["sonarr_quality_profile_id"] = payload.quality_profile_id
        if "series_type" in submitted:
            overrides["sonarr_series_type"] = (
                payload.series_type.strip()
                if payload.series_type is not None and payload.series_type.strip()
                else None
            )
        if "default_monitor_mode" in submitted:
            overrides["sonarr_default_monitor_mode"] = (
                payload.default_monitor_mode.strip()
                if payload.default_monitor_mode is not None
                and payload.default_monitor_mode.strip()
                else None
            )
        if "default_search_on_add" in submitted:
            overrides["sonarr_default_search_on_add"] = bool(
                payload.default_search_on_add
            )
        if "default_season_folder" in submitted:
            overrides["sonarr_default_season_folder"] = bool(
                payload.default_season_folder
            )
        if "language_profile_id" in submitted:
            overrides["sonarr_language_profile_id"] = payload.language_profile_id
        if "tags" in submitted:
            overrides["sonarr_tags"] = payload.tags or None
        return overrides

    def persist_request_settings(payload: RequestSettingsPayload) -> Settings:
        current = current_settings()
        if payload.request_backend is not None:
            settings_store.save_requests({"backend": payload.request_backend.strip()})
        if payload.seerr is not None:
            settings_store.save_seerr(build_seerr_overrides(payload.seerr, current))
        if payload.sonarr is not None:
            settings_store.save_requests(build_sonarr_overrides(payload.sonarr))
        service.clear_cache()
        return current_settings()

    @app.get("/api/settings/weebarr")
    async def app_settings() -> dict[str, Any]:
        return weebarr_summary()

    @app.get("/api/settings/requests")
    async def request_settings() -> dict[str, Any]:
        return request_settings_summary()

    @app.post("/api/settings/requests/test")
    async def test_request_settings(payload: RequestSettingsPayload) -> dict[str, Any]:
        backend = (
            (payload.request_backend or request_settings_summary()["requestBackend"])
            .strip()
            .lower()
        )
        current = current_settings()
        if backend == "sonarr":
            sonarr_payload = payload.sonarr or SonarrConnectionPayload()
            base_url = (
                sonarr_payload.base_url.strip().rstrip("/")
                if sonarr_payload.base_url and sonarr_payload.base_url.strip()
                else current.sonarr_base_url
            )
            api_key = (
                sonarr_payload.api_key.strip()
                if sonarr_payload.api_key and sonarr_payload.api_key.strip()
                else current.sonarr_api_key
            )
            if not base_url or not api_key:
                raise HTTPException(
                    status_code=400,
                    detail="Sonarr host and API key are required to test Sonarr Direct.",
                )
            result = await service.test_sonarr_connection(base_url, api_key)
            result["requestBackend"] = "sonarr"
            result["connection"] = {"baseUrl": base_url}
            return result

        seerr_payload = payload.seerr or ConnectionPayload()
        base_url = (
            seerr_payload.base_url.strip().rstrip("/")
            if seerr_payload.base_url and seerr_payload.base_url.strip()
            else current.seerr_base_url
        )
        api_key = (
            seerr_payload.api_key.strip()
            if seerr_payload.api_key and seerr_payload.api_key.strip()
            else current.seerr_api_key
        )
        if not base_url or not api_key:
            raise HTTPException(
                status_code=400,
                detail="Base URL and API key are required to test Seerr.",
            )

        result = await service.test_seerr_connection(base_url, api_key)
        result["requestBackend"] = "seerr"
        result["connection"] = {
            "baseUrl": base_url,
            "requestSeasons": seerr_payload.request_seasons
            or current.seerr_request_seasons,
        }
        return result

    @app.put("/api/settings/requests")
    async def save_request_settings(payload: RequestSettingsPayload) -> dict[str, Any]:
        try:
            updated = persist_request_settings(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "success": True,
            "requests": request_settings_summary(),
            "requestBackend": updated.active_request_backend,
            "requestBackendConfigured": updated.request_backend_configured,
        }

    @app.post("/api/setup/backend")
    async def complete_backend_setup(
        request: Request,
        payload: RequestSettingsPayload,
    ) -> dict[str, Any]:
        try:
            updated = persist_request_settings(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        missing = missing_request_backend_fields(updated)
        if missing:
            backend_name = (
                "Sonarr Direct"
                if updated.active_request_backend == "sonarr"
                else "Seerr"
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Add the required {backend_name} fields before continuing: "
                    f"{', '.join(missing)}."
                ),
            )

        updated = settings_store.save_requests({"setup_complete": True})
        request.session.pop("bootstrap_authorized", None)
        return {
            "success": True,
            "redirectTo": DEFAULT_REDIRECT_PATH,
            "requests": request_settings_summary(),
            "requestBackend": updated.active_request_backend,
            "requestBackendConfigured": updated.request_backend_configured,
            "access": access_summary(),
        }

    @app.post("/api/setup/backend/skip")
    async def skip_backend_setup(
        request: Request,
        payload: RequestBackendSelectionPayload,
    ) -> dict[str, Any]:
        try:
            if payload.request_backend is not None:
                settings_store.save_requests(
                    {"backend": payload.request_backend.strip()}
                )
            updated = settings_store.save_requests({"setup_complete": True})
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        service.clear_cache()
        request.session.pop("bootstrap_authorized", None)
        return {
            "success": True,
            "redirectTo": DEFAULT_REDIRECT_PATH,
            "requests": request_settings_summary(),
            "requestBackend": updated.active_request_backend,
            "requestBackendConfigured": updated.request_backend_configured,
            "access": access_summary(),
        }

    @app.get("/api/settings/seerr")
    async def seerr_settings() -> dict[str, Any]:
        return connection_summary()

    @app.put("/api/settings/access/local")
    async def save_local_account(
        request: Request,
        payload: LocalAccountPayload,
    ) -> dict[str, Any]:
        username = payload.username.strip()
        password = payload.password
        if not username:
            raise HTTPException(status_code=400, detail="Username is required.")
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters.",
            )
        if password != payload.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        settings_now = current_settings()
        next_mode = "both" if settings_now.uses_plex_auth else "local"
        updated = settings_store.save_auth(
            {
                "mode": next_mode,
                "username": username,
                "password_hash": hash_secret(password),
                "session_secret": settings_now.session_secret
                or generate_session_secret(),
            }
        )
        active_user = current_auth_user(request)
        if active_user and active_user.mode == "local":
            set_auth_user(
                request,
                AuthUser(
                    mode="local",
                    username=username,
                    display_name=username,
                ),
            )
        return {
            "success": True,
            "access": settings_store.access_summary(),
            "authMode": updated.effective_auth_mode,
        }

    @app.post("/api/settings/access/api-key/regenerate")
    async def regenerate_app_api_key() -> dict[str, Any]:
        fresh_key = generate_api_key()
        settings_store.save_auth(
            {
                "api_key_hash": hash_secret(fresh_key),
                "api_key_preview": masked_preview(fresh_key),
            }
        )
        return {
            "success": True,
            "access": settings_store.access_summary(),
            "apiKey": fresh_key,
        }

    @app.put("/api/settings/weebarr")
    async def save_app_settings(payload: WeebarrSettingsPayload) -> dict[str, Any]:
        overrides: dict[str, Any] = {}
        if (
            payload.content_filter_mode is not None
            and payload.content_filter_mode.strip()
        ):
            overrides["content_filter_mode"] = payload.content_filter_mode.strip()
        if payload.strict_monitoring is not None:
            overrides["strict_monitoring"] = payload.strict_monitoring
        if payload.automation is not None:
            enabled = payload.automation.get("enabledBuckets")
            if enabled is not None:
                overrides["automation_enabled_buckets"] = enabled
            interval_days = payload.automation.get("scanIntervalDays")
            interval_hours = payload.automation.get("scanIntervalHours")
            normalized_days = (
                int(interval_days)
                if interval_days is not None
                else DEFAULT_AUTOMATION_SCAN_INTERVAL_DAYS
            )
            normalized_hours = (
                int(interval_hours)
                if interval_hours is not None
                else DEFAULT_AUTOMATION_SCAN_INTERVAL_HOURS
            )
            if normalized_days < 0 or normalized_days > 365:
                raise HTTPException(
                    status_code=400,
                    detail="Automation days must be between 0 and 365.",
                )
            if normalized_hours < 0 or normalized_hours > 23:
                raise HTTPException(
                    status_code=400,
                    detail="Automation hours must be between 0 and 23.",
                )
            if normalized_days == 0 and normalized_hours == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Automation cadence must be at least 1 hour.",
                )
            overrides["automation_scan_interval_days"] = normalized_days
            overrides["automation_scan_interval_hours"] = normalized_hours
        if payload.theme is not None:
            active_theme_id = payload.theme.get("activeThemeId")
            if active_theme_id is not None:
                overrides["active_theme_id"] = active_theme_id
            color_picker_tokens = payload.theme.get("colorPickerTokens")
            if color_picker_tokens is not None:
                overrides["color_picker_tokens"] = color_picker_tokens

        try:
            updated = settings_store.save_weebarr(overrides)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        service.clear_cache()
        automation_result = None
        if payload.automation_start_current_season:
            season, year = service.current_season()
            automation_result = await run_automation_scan(
                season=season,
                year=year,
                force=True,
            )
        return {
            "success": True,
            "weebarr": settings_store.weebarr_summary(),
            "strictMonitoring": updated.strict_monitoring,
            "automationResult": automation_result,
        }

    @app.post("/api/automation/scan")
    async def automation_scan(payload: AutomationScanPayload) -> dict[str, Any]:
        season = payload.season.upper() if payload.season else None
        if season is not None and season not in {"WINTER", "SPRING", "SUMMER", "FALL"}:
            raise HTTPException(status_code=400, detail="Invalid season")
        return await run_automation_scan(
            season=season,
            year=payload.year,
            force=True,
        )

    @app.post("/api/themes/import/url")
    async def import_theme_from_url(payload: ThemeImportUrlPayload) -> dict[str, Any]:
        url = payload.url.strip()
        if not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400, detail="Theme URL must be http or https."
            )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        updated = save_imported_theme(body)
        return {
            "success": True,
            "weebarr": settings_store.weebarr_summary(),
            "activeThemeId": updated.active_theme_id,
        }

    @app.post("/api/themes/import/zip")
    async def import_theme_from_zip(file: UploadFile = File(...)) -> dict[str, Any]:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Upload a .zip theme pack.")
        try:
            payload = await file.read()
            with ZipFile(BytesIO(payload)) as archive:
                theme_members = [
                    name
                    for name in archive.namelist()
                    if name.lower().endswith("theme.json")
                ]
                if not theme_members:
                    raise HTTPException(
                        status_code=400,
                        detail="Theme zip must include a theme.json manifest.",
                    )
                with archive.open(theme_members[0]) as handle:
                    body = json.loads(handle.read().decode("utf-8"))
        except HTTPException:
            raise
        except (BadZipFile, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        updated = save_imported_theme(body)
        return {
            "success": True,
            "weebarr": settings_store.weebarr_summary(),
            "activeThemeId": updated.active_theme_id,
        }

    @app.post("/api/settings/seerr/test")
    async def test_seerr_settings(payload: ConnectionPayload) -> dict[str, Any]:
        current = current_settings()
        base_url = (
            payload.base_url.strip().rstrip("/")
            if payload.base_url and payload.base_url.strip()
            else current.seerr_base_url
        )
        api_key = (
            payload.api_key.strip()
            if payload.api_key and payload.api_key.strip()
            else current.seerr_api_key
        )
        if not base_url or not api_key:
            raise HTTPException(
                status_code=400,
                detail="Base URL and API key are required to test Seerr.",
            )

        result = await service.test_seerr_connection(base_url, api_key)
        result["connection"] = {
            "baseUrl": base_url,
            "requestSeasons": payload.request_seasons or current.seerr_request_seasons,
        }
        return result

    @app.put("/api/settings/seerr")
    async def save_seerr_settings(payload: ConnectionPayload) -> dict[str, Any]:
        current = current_settings()
        updated = settings_store.save_seerr(build_seerr_overrides(payload, current))
        service.clear_cache()
        return {
            "success": True,
            "connection": settings_store.connection_summary(),
            "seerrConfigured": updated.seerr_configured,
        }

    @app.get("/api/seasonal")
    async def seasonal_anime(
        season: str = Query(..., pattern="^(WINTER|SPRING|SUMMER|FALL)$"),
        year: int = Query(..., ge=1970, le=2100),
        per_page: int = Query(default=48, ge=1, le=80, alias="perPage"),
    ) -> dict[str, Any]:
        try:
            await maybe_run_scheduled_automation()
            payload = await service.seasonal_anime(
                season=season.upper(),
                year=year,
                per_page=per_page,
            )
            return annotate_weebarr_requests(
                payload,
                season=season.upper(),
                year=year,
            )
        except Exception as exc:
            logger.exception("seasonal lookup failed")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/anime/{anime_id}/characters")
    async def anime_characters(anime_id: int) -> dict[str, Any]:
        try:
            return await service.anime_characters(anime_id)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("AniList character lookup failed")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/request")
    async def request_in_backend(payload: RequestPayload) -> dict[str, Any]:
        settings_now = current_settings()
        backend_name = (
            "Sonarr Direct"
            if settings_now.active_request_backend == "sonarr"
            else "Seerr"
        )
        if not settings_now.request_backend_configured:
            raise HTTPException(
                status_code=503,
                detail=f"{backend_name} is not configured",
            )

        try:
            request_options = (
                payload.options.model_dump(by_alias=True, exclude_none=True)
                if payload.options is not None
                else None
            )
            default_seasons: list[int] | str = (
                settings_now.seerr_request_seasons
                if settings_now.active_request_backend == "seerr"
                else "all"
            )
            result = await service.request_title(
                media_id=payload.media_id,
                title=payload.title,
                tvdb_id=payload.tvdb_id,
                seasons=payload.seasons or default_seasons,
                options=request_options,
            )
            request_state = result.get("requestState") or {
                "backend": "seerr",
                "state": "requested",
                "label": "Requested",
                "requestable": False,
            }
            if (
                payload.anime_id is not None
                and payload.season
                and payload.year is not None
            ):
                record = settings_store.record_request(
                    {
                        "anilist_id": payload.anime_id,
                        "backend": settings_now.active_request_backend,
                        "tmdb_id": (
                            payload.media_id
                            if settings_now.active_request_backend == "seerr"
                            else None
                        ),
                        "tvdb_id": payload.tvdb_id,
                        "sonarr_series_id": result.get("seriesId"),
                        "title": payload.title,
                        "season": payload.season,
                        "year": payload.year,
                        "requested_at": datetime.now(timezone.utc).isoformat(),
                        "request_seasons": result.get("sentSeasons", []),
                        "request_state": request_state.get("state"),
                        "request_label": request_state.get("label"),
                    }
                )
                result["weebarrRequest"] = {
                    "backend": record["backend"],
                    "requestedAt": record["requested_at"],
                    "requestSeasons": record["request_seasons"],
                    "tmdbId": record["tmdb_id"],
                    "tvdbId": record["tvdb_id"],
                    "sonarrSeriesId": record["sonarr_series_id"],
                    "title": record["title"],
                    "requestState": record["request_state"],
                    "requestLabel": record["request_label"],
                }
            result["requestState"] = request_state
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("%s request failed", backend_name)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


def cli() -> None:
    settings = Settings.from_env()
    uvicorn.run(
        "src.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    cli()
