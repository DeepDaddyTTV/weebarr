#!/usr/bin/env python3
"""Weebarr entry point."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from src.version import __version__
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


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI app."""

    base_settings = settings or Settings.from_env()
    settings_store = SettingsStore(base_settings)
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

    def connection_summary() -> dict[str, Any]:
        return settings_store.connection_summary()

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
        }

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/seasonal")

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
