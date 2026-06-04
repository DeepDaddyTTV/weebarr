#!/usr/bin/env python3
"""Weebarr entry point."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.version import __version__
from src.weebarr.services import WeebarrService
from src.weebarr.settings import Settings

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
    title: str
    tvdb_id: Optional[int] = Field(default=None, alias="tvdbId")
    seasons: Optional[Union[list[int], str]] = "all"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI app."""

    app_settings = settings or Settings.from_env()
    service = WeebarrService(app_settings)
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

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/seasonal")

    @app.get("/seasonal", response_class=HTMLResponse, include_in_schema=False)
    async def seasonal_page(request: Request) -> HTMLResponse:
        season, year = service.current_season()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "version": __version__,
                "default_season": season,
                "default_year": year,
                "seerr_configured": app_settings.seerr_configured,
            },
        )

    @app.get("/api/health")
    async def health() -> dict:
        return {
            "status": "healthy",
            "app": "weebarr",
            "version": __version__,
            "seerr_configured": app_settings.seerr_configured,
        }

    @app.get("/api/config")
    async def public_config() -> dict:
        season, year = service.current_season()
        return {
            "version": __version__,
            "defaultSeason": season,
            "defaultYear": year,
            "seasonOptions": service.season_options(year),
            "seerrConfigured": app_settings.seerr_configured,
            "requestSeasons": app_settings.seerr_request_seasons,
        }

    @app.get("/api/seasonal")
    async def seasonal_anime(
        season: str = Query(..., pattern="^(WINTER|SPRING|SUMMER|FALL)$"),
        year: int = Query(..., ge=1970, le=2100),
        per_page: int = Query(default=48, ge=1, le=80, alias="perPage"),
    ) -> dict:
        try:
            return await service.seasonal_anime(
                season=season.upper(),
                year=year,
                per_page=per_page,
            )
        except Exception as exc:
            logger.exception("seasonal lookup failed")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/request")
    async def request_in_seerr(payload: RequestPayload) -> dict:
        if not app_settings.seerr_configured:
            raise HTTPException(status_code=503, detail="Seerr is not configured")

        try:
            return await service.request_in_seerr(
                media_id=payload.media_id,
                title=payload.title,
                tvdb_id=payload.tvdb_id,
                seasons=payload.seasons or app_settings.seerr_request_seasons,
            )
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
