"""External service integrations for Weebarr."""

from __future__ import annotations

import asyncio
import html
import re
import time
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, cast

import httpx
from fastapi import HTTPException

from src.weebarr.settings import Settings

ANILIST_URL = "https://graphql.anilist.co"
JIKAN_CHARACTERS_URL = "https://api.jikan.moe/v4/anime/{mal_id}/characters"
SEASONS = ("WINTER", "SPRING", "SUMMER", "FALL")
MEDIA_STATUS = {
    1: "Unknown",
    2: "Pending",
    3: "Processing",
    4: "Partially Available",
    5: "Available",
    6: "Blocklisted",
    7: "Deleted",
}
SOURCE_AUDIO = {
    "JP": {"language": "ja", "label": "JA", "state": "ja_only"},
    "CN": {"language": "zh", "label": "CH", "state": "ch_only"},
    "TW": {"language": "zh", "label": "CH", "state": "ch_only"},
    "HK": {"language": "zh", "label": "CH", "state": "ch_only"},
    "KR": {"language": "ko", "label": "KO", "state": "ko_only"},
}

ANILIST_QUERY = """
query SeasonalAnime($season: MediaSeason!, $year: Int!, $page: Int!, $perPage: Int!) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage total }
    media(type: ANIME, season: $season, seasonYear: $year, sort: POPULARITY_DESC, isAdult: false) {
      id
      idMal
      siteUrl
      format
      status
      episodes
      duration
      popularity
      averageScore
      meanScore
      favourites
      countryOfOrigin
      season
      seasonYear
      title { romaji english native }
      coverImage { extraLarge large color }
      bannerImage
      description(asHtml: false)
      genres
      startDate { year month day }
      nextAiringEpisode { airingAt episode timeUntilAiring }
      studios(isMain: true) { nodes { name } }
    }
  }
}
"""


def normalize_title(value: str | None) -> str:
    """Normalize titles for loose matching."""

    if not value:
        return ""
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def strip_description(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:420]


def _date_from_parts(parts: dict[str, Any] | None) -> str | None:
    if (
        not parts
        or not parts.get("year")
        or not parts.get("month")
        or not parts.get("day")
    ):
        return None
    return f"{parts['year']:04d}-{parts['month']:02d}-{parts['day']:02d}"


def _next_airing(next_airing: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_airing:
        return None
    airing_at = next_airing.get("airingAt")
    iso = None
    if airing_at:
        iso = datetime.fromtimestamp(airing_at, tz=timezone.utc).isoformat()
    return {
        "episode": next_airing.get("episode"),
        "airingAt": iso,
        "timeUntilAiring": next_airing.get("timeUntilAiring"),
    }


def candidate_score(
    titles: list[str],
    candidate: dict[str, Any],
    start_year: int | None,
) -> int:
    """Score a Seerr/TMDB candidate against AniList titles."""

    candidate_title = candidate.get("name") or candidate.get("title") or ""
    normalized_candidate = normalize_title(candidate_title)
    if not normalized_candidate:
        return 0

    best = 0
    for title in titles:
        normalized_title = normalize_title(title)
        if not normalized_title:
            continue
        if normalized_title == normalized_candidate:
            best = max(best, 100)
        elif (
            normalized_title in normalized_candidate
            or normalized_candidate in normalized_title
        ):
            best = max(best, 85)
        else:
            title_tokens = set(normalized_title.split())
            candidate_tokens = set(normalized_candidate.split())
            overlap = title_tokens & candidate_tokens
            if title_tokens:
                best = max(best, int((len(overlap) / len(title_tokens)) * 70))

    first_air = candidate.get("firstAirDate") or candidate.get("first_air_date") or ""
    if start_year and first_air.startswith(str(start_year)):
        best += 10

    return min(best, 110)


def title_search_variants(title: str) -> list[str]:
    """Generate safe Seerr search fallbacks for titles with season suffixes."""

    variants = [title]
    cleaned = re.sub(
        r"\s+(season|cour|part)\s+\d+\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"\s+\d+(st|nd|rd|th)\s+season\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    if cleaned and cleaned != title:
        variants.append(cleaned)
    return list(dict.fromkeys(variants))


class TTLCache:
    """Tiny in-memory TTL cache for API responses."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


class WeebarrService:
    """Coordinates AniList seasonal data and Seerr request state."""

    def __init__(
        self,
        settings: Settings | Callable[[], Settings],
    ):
        if callable(settings):
            self._settings_provider = settings
        else:
            self._settings_provider = lambda: settings
        self.cache = TTLCache()

    @property
    def settings(self) -> Settings:
        return self._settings_provider()

    def clear_cache(self) -> None:
        self.cache.clear()

    def current_season(self) -> tuple[str, int]:
        now = datetime.now()
        if now.month <= 3:
            return "WINTER", now.year
        if now.month <= 6:
            return "SPRING", now.year
        if now.month <= 9:
            return "SUMMER", now.year
        return "FALL", now.year

    def season_options(self, current_year: int) -> list[dict[str, Any]]:
        return [
            {"season": season, "year": year, "label": f"{season.title()} {year}"}
            for year in range(current_year - 1, current_year + 2)
            for season in SEASONS
        ]

    async def seasonal_anime(
        self, season: str, year: int, per_page: int
    ) -> dict[str, Any]:
        cache_key = (
            f"seasonal:{season}:{year}:{per_page}:{self.settings.seerr_configured}"
        )
        cached = self.cache.get(cache_key)
        if cached:
            return cast(dict[str, Any], cached)

        anime = await self._fetch_anilist(season, year, per_page)
        seerr_semaphore = asyncio.Semaphore(8)
        # Jikan is rate-limited, but serializing dub lookups makes cold loads feel stuck.
        # A moderate fan-out keeps the first render responsive while still falling back
        # quickly when Jikan returns 429s.
        audio_semaphore = asyncio.Semaphore(6)

        async def enrich(item: dict[str, Any]) -> dict[str, Any]:
            async def resolve_seerr() -> dict[str, Any]:
                async with seerr_semaphore:
                    return await self._resolve_seerr(item)

            async def resolve_audio() -> dict[str, Any]:
                async with audio_semaphore:
                    return await self._resolve_audio(item)

            item["seerr"], item["audio"] = await asyncio.gather(
                resolve_seerr(),
                resolve_audio(),
            )
            return item

        enriched = await asyncio.gather(*(enrich(item) for item in anime))
        stats = Counter(item["seerr"]["state"] for item in enriched)
        result = {
            "season": season,
            "year": year,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "stats": {
                "total": len(enriched),
                "requestable": stats.get("requestable", 0) + stats.get("partial", 0),
                "requested": stats.get("requested", 0),
                "available": stats.get("available", 0),
                "missingMapping": stats.get("missing_mapping", 0),
            },
            "items": enriched,
        }
        self.cache.set(cache_key, result, self.settings.anilist_cache_ttl_seconds)
        return result

    async def _fetch_anilist(self, season: str, year: int, per_page: int) -> list[dict]:
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.post(
                ANILIST_URL,
                json={
                    "query": ANILIST_QUERY,
                    "variables": {
                        "season": season,
                        "year": year,
                        "page": 1,
                        "perPage": per_page,
                    },
                },
            )
            response.raise_for_status()
            body = response.json()
            if "errors" in body:
                raise RuntimeError(body["errors"][0].get("message", "AniList error"))

        media = body["data"]["Page"]["media"]
        return [
            self._shape_anime(item, rank) for rank, item in enumerate(media, start=1)
        ]

    def _shape_anime(self, item: dict[str, Any], rank: int) -> dict[str, Any]:
        titles = item.get("title") or {}
        start_year = (item.get("startDate") or {}).get("year")
        return {
            "id": item.get("id"),
            "malId": item.get("idMal"),
            "rank": rank,
            "bucket": self._bucket_for_rank(rank),
            "title": titles.get("english") or titles.get("romaji") or "Untitled",
            "romajiTitle": titles.get("romaji"),
            "englishTitle": titles.get("english"),
            "nativeTitle": titles.get("native"),
            "siteUrl": item.get("siteUrl"),
            "format": item.get("format"),
            "status": item.get("status"),
            "episodes": item.get("episodes"),
            "duration": item.get("duration"),
            "popularity": item.get("popularity") or 0,
            "averageScore": item.get("averageScore") or item.get("meanScore"),
            "favourites": item.get("favourites") or 0,
            "countryOfOrigin": item.get("countryOfOrigin"),
            "season": item.get("season"),
            "seasonYear": item.get("seasonYear"),
            "startDate": _date_from_parts(item.get("startDate")),
            "startYear": start_year,
            "nextAiring": _next_airing(item.get("nextAiringEpisode")),
            "cover": (item.get("coverImage") or {}).get("extraLarge")
            or (item.get("coverImage") or {}).get("large"),
            "coverColor": (item.get("coverImage") or {}).get("color") or "#83e8ff",
            "banner": item.get("bannerImage"),
            "genres": item.get("genres") or [],
            "description": strip_description(item.get("description")),
            "studios": [
                node.get("name")
                for node in ((item.get("studios") or {}).get("nodes") or [])
                if node.get("name")
            ],
        }

    def _bucket_for_rank(self, rank: int) -> str:
        if rank <= 10:
            return "Headliners"
        if rank <= 30:
            return "Strong Signal"
        return "Deep Cuts"

    def _source_audio(self, country: str | None) -> dict[str, Any]:
        source = SOURCE_AUDIO.get(country or "")
        if source:
            return {
                "sourceCountry": country,
                "sourceLanguage": source["language"],
                "sourceLabel": source["label"],
                "fallbackState": source["state"],
                "fallbackLabel": f"{source['label']} only",
            }
        return {
            "sourceCountry": country,
            "sourceLanguage": None,
            "sourceLabel": "Sub",
            "fallbackState": "unknown",
            "fallbackLabel": "Audio ?",
        }

    async def _resolve_audio(self, anime: dict[str, Any]) -> dict[str, Any]:
        source = self._source_audio(anime.get("countryOfOrigin"))
        mal_id = anime.get("malId")

        if not self.settings.audio_lookup_enabled or not mal_id:
            return {
                "state": source["fallbackState"],
                "label": source["fallbackLabel"],
                "englishDub": None,
                "sourceCountry": source["sourceCountry"],
                "sourceLanguage": source["sourceLanguage"],
                "confidence": "source_origin",
            }

        cache_key = f"audio:jikan:{mal_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        result = {
            "state": "unknown",
            "label": "Audio ?",
            "englishDub": None,
            "sourceCountry": source["sourceCountry"],
            "sourceLanguage": source["sourceLanguage"],
            "confidence": "lookup_failed",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.audio_lookup_timeout_seconds
            ) as client:
                response = await client.get(JIKAN_CHARACTERS_URL.format(mal_id=mal_id))
            if response.status_code == 404:
                result["confidence"] = "no_mal_character_data"
                self.cache.set(cache_key, result, self.settings.audio_cache_ttl_seconds)
                return result
            response.raise_for_status()
            characters = cast(list[dict[str, Any]], response.json().get("data", []))
        except (httpx.HTTPError, ValueError):
            self.cache.set(
                cache_key, result, min(3600, self.settings.audio_cache_ttl_seconds)
            )
            return result

        languages = {
            actor.get("language")
            for character in characters
            for actor in character.get("voice_actors", [])
            if actor.get("language")
        }
        has_english = any(language == "English" for language in languages)
        if has_english:
            result = {
                "state": "en_dubbed",
                "label": "EN Dub",
                "englishDub": True,
                "sourceCountry": source["sourceCountry"],
                "sourceLanguage": source["sourceLanguage"],
                "confidence": "jikan_voice_actors",
            }
        elif characters:
            result = {
                "state": source["fallbackState"],
                "label": source["fallbackLabel"],
                "englishDub": False,
                "sourceCountry": source["sourceCountry"],
                "sourceLanguage": source["sourceLanguage"],
                "confidence": "jikan_no_english_voice_actors",
            }
        self.cache.set(cache_key, result, self.settings.audio_cache_ttl_seconds)
        return result

    async def _resolve_seerr(self, anime: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.seerr_configured:
            return {
                "state": "disabled",
                "label": "Seerr not configured",
                "requestable": False,
            }

        raw_titles = [
            anime.get("englishTitle"),
            anime.get("title"),
            anime.get("romajiTitle"),
            anime.get("nativeTitle"),
        ]
        titles = [title for title in raw_titles if isinstance(title, str) and title]
        raw_start_year = anime.get("startYear")
        start_year = raw_start_year if isinstance(raw_start_year, int) else None
        best: dict[str, Any] | None = None
        best_score = 0

        for title in dict.fromkeys(titles):
            results: list[dict[str, Any]] = []
            for query in title_search_variants(title):
                results = await self._seerr_search(query)
                if results:
                    break
            for candidate in results:
                media_type = candidate.get("mediaType") or candidate.get("media_type")
                if media_type != "tv":
                    continue
                score = candidate_score(titles, candidate, start_year)
                if score > best_score:
                    best = candidate
                    best_score = score
            if best_score >= 95:
                break

        if not best or best_score < 45:
            return {
                "state": "missing_mapping",
                "label": "No Seerr match",
                "requestable": False,
                "matchScore": best_score,
            }

        media_info = best.get("mediaInfo") or {}
        requests = [
            req
            for req in media_info.get("requests", [])
            if req.get("status") not in (3, 5)
        ]
        raw_status_code = media_info.get("status")
        status_code = raw_status_code if isinstance(raw_status_code, int) else None
        state = "requestable"
        label = "Requestable"
        requestable = True

        if status_code == 5:
            state, label, requestable = "available", "Available", False
        elif status_code == 6:
            state, label, requestable = "blocklisted", "Blocklisted", False
        elif requests or status_code in (2, 3):
            state, label, requestable = (
                "requested",
                MEDIA_STATUS.get(status_code or 0, "Requested"),
                False,
            )
        elif status_code == 4:
            state, label, requestable = "partial", "Request Missing", True

        return {
            "state": state,
            "label": label,
            "requestable": requestable,
            "tmdbId": best.get("id"),
            "tvdbId": (best.get("externalIds") or {}).get("tvdbId"),
            "title": best.get("name") or best.get("title"),
            "firstAirDate": best.get("firstAirDate") or best.get("first_air_date"),
            "matchScore": best_score,
            "mediaStatus": status_code,
        }

    async def _seerr_search(self, query: str) -> list[dict[str, Any]]:
        cache_key = f"seerr-search:{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.get(
                f"{self.settings.seerr_base_url}/api/v1/search",
                params={"query": query},
                headers={"X-Api-Key": self.settings.seerr_api_key},
            )
            if response.status_code == 400:
                self.cache.set(cache_key, [], self.settings.seerr_cache_ttl_seconds)
                return []
            response.raise_for_status()
            results = cast(list[dict[str, Any]], response.json().get("results", []))

        self.cache.set(cache_key, results, self.settings.seerr_cache_ttl_seconds)
        return results

    async def _sonarr_servers(
        self,
        base_url: str,
        api_key: str,
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.get(
                f"{base_url.rstrip('/')}/api/v1/settings/sonarr",
                headers={"X-Api-Key": api_key},
            )
            response.raise_for_status()
            return cast(list[dict[str, Any]], response.json())

    @staticmethod
    def _select_default_server(servers: list[dict[str, Any]]) -> dict[str, Any]:
        return next((item for item in servers if item.get("isDefault")), servers[0])

    async def _sonarr_defaults(self) -> dict[str, Any]:
        cache_key = "seerr-sonarr-defaults"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        defaults: dict[str, Any] = {}
        servers = await self._sonarr_servers(
            self.settings.seerr_base_url,
            self.settings.seerr_api_key,
        )

        if servers:
            server = self._select_default_server(servers)
            defaults = {
                "serverId": server.get("id"),
                "profileId": server.get("activeAnimeProfileId")
                or server.get("activeProfileId"),
                "rootFolder": server.get("activeAnimeDirectory")
                or server.get("activeDirectory"),
            }
        self.cache.set(cache_key, defaults, self.settings.seerr_cache_ttl_seconds)
        return defaults

    async def test_seerr_connection(
        self,
        base_url: str,
        api_key: str,
    ) -> dict[str, Any]:
        try:
            servers = await self._sonarr_servers(base_url, api_key)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            raise HTTPException(
                status_code=exc.response.status_code, detail=detail
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        defaults: dict[str, Any] = {}
        if servers:
            server = self._select_default_server(servers)
            defaults = {
                "serverId": server.get("id"),
                "serverName": server.get("name"),
                "profileId": server.get("activeAnimeProfileId")
                or server.get("activeProfileId"),
                "rootFolder": server.get("activeAnimeDirectory")
                or server.get("activeDirectory"),
            }

        return {
            "success": True,
            "serverCount": len(servers),
            "defaults": defaults,
        }

    async def request_in_seerr(
        self,
        media_id: int,
        title: str,
        tvdb_id: int | None,
        seasons: list[int] | str,
    ) -> dict[str, Any]:
        defaults = await self._sonarr_defaults()
        payload: dict[str, Any] = {
            "mediaType": "tv",
            "mediaId": media_id,
            "is4k": False,
            "seasons": seasons,
            "serverId": (
                self.settings.seerr_sonarr_server_id
                if self.settings.seerr_sonarr_server_id is not None
                else defaults.get("serverId")
            ),
            "profileId": (
                self.settings.seerr_profile_id
                if self.settings.seerr_profile_id is not None
                else defaults.get("profileId")
            ),
            "rootFolder": self.settings.seerr_root_folder or defaults.get("rootFolder"),
        }
        if tvdb_id:
            payload["tvdbId"] = tvdb_id
        if self.settings.seerr_language_profile_id is not None:
            payload["languageProfileId"] = self.settings.seerr_language_profile_id
        if self.settings.seerr_request_user_id is not None:
            payload["userId"] = self.settings.seerr_request_user_id
        if self.settings.seerr_tags:
            payload["tags"] = self.settings.seerr_tags

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.post(
                f"{self.settings.seerr_base_url}/api/v1/request",
                json=payload,
                headers={"X-Api-Key": self.settings.seerr_api_key},
            )

        if response.status_code in (200, 201, 202):
            return {
                "success": True,
                "statusCode": response.status_code,
                "title": title,
                "response": response.json() if response.content else {},
            }
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail="Already requested in Seerr")
        raise HTTPException(status_code=response.status_code, detail=response.text)
