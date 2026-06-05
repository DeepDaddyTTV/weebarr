#!/usr/bin/env python3
"""Weebarr entry point."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any, Optional, Union
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
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
    verify_local_credentials,
)
from src.weebarr.services import WeebarrService
from src.weebarr.settings import Settings, SettingsStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("weebarr")

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))


class RequestPayload(BaseModel):
    """Payload accepted by Weebarr before forwarding to Seerr."""

    media_id: int = Field(..., alias="mediaId")
    anime_id: Optional[int] = Field(default=None, alias="animeId")
    title: str
    tvdb_id: Optional[int] = Field(default=None, alias="tvdbId")
    season: Optional[str] = None
    year: Optional[int] = None
    seasons: Optional[Union[list[int], str]] = None


class ConnectionPayload(BaseModel):
    """Editable Seerr connection settings."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: Optional[str] = Field(default=None, alias="baseUrl")
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    request_seasons: Optional[str] = Field(default=None, alias="requestSeasons")
    sonarr_server_id: Optional[int] = Field(default=None, alias="sonarrServerId")
    profile_id: Optional[int] = Field(default=None, alias="profileId")
    root_folder: Optional[str] = Field(default=None, alias="rootFolder")
    language_profile_id: Optional[int] = Field(default=None, alias="languageProfileId")
    request_user_id: Optional[int] = Field(default=None, alias="requestUserId")
    tags: Optional[list[int]] = None
    content_filter_mode: Optional[str] = Field(default=None, alias="contentFilterMode")
    admin_token: Optional[str] = Field(default=None, alias="adminToken")


class LocalLoginPayload(BaseModel):
    """Username/password login payload for local auth mode."""

    username: str = ""
    password: str = ""
    next: Optional[str] = None


class AccessSetupPayload(BaseModel):
    """First-run access configuration payload."""

    model_config = ConfigDict(populate_by_name=True)

    mode: str = "local"
    username: str = ""
    password: str = ""
    confirm_password: str = Field(default="", alias="confirmPassword")
    public_url: Optional[str] = Field(default=None, alias="publicUrl")
    plex_allowed_users: Optional[list[str]] = Field(
        default=None,
        alias="plexAllowedUsers",
    )
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    generate_api_key: bool = Field(default=True, alias="generateApiKey")
    admin_token: Optional[str] = Field(default=None, alias="adminToken")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI app."""

    base_settings = settings or Settings.from_env()
    settings_store = SettingsStore(base_settings)
    initial_settings = settings_store.get()
    if initial_settings.auth_enabled and not initial_settings.session_secret:
        raise RuntimeError(
            "A session secret is required when Weebarr authentication is enabled."
        )
    if initial_settings.uses_local_auth and (
        not initial_settings.auth_username
        or not (initial_settings.auth_password_hash or initial_settings.auth_password)
    ):
        raise RuntimeError(
            "A username and password are required when local auth is enabled."
        )
    service = WeebarrService(settings_store.get)
    asset_version = str(int(time()))
    app = FastAPI(
        title="Weebarr",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
    )

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

    def connection_summary() -> dict[str, Any]:
        return settings_store.connection_summary()

    def access_summary() -> dict[str, Any]:
        return settings_store.access_summary()

    def auth_summary(request: Request) -> dict[str, Any]:
        user = current_auth_user(request)
        return {
            "auth_enabled": current_settings().auth_enabled,
            "auth_mode": current_settings().auth_mode,
            "auth_user_name": user.display_name if user else None,
            "auth_user_mode": user.mode if user else None,
        }

    def annotate_weebarr_requests(
        payload: dict[str, Any],
        *,
        season: str,
        year: int,
    ) -> dict[str, Any]:
        history = settings_store.request_history(season=season, year=year)
        history_by_anilist = {
            str(record["anilist_id"]): {
                "requestedAt": record["requested_at"],
                "requestSeasons": record["request_seasons"],
                "tmdbId": record["tmdb_id"],
                "tvdbId": record["tvdb_id"],
                "title": record["title"],
            }
            for record in history
        }
        items = []
        for item in payload.get("items", []):
            enriched = dict(item)
            enriched["weebarrRequest"] = history_by_anilist.get(str(item.get("id")))
            items.append(enriched)
        return {**payload, "items": items}

    def require_admin(token: Optional[str]) -> None:
        configured = current_settings().admin_token
        if configured and token != configured:
            raise HTTPException(status_code=401, detail="Valid admin token required")

    def login_error_message(error: str | None) -> str | None:
        return {
            "invalid_credentials": "That username or password did not match this Weebarr instance.",
            "plex_pending": "The Plex sign-in session expired. Start the Plex auth flow again.",
            "plex_incomplete": "Plex did not finish the sign-in handoff in time. Try again.",
            "plex_not_allowed": "That Plex account is not allowed to access this Weebarr instance.",
            "plex_failed": "Plex sign-in could not be completed. Try again.",
        }.get((error or "").strip().lower())

    def dashboard_context(
        request: Request,
        *,
        page_name: str,
        page_title: str,
        page_subtitle: str,
        initial_filter: str,
    ) -> dict[str, Any]:
        summary = connection_summary()
        season, year = service.current_season()
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "default_season": season,
            "default_year": year,
            "seerr_configured": summary["configured"],
            "seerr_base_url": summary["baseUrl"],
            "page_name": page_name,
            "page_title": page_title,
            "page_subtitle": page_subtitle,
            "initial_filter": initial_filter,
            "access": access_summary(),
            **auth_summary(request),
        }

    def login_context(request: Request) -> dict[str, Any]:
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "auth_mode": current_settings().auth_mode,
            "next_path": sanitize_next_path(request.query_params.get("next")),
            "error_message": login_error_message(request.query_params.get("error")),
        }

    def setup_context(request: Request) -> dict[str, Any]:
        suggested_public_url = current_settings().public_url or str(
            request.base_url
        ).rstrip("/")
        return {
            "request": request,
            "version": __version__,
            "asset_version": asset_version,
            "suggested_public_url": suggested_public_url,
            "setup_required": current_settings().setup_required,
            "admin_protected": current_settings().admin_protected,
        }

    class AuthGateMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.auth_user = current_auth_user(request)
            settings_now = current_settings()
            path = request.url.path

            if settings_now.setup_required:
                if path.startswith("/static") or path in {
                    "/api/health",
                    "/setup",
                    "/api/setup/status",
                    "/api/setup/access",
                }:
                    return await call_next(request)
                if path.startswith("/api/"):
                    return JSONResponse(
                        status_code=409,
                        content={
                            "detail": "Weebarr setup is required before using the API."
                        },
                    )
                return RedirectResponse(url="/setup")

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
                return await call_next(request)

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
        secret_key=initial_settings.session_secret or "weebarr-dev-session",
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
            if current_auth_user(request):
                return RedirectResponse(url=DEFAULT_REDIRECT_PATH)
            return RedirectResponse(url="/login")
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context=setup_context(request),
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
        require_admin(payload.admin_token)

        mode = payload.mode.strip().lower()
        if mode not in {"local", "plex"}:
            raise HTTPException(
                status_code=400,
                detail="Choose either local or plex access.",
            )

        session_secret = generate_session_secret()
        api_key_plain = (payload.api_key or "").strip()
        if payload.generate_api_key and not api_key_plain:
            api_key_plain = generate_api_key()

        overrides: dict[str, Any] = {
            "mode": mode,
            "session_secret": session_secret,
            "api_key_hash": hash_secret(api_key_plain) if api_key_plain else None,
            "api_key_preview": masked_preview(api_key_plain) if api_key_plain else None,
        }

        if mode == "local":
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

            overrides.update(
                {
                    "username": username,
                    "password_hash": hash_secret(password),
                    "public_url": (
                        payload.public_url.strip().rstrip("/")
                        if payload.public_url and payload.public_url.strip()
                        else None
                    ),
                    "plex_allowed_users": None,
                }
            )
            updated = settings_store.save_auth(overrides)
            user = AuthUser(mode="local", username=username, display_name=username)
            set_auth_user(request, user)
            return {
                "success": True,
                "mode": updated.auth_mode,
                "redirectTo": DEFAULT_REDIRECT_PATH,
                "generatedApiKey": api_key_plain or None,
            }

        public_url = (
            payload.public_url.strip().rstrip("/")
            if payload.public_url and payload.public_url.strip()
            else str(request.base_url).rstrip("/")
        )
        allowed_users = [
            entry.strip()
            for entry in (payload.plex_allowed_users or [])
            if entry and entry.strip()
        ]
        overrides.update(
            {
                "username": "",
                "password_hash": None,
                "public_url": public_url,
                "plex_allowed_users": allowed_users,
            }
        )
        updated = settings_store.save_auth(overrides)
        return {
            "success": True,
            "mode": updated.auth_mode,
            "redirectTo": "/login",
            "generatedApiKey": api_key_plain or None,
        }

    @app.get("/login", response_class=HTMLResponse, include_in_schema=False)
    async def login_page(request: Request):
        settings_now = current_settings()
        if settings_now.setup_required:
            return RedirectResponse(url="/setup")
        if not settings_now.auth_enabled:
            return RedirectResponse(url=DEFAULT_REDIRECT_PATH)
        if current_auth_user(request):
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
        if not settings_now.uses_local_auth:
            raise HTTPException(status_code=404, detail="Local auth is not enabled.")

        if not verify_local_credentials(
            settings_now,
            username=payload.username,
            password=payload.password,
        ):
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        user = AuthUser(
            mode="local",
            username=settings_now.auth_username,
            display_name=settings_now.auth_username,
        )
        set_auth_user(request, user)
        return {
            "success": True,
            "redirectTo": sanitize_next_path(payload.next),
        }

    @app.get("/auth/plex/start", include_in_schema=False)
    async def plex_auth_start(
        request: Request,
        next: str | None = None,
    ) -> RedirectResponse:
        settings_now = current_settings()
        if not settings_now.uses_plex_auth:
            return RedirectResponse(url="/login")

        pin = await create_plex_pin(settings_now)
        request.session["plex_pending"] = {
            "id": pin.get("id"),
            "code": pin.get("code"),
            "next": sanitize_next_path(next),
        }
        public_origin = (
            settings_now.public_url.rstrip("/")
            if settings_now.public_url
            else str(request.base_url).rstrip("/")
        )
        forward_url = f"{public_origin}/auth/plex/callback"
        auth_url = build_plex_auth_url(
            settings_now,
            code=str(pin.get("code") or ""),
            forward_url=forward_url,
        )
        return RedirectResponse(url=auth_url)

    @app.get("/auth/plex/callback", include_in_schema=False)
    async def plex_auth_callback(request: Request) -> RedirectResponse:
        settings_now = current_settings()
        if not settings_now.uses_plex_auth:
            return RedirectResponse(url="/login")

        pending = request.session.get("plex_pending")
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
        if not plex_user_allowed(settings_now, user_payload):
            request.session.pop("plex_pending", None)
            return RedirectResponse(url="/login?error=plex_not_allowed")

        set_auth_user(request, plex_auth_user(user_payload))
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
                page_subtitle="Track each anime season by popularity, dub signal, airing cadence, and Seerr request status.",
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
                page_subtitle="Review the titles this season that are already requested, partially requested, or fully available in Seerr.",
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
                "connection": connection_summary(),
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
            "seerr_configured": settings_now.seerr_configured,
        }

    @app.get("/api/config")
    async def public_config() -> dict[str, Any]:
        season, year = service.current_season()
        summary = connection_summary()
        return {
            "version": __version__,
            "defaultSeason": season,
            "defaultYear": year,
            "seasonOptions": service.season_options(year),
            "seerrConfigured": summary["configured"],
            "seerrBaseUrl": summary["baseUrl"],
            "hasApiKey": summary["hasApiKey"],
            "apiKeyPreview": summary["apiKeyPreview"],
            "requestSeasons": summary["requestSeasons"],
            "contentFilterMode": summary["contentFilterMode"],
            "adminProtected": summary["adminProtected"],
            "access": access_summary(),
        }

    @app.get("/api/settings/seerr")
    async def seerr_settings() -> dict[str, Any]:
        return connection_summary()

    @app.post("/api/settings/seerr/test")
    async def test_seerr_settings(payload: ConnectionPayload) -> dict[str, Any]:
        require_admin(payload.admin_token)
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
        require_admin(payload.admin_token)

        overrides: dict[str, Any] = {}
        if payload.base_url is not None and payload.base_url.strip():
            overrides["base_url"] = payload.base_url.strip().rstrip("/")
        if payload.api_key is not None and payload.api_key.strip():
            overrides["api_key"] = payload.api_key.strip()
        if payload.request_seasons is not None and payload.request_seasons.strip():
            overrides["request_seasons"] = payload.request_seasons.strip()
        if payload.sonarr_server_id is not None:
            overrides["sonarr_server_id"] = payload.sonarr_server_id
        if payload.profile_id is not None:
            overrides["profile_id"] = payload.profile_id
        if payload.root_folder is not None:
            overrides["root_folder"] = payload.root_folder.strip() or None
        if payload.language_profile_id is not None:
            overrides["language_profile_id"] = payload.language_profile_id
        if payload.request_user_id is not None:
            overrides["request_user_id"] = payload.request_user_id
        if payload.tags is not None:
            overrides["tags"] = payload.tags
        if (
            payload.content_filter_mode is not None
            and payload.content_filter_mode.strip()
        ):
            overrides["content_filter_mode"] = payload.content_filter_mode.strip()

        updated = settings_store.save_seerr(overrides)
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

    @app.post("/api/request")
    async def request_in_seerr(payload: RequestPayload) -> dict[str, Any]:
        if not current_settings().seerr_configured:
            raise HTTPException(status_code=503, detail="Seerr is not configured")

        try:
            result = await service.request_in_seerr(
                media_id=payload.media_id,
                title=payload.title,
                tvdb_id=payload.tvdb_id,
                seasons=payload.seasons or current_settings().seerr_request_seasons,
            )
            if (
                payload.anime_id is not None
                and payload.season
                and payload.year is not None
            ):
                record = settings_store.record_request(
                    {
                        "anilist_id": payload.anime_id,
                        "tmdb_id": payload.media_id,
                        "tvdb_id": payload.tvdb_id,
                        "title": payload.title,
                        "season": payload.season,
                        "year": payload.year,
                        "requested_at": datetime.now(timezone.utc).isoformat(),
                        "request_seasons": result.get("sentSeasons", []),
                    }
                )
                result["weebarrRequest"] = {
                    "requestedAt": record["requested_at"],
                    "requestSeasons": record["request_seasons"],
                    "tmdbId": record["tmdb_id"],
                    "tvdbId": record["tvdb_id"],
                    "title": record["title"],
                }
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Seerr request failed")
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
