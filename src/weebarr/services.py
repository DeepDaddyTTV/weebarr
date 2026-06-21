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
from urllib.parse import quote

import httpx
from fastapi import HTTPException

from src.weebarr.settings import SONARR_MONITOR_TYPES, Settings

ANILIST_URL = "https://graphql.anilist.co"
JIKAN_CHARACTERS_URL = "https://api.jikan.moe/v4/anime/{mal_id}/characters"
IDS_MOE_URL = "https://api.ids.moe/ids/{mal_id}?p=mal"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
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
SEERR_REQUESTED_STATES = {"requested", "partial", "available"}
SONARR_REQUESTED_STATES = {"in_library", "partial", "available"}
SONARR_AVAILABLE_MISSING_EPISODE_TOLERANCE = 2
TITLE_SUFFIX_PATTERNS = (
    (
        re.compile(r"\s+(season|cour|part)\s+\d+\s*$", flags=re.IGNORECASE),
        None,
    ),
    (
        re.compile(r"\s+\d+(st|nd|rd|th)\s+season\s*$", flags=re.IGNORECASE),
        None,
    ),
    (
        re.compile(
            r"(?P<base>.*?)(?P<number>\d+)(?P<label>st|nd|rd|th)\s+season\s*$",
            flags=re.IGNORECASE,
        ),
        "Season {number}",
    ),
    (
        re.compile(
            r"(?P<base>.*?)(?P<label>season|cour|part)\s*(?P<number>\d+)\s*$",
            flags=re.IGNORECASE,
        ),
        "{label} {number}",
    ),
    (
        re.compile(r"(?P<base>.*?)(?P<number>\d+)\s*$", flags=re.IGNORECASE),
        "Season {number}",
    ),
)

ANILIST_QUERY = """
query SeasonalAnime($season: MediaSeason!, $year: Int!, $page: Int!, $perPage: Int!) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage total }
    media(type: ANIME, season: $season, seasonYear: $year, sort: POPULARITY_DESC) {
      id
      idMal
      siteUrl
      trailer { id site thumbnail }
      format
      status
      episodes
      duration
      popularity
      averageScore
      meanScore
      favourites
      countryOfOrigin
      isAdult
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

ANILIST_CHARACTERS_QUERY = """
query AnimeCharacters($id: Int!, $perPage: Int!) {
  Media(id: $id, type: ANIME) {
    siteUrl
    characters(page: 1, perPage: $perPage, sort: [ROLE, RELEVANCE, ID]) {
      pageInfo { total hasNextPage }
      edges {
        role
        node {
          id
          siteUrl
          name { full native }
          image { large medium }
        }
        voiceActors(sort: [RELEVANCE, ID]) {
          id
          siteUrl
          languageV2
          name { full native }
          image { large medium }
        }
      }
    }
  }
}
"""
CHARACTER_SPOTLIGHT_LIMIT = 18


def normalize_title(value: str | None) -> str:
    """Normalize titles for loose matching."""

    if not value:
        return ""
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact_title(value: str | None) -> str:
    """Collapse a title down to bare alphanumerics for spacing-insensitive matches."""

    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


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


def _season_window_label(season: str | None, year: int | None) -> str | None:
    if not season or not year:
        return None
    return f"{season.title()} {year}"


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _shape_trailer(trailer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(trailer, dict):
        return None

    trailer_id = trailer.get("id")
    if not isinstance(trailer_id, str) or not trailer_id.strip():
        return None

    site = trailer.get("site")
    if not isinstance(site, str) or not site.strip():
        return None

    normalized_id = quote(trailer_id.strip(), safe="")
    normalized_site = site.strip().lower()
    thumbnail = trailer.get("thumbnail")
    thumbnail_url = (
        thumbnail.strip() if isinstance(thumbnail, str) and thumbnail.strip() else None
    )

    embed_url: str | None = None
    watch_url: str | None = None
    site_label = normalized_site.title()

    if normalized_site == "youtube":
        embed_url = f"https://www.youtube-nocookie.com/embed/{normalized_id}?rel=0"
        watch_url = f"https://www.youtube.com/watch?v={normalized_id}"
        site_label = "YouTube"
    elif normalized_site == "dailymotion":
        embed_url = f"https://www.dailymotion.com/embed/video/{normalized_id}"
        watch_url = f"https://www.dailymotion.com/video/{normalized_id}"
        site_label = "Dailymotion"

    return {
        "id": trailer_id.strip(),
        "site": normalized_site,
        "siteLabel": site_label,
        "thumbnail": thumbnail_url,
        "embedUrl": embed_url,
        "watchUrl": watch_url,
    }


def _normalize_character_role(role: Any) -> str:
    normalized = str(role or "").strip().upper()
    if normalized == "MAIN":
        return "Main"
    if normalized == "SUPPORTING":
        return "Supporting"
    if normalized == "BACKGROUND":
        return "Background"
    return "Cast"


def _shape_voice_actor(actor: dict[str, Any]) -> dict[str, Any] | None:
    name = cast(dict[str, Any], actor.get("name") or {})
    full_name = str(name.get("full") or "").strip()
    native_name = str(name.get("native") or "").strip() or None
    if not full_name:
        return None
    image = cast(dict[str, Any], actor.get("image") or {})
    return {
        "id": actor.get("id"),
        "name": full_name,
        "nativeName": native_name,
        "language": str(actor.get("languageV2") or "").strip() or "Unknown",
        "siteUrl": str(actor.get("siteUrl") or "").strip() or None,
        "image": str(image.get("large") or image.get("medium") or "").strip() or None,
    }


def _shape_character_edge(edge: dict[str, Any]) -> dict[str, Any] | None:
    node = cast(dict[str, Any], edge.get("node") or {})
    name = cast(dict[str, Any], node.get("name") or {})
    full_name = str(name.get("full") or "").strip()
    native_name = str(name.get("native") or "").strip() or None
    if not full_name:
        return None
    image = cast(dict[str, Any], node.get("image") or {})
    voice_actors = [
        actor
        for actor in (
            _shape_voice_actor(cast(dict[str, Any], actor))
            for actor in (edge.get("voiceActors") or [])
        )
        if actor is not None
    ]
    return {
        "id": node.get("id"),
        "name": full_name,
        "nativeName": native_name,
        "role": _normalize_character_role(edge.get("role")),
        "siteUrl": str(node.get("siteUrl") or "").strip() or None,
        "image": str(image.get("large") or image.get("medium") or "").strip() or None,
        "voiceActors": voice_actors,
    }


def tmdb_image_url(path: str | None, size: str) -> str | None:
    """Return a public TMDb image URL when a poster or backdrop path is present."""

    if not path:
        return None
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{TMDB_IMAGE_BASE_URL}/{size}{normalized}"


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
        compact_candidate = compact_title(candidate_title)
        compact_match = compact_title(title)
        if not normalized_title:
            continue
        if normalized_title == normalized_candidate:
            best = max(best, 100)
        elif compact_match and compact_match == compact_candidate:
            best = max(best, 100)
        elif (
            normalized_title in normalized_candidate
            or normalized_candidate in normalized_title
        ):
            best = max(best, 85)
        elif (
            compact_match
            and compact_candidate
            and (
                compact_match in compact_candidate or compact_candidate in compact_match
            )
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


def extract_installment_info(titles: list[str]) -> dict[str, Any]:
    """Infer the franchise installment from AniList titles when present."""

    for title in titles:
        if not title:
            continue
        stripped = title.strip()
        for pattern, template in TITLE_SUFFIX_PATTERNS:
            match = pattern.match(stripped)
            if not match:
                continue
            number = _coerce_int(match.groupdict().get("number"))
            base = (match.groupdict().get("base") or "").strip(" :-")
            if not number or not base:
                continue
            raw_label = match.groupdict().get("label")
            if template:
                label = template.format(
                    label=(raw_label or "Season").title(),
                    number=number,
                )
            else:
                label = None
            return {
                "seasonNumber": number,
                "label": label or f"Season {number}",
                "baseTitle": base,
            }
    return {"seasonNumber": None, "label": None, "baseTitle": None}


def strip_installment_suffix(title: str) -> str:
    """Remove season/cour/part suffixes so franchise titles search cleanly."""

    stripped = title.strip()
    for pattern, _template in TITLE_SUFFIX_PATTERNS:
        match = pattern.match(stripped)
        if not match:
            continue
        base = (match.groupdict().get("base") or "").strip(" :-")
        if base:
            return base
    return stripped


def title_search_variants(title: str) -> list[str]:
    """Generate safe Seerr search fallbacks for titles with season suffixes."""

    variants = [title]
    cleaned = strip_installment_suffix(title)
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

    @property
    def request_backend(self) -> str:
        return self.settings.active_request_backend

    def requested_states(self) -> set[str]:
        if self.request_backend == "sonarr":
            return SONARR_REQUESTED_STATES
        return SEERR_REQUESTED_STATES

    async def resolve_request_state(self, anime: dict[str, Any]) -> dict[str, Any]:
        if self.request_backend == "sonarr":
            return await self._resolve_sonarr(anime)
        return await self._resolve_seerr(anime)

    async def request_title(
        self,
        *,
        media_id: int,
        title: str,
        tvdb_id: int | None,
        seasons: list[int] | str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.request_backend == "sonarr":
            return await self.request_in_sonarr(
                media_id=media_id,
                title=title,
                tvdb_id=tvdb_id,
                seasons=seasons,
                options=options,
            )
        return await self.request_in_seerr(
            media_id=media_id,
            title=title,
            tvdb_id=tvdb_id,
            seasons=seasons,
        )

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
            f"seasonal:{season}:{year}:{per_page}:{self.request_backend}:"
            f"{self.settings.request_backend_configured}:"
            f"{self.settings.content_filter_mode}"
        )
        cached = self.cache.get(cache_key)
        if cached:
            return cast(dict[str, Any], cached)

        anime = await self._fetch_anilist(season, year, per_page)
        request_semaphore = asyncio.Semaphore(8)
        # Jikan is rate-limited, but serializing dub lookups makes cold loads feel stuck.
        # A moderate fan-out keeps the first render responsive while still falling back
        # quickly when Jikan returns 429s.
        audio_semaphore = asyncio.Semaphore(6)

        async def enrich(item: dict[str, Any]) -> dict[str, Any]:
            async def resolve_request() -> dict[str, Any]:
                async with request_semaphore:
                    return await self.resolve_request_state(item)

            async def resolve_audio() -> dict[str, Any]:
                async with audio_semaphore:
                    return await self._resolve_audio(item)

            request_state, item["audio"] = await asyncio.gather(
                resolve_request(),
                resolve_audio(),
            )
            item["request"] = request_state
            item["seerr"] = request_state
            return self._apply_request_art(item)

        enriched = await asyncio.gather(*(enrich(item) for item in anime))
        stats = Counter((item.get("request") or {}).get("state") for item in enriched)
        requestable_count = sum(
            1 for item in enriched if (item.get("request") or {}).get("requestable")
        )
        requested_states = self.requested_states()
        result = {
            "season": season,
            "year": year,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "stats": {
                "total": len(enriched),
                "requestable": requestable_count,
                "requested": sum(stats.get(state, 0) for state in requested_states),
                "available": stats.get("available", 0),
                "partial": stats.get("partial", 0),
                "seasonMissing": stats.get("season_missing", 0),
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
        filtered_media = [
            item
            for item in media
            if self._passes_content_filter(cast(dict[str, Any], item))
        ]
        return [
            self._shape_anime(item, rank)
            for rank, item in enumerate(filtered_media, start=1)
        ]

    def _passes_content_filter(self, item: dict[str, Any]) -> bool:
        return self.settings.content_filter_mode == "show_all" or not bool(
            item.get("isAdult")
        )

    def _shape_anime(self, item: dict[str, Any], rank: int) -> dict[str, Any]:
        titles = item.get("title") or {}
        title_candidates = [
            candidate
            for candidate in (
                titles.get("english"),
                titles.get("romaji"),
                titles.get("native"),
            )
            if isinstance(candidate, str) and candidate
        ]
        installment = extract_installment_info(title_candidates)
        start_year = (item.get("startDate") or {}).get("year")
        anilist_cover = (item.get("coverImage") or {}).get("extraLarge") or (
            item.get("coverImage") or {}
        ).get("large")
        anilist_banner = item.get("bannerImage")
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
            "trailer": _shape_trailer(item.get("trailer")),
            "format": item.get("format"),
            "status": item.get("status"),
            "episodes": item.get("episodes"),
            "duration": item.get("duration"),
            "popularity": item.get("popularity") or 0,
            "averageScore": item.get("averageScore") or item.get("meanScore"),
            "favourites": item.get("favourites") or 0,
            "countryOfOrigin": item.get("countryOfOrigin"),
            "isAdult": bool(item.get("isAdult")),
            "season": item.get("season"),
            "seasonYear": item.get("seasonYear"),
            "seasonLabel": _season_window_label(
                item.get("season"), item.get("seasonYear")
            ),
            "installment": installment,
            "installmentLabel": installment.get("label"),
            "startDate": _date_from_parts(item.get("startDate")),
            "startYear": start_year,
            "nextAiring": _next_airing(item.get("nextAiringEpisode")),
            "anilistCover": anilist_cover,
            "anilistBanner": anilist_banner,
            "cover": anilist_cover,
            "coverColor": (item.get("coverImage") or {}).get("color") or "#83e8ff",
            "banner": anilist_banner,
            "coverSource": "anilist",
            "bannerSource": "anilist",
            "genres": item.get("genres") or [],
            "description": strip_description(item.get("description")),
            "studios": [
                node.get("name")
                for node in ((item.get("studios") or {}).get("nodes") or [])
                if node.get("name")
            ],
            "characters": [],
            "charactersLoaded": False,
        }

    async def anime_characters(self, anime_id: int) -> dict[str, Any]:
        cache_key = f"anilist-characters:{anime_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds
            ) as client:
                response = await client.post(
                    ANILIST_URL,
                    json={
                        "query": ANILIST_CHARACTERS_QUERY,
                        "variables": {
                            "id": anime_id,
                            "perPage": CHARACTER_SPOTLIGHT_LIMIT,
                        },
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        if "errors" in body:
            raise HTTPException(
                status_code=502,
                detail=body["errors"][0].get("message", "AniList error"),
            )

        media = cast(dict[str, Any], (body.get("data") or {}).get("Media") or {})
        characters_block = cast(dict[str, Any], media.get("characters") or {})
        page_info = cast(dict[str, Any], characters_block.get("pageInfo") or {})
        edges = cast(list[dict[str, Any]], characters_block.get("edges") or [])
        characters = [
            character
            for character in (_shape_character_edge(edge) for edge in edges)
            if character is not None
        ]
        payload = {
            "characters": characters,
            "shown": len(characters),
            "total": _coerce_int(page_info.get("total")) or len(characters),
            "hasMore": bool(page_info.get("hasNextPage")),
            "siteUrl": str(media.get("siteUrl") or "").strip() or None,
        }
        self.cache.set(cache_key, payload, self.settings.anilist_cache_ttl_seconds)
        return payload

    def _apply_request_art(self, anime: dict[str, Any]) -> dict[str, Any]:
        """Prefer backend-provided TMDB art when a confident match exposes it."""

        request_state = anime.get("request") or anime.get("seerr") or {}
        poster_url = request_state.get("posterUrl")
        backdrop_url = request_state.get("backdropUrl")
        if poster_url:
            anime["cover"] = poster_url
            anime["coverSource"] = "tmdb"
        if backdrop_url:
            anime["banner"] = backdrop_url
            anime["bannerSource"] = "tmdb"
        return anime

    def _bucket_for_rank(self, rank: int) -> str:
        if rank <= 10:
            return "S-Tier"
        if rank <= 20:
            return "Canon"
        if rank <= 30:
            return "Bingeable"
        return "Filler"

    def _source_audio(self, country: str | None) -> dict[str, Any]:
        source = SOURCE_AUDIO.get(country or "")
        if source:
            return {
                "sourceCountry": country,
                "sourceLanguage": source["language"],
                "sourceLabel": source["label"],
                "fallbackState": source["state"],
                "fallbackLabel": "EN Sub",
            }
        return {
            "sourceCountry": country,
            "sourceLanguage": None,
            "sourceLabel": "Sub",
            "fallbackState": "sub_only",
            "fallbackLabel": "EN Sub",
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
            "state": source["fallbackState"],
            "label": source["fallbackLabel"],
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

    async def _seerr_tv_details(self, tmdb_id: int) -> dict[str, Any]:
        cache_key = f"seerr-tv:{tmdb_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.get(
                f"{self.settings.seerr_base_url}/api/v1/tv/{tmdb_id}",
                headers={"X-Api-Key": self.settings.seerr_api_key},
            )
            response.raise_for_status()
            payload = cast(dict[str, Any], response.json())

        self.cache.set(cache_key, payload, self.settings.seerr_cache_ttl_seconds)
        return payload

    async def _ids_moe_tmdb_id(self, mal_id: int) -> int | None:
        cache_key = f"idsmoe-mal:{mal_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(int | None, cached)

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.get(IDS_MOE_URL.format(mal_id=mal_id))
            if response.status_code == 404:
                self.cache.set(cache_key, None, self.settings.anilist_cache_ttl_seconds)
                return None
            response.raise_for_status()
            payload = cast(dict[str, Any], response.json())

        tmdb_id = _coerce_int(payload.get("themoviedb"))
        self.cache.set(cache_key, tmdb_id, self.settings.anilist_cache_ttl_seconds)
        return tmdb_id

    def _resolve_target_season(
        self,
        anime: dict[str, Any],
        details: dict[str, Any],
    ) -> tuple[int | None, str | None]:
        installment = cast(dict[str, Any], anime.get("installment") or {})
        target_season = _coerce_int(installment.get("seasonNumber"))
        target_label = cast(str | None, installment.get("label"))

        catalog_seasons = [
            _coerce_int(item.get("seasonNumber"))
            for item in details.get("seasons", [])
            if _coerce_int(item.get("seasonNumber")) not in (None, 0)
        ]
        catalog_seasons = [value for value in catalog_seasons if value is not None]

        if target_season and target_season in catalog_seasons:
            return target_season, target_label or f"Season {target_season}"
        if len(catalog_seasons) == 1:
            only_season = catalog_seasons[0]
            return only_season, target_label or f"Season {only_season}"
        if target_season:
            return target_season, target_label or f"Season {target_season}"
        return None, None

    @staticmethod
    def _anime_titles(anime: dict[str, Any]) -> list[str]:
        raw_titles = [
            anime.get("englishTitle"),
            anime.get("title"),
            anime.get("romajiTitle"),
            anime.get("nativeTitle"),
        ]
        return [
            title
            for title in dict.fromkeys(raw_titles)
            if isinstance(title, str) and title.strip()
        ]

    @staticmethod
    def _score_titles(titles: list[str]) -> list[str]:
        return list(
            dict.fromkeys(
                titles
                + [
                    variant
                    for title in titles
                    for variant in title_search_variants(title)
                ]
            )
        )

    @staticmethod
    def _catalog_seasons(details: dict[str, Any]) -> list[int]:
        return sorted(
            {
                season_number
                for season_number in (
                    _coerce_int(item.get("seasonNumber"))
                    for item in cast(list[dict[str, Any]], details.get("seasons") or [])
                )
                if season_number is not None and season_number > 0
            }
        )

    @staticmethod
    def _resolve_catalog_request_seasons(
        catalog_seasons: list[int],
        seasons: list[int] | str,
    ) -> list[int]:
        if isinstance(seasons, list):
            return sorted(
                {
                    season_number
                    for season_number in (_coerce_int(value) for value in seasons)
                    if season_number is not None and season_number > 0
                }
            )

        if not catalog_seasons:
            return []

        choice = seasons.strip().lower()
        if choice == "first":
            return [catalog_seasons[0]]
        if choice == "latest":
            return [catalog_seasons[-1]]
        return catalog_seasons

    def _classify_seerr_state(
        self,
        anime: dict[str, Any],
        best: dict[str, Any],
        details: dict[str, Any] | None,
        best_score: int,
    ) -> dict[str, Any]:
        details_media_info = (
            cast(dict[str, Any], details.get("mediaInfo"))
            if isinstance(details, dict) and isinstance(details.get("mediaInfo"), dict)
            else {}
        )
        media_info = details_media_info or cast(
            dict[str, Any], best.get("mediaInfo") or {}
        )
        raw_status_code = media_info.get("status")
        status_code = raw_status_code if isinstance(raw_status_code, int) else None

        state = "missing"
        label = "Missing"
        requestable = True
        target_season: int | None = None
        target_label: str | None = None
        season_statuses: dict[int, int] = {}
        requested_seasons: set[int] = set()
        catalog_seasons: set[int] = set()

        requests = cast(list[dict[str, Any]], media_info.get("requests") or [])
        open_requests = [
            req for req in requests if _coerce_int(req.get("status")) not in (5, 7)
        ]

        if details:
            target_season, target_label = self._resolve_target_season(anime, details)
            for item in cast(list[dict[str, Any]], details.get("seasons") or []):
                season_number = _coerce_int(item.get("seasonNumber"))
                if season_number is not None and season_number != 0:
                    catalog_seasons.add(season_number)
            for season in cast(list[dict[str, Any]], media_info.get("seasons") or []):
                season_number = _coerce_int(season.get("seasonNumber"))
                season_status = _coerce_int(season.get("status"))
                if season_number and season_status:
                    season_statuses[season_number] = season_status

            for request in open_requests:
                for season in cast(list[dict[str, Any]], request.get("seasons") or []):
                    season_number = _coerce_int(season.get("seasonNumber"))
                    if season_number:
                        requested_seasons.add(season_number)

        available_seasons = {
            season_number
            for season_number, season_status in season_statuses.items()
            if season_status == 5
        }
        tracked_seasons = {
            season_number
            for season_number, season_status in season_statuses.items()
            if season_status in (4, 5)
        }
        show_has_existing_episodes = bool(tracked_seasons) or status_code in (4, 5)

        if status_code == 6:
            state, label, requestable = "blocklisted", "Blocklisted", False
        elif target_season:
            required_seasons = list(range(1, target_season + 1))
            explicit_coverage = tracked_seasons | requested_seasons
            all_required_available = all(
                season_number in available_seasons for season_number in required_seasons
            )
            all_required_covered = all(
                season_number in explicit_coverage for season_number in required_seasons
            )
            any_required_available = any(
                season_number in tracked_seasons for season_number in required_seasons
            )
            any_previous_available = any(
                season_number in tracked_seasons
                for season_number in required_seasons
                if season_number != target_season
            )
            any_required_request = any(
                season_number in requested_seasons for season_number in required_seasons
            )
            target_has_explicit_coverage = target_season in explicit_coverage
            implicit_later_season = (
                target_season > 1
                and show_has_existing_episodes
                and not target_has_explicit_coverage
            )

            if all_required_available:
                state, label, requestable = "available", "Available", False
            elif implicit_later_season and self.settings.strict_monitoring:
                state, label, requestable = "season_missing", "Season Missing", True
            elif any_required_request and not any_previous_available:
                state, label, requestable = "requested", "Requested", False
            elif (
                target_season > 1
                and show_has_existing_episodes
                and any_required_available
            ):
                state, label, requestable = "partial", "Partially Available", False
            elif all_required_covered and any_required_available:
                state, label, requestable = "partial", "Partially Available", False
            else:
                state, label, requestable = "missing", "Missing", True
        elif open_requests or status_code in (2, 3):
            state, label, requestable = "requested", "Requested", False
        elif status_code == 5:
            state, label, requestable = "available", "Available", False
        elif status_code == 4:
            state, label, requestable = "partial", "Partially Available", False
        else:
            state, label, requestable = "missing", "Missing", True

        return {
            "backend": "seerr",
            "state": state,
            "label": label,
            "requestable": requestable,
            "tmdbId": best.get("id"),
            "tvdbId": (best.get("externalIds") or {}).get("tvdbId")
            or media_info.get("tvdbId"),
            "title": (
                details.get("name")
                if isinstance(details, dict) and details.get("name")
                else best.get("name") or best.get("title")
            ),
            "firstAirDate": best.get("firstAirDate") or best.get("first_air_date"),
            "posterPath": best.get("posterPath"),
            "backdropPath": best.get("backdropPath"),
            "posterUrl": tmdb_image_url(best.get("posterPath"), "w500"),
            "backdropUrl": tmdb_image_url(best.get("backdropPath"), "w780"),
            "matchScore": best_score,
            "mediaStatus": status_code,
            "targetSeason": target_season,
            "targetSeasonLabel": target_label,
            "catalogSeasons": sorted(catalog_seasons),
            "requestSeasons": (
                [target_season]
                if target_season is not None
                else self.settings.seerr_request_seasons
            ),
        }

    async def _resolve_seerr(self, anime: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.seerr_configured:
            return {
                "backend": "seerr",
                "state": "disabled",
                "label": "Seerr not configured",
                "requestable": False,
            }

        mal_id = _coerce_int(anime.get("malId"))
        if mal_id is not None:
            try:
                tmdb_id = await self._ids_moe_tmdb_id(mal_id)
            except httpx.HTTPError:
                tmdb_id = None
            if tmdb_id is not None:
                try:
                    details = await self._seerr_tv_details(tmdb_id)
                except httpx.HTTPError:
                    details = None
                if isinstance(details, dict) and details.get("id"):
                    return self._classify_seerr_state(anime, details, details, 120)

        raw_titles = [
            anime.get("englishTitle"),
            anime.get("title"),
            anime.get("romajiTitle"),
            anime.get("nativeTitle"),
        ]
        titles = [title for title in raw_titles if isinstance(title, str) and title]
        score_titles = list(
            dict.fromkeys(
                titles
                + [
                    variant
                    for title in titles
                    for variant in title_search_variants(title)
                ]
            )
        )
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
                score = candidate_score(score_titles, candidate, start_year)
                if score > best_score:
                    best = candidate
                    best_score = score
            if best_score >= 95:
                break

        if not best or best_score < 45:
            return {
                "backend": "seerr",
                "state": "missing_mapping",
                "label": "No Seerr match",
                "requestable": False,
                "matchScore": best_score,
            }
        details = None
        tmdb_id = _coerce_int(best.get("id"))
        if tmdb_id is not None:
            try:
                details = await self._seerr_tv_details(tmdb_id)
            except httpx.HTTPError:
                details = None
        return self._classify_seerr_state(anime, best, details, best_score)

    async def _seerr_search(self, query: str) -> list[dict[str, Any]]:
        cache_key = f"seerr-search:{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.get(
                f"{self.settings.seerr_base_url}/api/v1/search?query={quote(query, safe='')}",
                headers={"X-Api-Key": self.settings.seerr_api_key},
            )
            if response.status_code == 400:
                self.cache.set(cache_key, [], self.settings.seerr_cache_ttl_seconds)
                return []
            response.raise_for_status()
            results = cast(list[dict[str, Any]], response.json().get("results", []))

        self.cache.set(cache_key, results, self.settings.seerr_cache_ttl_seconds)
        return results

    async def _sonarr_request(
        self,
        method: str,
        path: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        resolved_base_url = (base_url or self.settings.sonarr_base_url).rstrip("/")
        resolved_api_key = api_key or self.settings.sonarr_api_key
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            return await client.request(
                method,
                f"{resolved_base_url}{path}",
                params=params,
                json=json,
                headers={"X-Api-Key": resolved_api_key},
            )

    async def _sonarr_request_json(
        self,
        method: str,
        path: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._sonarr_request(
            method,
            path,
            base_url=base_url,
            api_key=api_key,
            params=params,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    async def _sonarr_series(self) -> list[dict[str, Any]]:
        cache_key = "sonarr-series"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        payload = cast(
            list[dict[str, Any]],
            await self._sonarr_request_json("GET", "/api/v3/series"),
        )
        self.cache.set(cache_key, payload, self.settings.seerr_cache_ttl_seconds)
        return payload

    async def _sonarr_series_details(self, series_id: int) -> dict[str, Any]:
        cache_key = f"sonarr-series:{series_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        payload = cast(
            dict[str, Any],
            await self._sonarr_request_json("GET", f"/api/v3/series/{series_id}"),
        )
        self.cache.set(cache_key, payload, self.settings.seerr_cache_ttl_seconds)
        return payload

    async def _sonarr_lookup(self, term: str) -> list[dict[str, Any]]:
        cache_key = f"sonarr-lookup:{term}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        payload = cast(
            list[dict[str, Any]],
            await self._sonarr_request_json(
                "GET",
                "/api/v3/series/lookup",
                params={"term": term},
            ),
        )
        self.cache.set(cache_key, payload, self.settings.seerr_cache_ttl_seconds)
        return payload

    async def _sonarr_series_payload(self, series: dict[str, Any]) -> dict[str, Any]:
        series_id = _coerce_int(series.get("id"))
        if series_id is None:
            return series
        try:
            return await self._sonarr_series_details(series_id)
        except httpx.HTTPError:
            return series

    async def _sonarr_root_folders(
        self, base_url: str, api_key: str
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            await self._sonarr_request_json(
                "GET",
                "/api/v3/rootfolder",
                base_url=base_url,
                api_key=api_key,
            ),
        )

    async def _sonarr_quality_profiles(
        self, base_url: str, api_key: str
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            await self._sonarr_request_json(
                "GET",
                "/api/v3/qualityprofile",
                base_url=base_url,
                api_key=api_key,
            ),
        )

    async def _sonarr_language_profiles(
        self, base_url: str, api_key: str
    ) -> list[dict[str, Any]]:
        response = await self._sonarr_request(
            "GET",
            "/api/v3/languageprofile",
            base_url=base_url,
            api_key=api_key,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())

    async def _sonarr_tags(self, base_url: str, api_key: str) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            await self._sonarr_request_json(
                "GET",
                "/api/v3/tag",
                base_url=base_url,
                api_key=api_key,
            ),
        )

    def _best_scored_candidate(
        self,
        titles: list[str],
        candidates: list[dict[str, Any]],
        start_year: int | None,
    ) -> tuple[dict[str, Any] | None, int]:
        best: dict[str, Any] | None = None
        best_score = 0
        score_titles = self._score_titles(titles)
        for candidate in candidates:
            score = candidate_score(score_titles, candidate, start_year)
            if score > best_score:
                best = candidate
                best_score = score
        return best, best_score

    @staticmethod
    def _sonarr_season_has_files(season: dict[str, Any]) -> bool:
        statistics = cast(dict[str, Any], season.get("statistics") or {})
        count = _coerce_int(statistics.get("episodeFileCount")) or 0
        return count > 0

    @staticmethod
    def _sonarr_statistics_are_available(statistics: dict[str, Any]) -> bool:
        percent = statistics.get("percentOfEpisodes")
        if isinstance(percent, (int, float)) and percent >= 99.9:
            return True
        episode_count = _coerce_int(statistics.get("totalEpisodeCount")) or _coerce_int(
            statistics.get("episodeCount")
        )
        file_count = _coerce_int(statistics.get("episodeFileCount")) or 0
        if not episode_count or file_count <= 0:
            return False
        missing_episodes = max(episode_count - file_count, 0)
        return missing_episodes <= SONARR_AVAILABLE_MISSING_EPISODE_TOLERANCE

    @staticmethod
    def _sonarr_season_is_available(season: dict[str, Any]) -> bool:
        statistics = cast(dict[str, Any], season.get("statistics") or {})
        return WeebarrService._sonarr_statistics_are_available(statistics)

    def _classify_sonarr_state(
        self,
        anime: dict[str, Any],
        matched: dict[str, Any],
        best_score: int,
        *,
        in_library: bool,
        lookup_match: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        season_source = lookup_match or matched
        catalog_seasons = self._catalog_seasons(season_source)
        target_season, target_label = self._resolve_target_season(anime, season_source)
        season_selection_enabled = bool(catalog_seasons)
        default_request_seasons = (
            [target_season] if target_season is not None else list(catalog_seasons)
        )
        images = cast(list[dict[str, Any]], matched.get("images") or [])
        poster_url = next(
            (
                str(image.get("remoteUrl") or "").strip()
                for image in images
                if image.get("coverType") == "poster"
                and str(image.get("remoteUrl") or "").strip()
            ),
            None,
        )
        backdrop_url = next(
            (
                str(image.get("remoteUrl") or "").strip()
                for image in images
                if image.get("coverType") == "fanart"
                and str(image.get("remoteUrl") or "").strip()
            ),
            None,
        )

        state = "missing"
        label = "Missing"
        requestable = True
        if in_library:
            required_seasons = (
                list(range(1, target_season + 1))
                if target_season is not None
                else list(catalog_seasons)
            )
            available_seasons: set[int] = set()
            covered_seasons: set[int] = set()
            monitored_seasons: set[int] = set()
            for season in cast(list[dict[str, Any]], matched.get("seasons") or []):
                season_number = _coerce_int(season.get("seasonNumber"))
                if season_number is None or season_number == 0:
                    continue
                if season.get("monitored") is True:
                    monitored_seasons.add(season_number)
                if self._sonarr_season_has_files(season):
                    covered_seasons.add(season_number)
                if self._sonarr_season_is_available(season):
                    available_seasons.add(season_number)

            statistics = cast(dict[str, Any], matched.get("statistics") or {})
            overall_episode_files = _coerce_int(statistics.get("episodeFileCount")) or 0
            overall_available = self._sonarr_statistics_are_available(statistics)
            overall_has_files = overall_episode_files > 0
            required_season_set = set(required_seasons)
            fallback_uses_overall_stats = bool(
                required_season_set
                and overall_available
                and (not catalog_seasons or required_season_set == set(catalog_seasons))
            )
            fallback_has_overall_coverage = bool(
                required_season_set
                and overall_has_files
                and (not catalog_seasons or required_season_set == set(catalog_seasons))
            )

            if required_seasons and all(
                season_number in available_seasons for season_number in required_seasons
            ):
                state, label, requestable = "available", "Available", False
            elif fallback_uses_overall_stats:
                state, label, requestable = "available", "Available", False
            elif required_seasons and any(
                season_number in covered_seasons or season_number in available_seasons
                for season_number in required_seasons
            ):
                state, label, requestable = (
                    "partial",
                    "Partially Available",
                    True,
                )
            elif fallback_has_overall_coverage:
                state, label, requestable = (
                    "partial",
                    "Partially Available",
                    True,
                )
            elif not required_seasons and overall_available:
                state, label, requestable = "available", "Available", False
            elif not required_seasons and overall_has_files:
                state, label, requestable = (
                    "partial",
                    "Partially Available",
                    True,
                )
            else:
                state, label, requestable = "in_library", "In Library", True

        return {
            "backend": "sonarr",
            "state": state,
            "label": label,
            "requestable": requestable,
            "seriesId": _coerce_int(matched.get("id")) if in_library else None,
            "tmdbId": None,
            "tvdbId": _coerce_int(matched.get("tvdbId"))
            or _coerce_int((lookup_match or {}).get("tvdbId")),
            "title": matched.get("title")
            or matched.get("sortTitle")
            or anime.get("title"),
            "matchScore": best_score,
            "posterUrl": poster_url,
            "backdropUrl": backdrop_url,
            "targetSeason": target_season,
            "targetSeasonLabel": target_label,
            "catalogSeasons": catalog_seasons,
            "requestSeasons": default_request_seasons,
            "seasonSelectionEnabled": season_selection_enabled,
            "monitorModeDefault": self.settings.sonarr_default_monitor_mode,
            "searchOnAddDefault": self.settings.sonarr_default_search_on_add,
            "seasonFolderDefault": self.settings.sonarr_default_season_folder,
        }

    async def _resolve_sonarr(self, anime: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.sonarr_configured:
            return {
                "backend": "sonarr",
                "state": "disabled",
                "label": "Sonarr Direct not configured",
                "requestable": False,
            }

        titles = self._anime_titles(anime)
        raw_start_year = anime.get("startYear")
        start_year = raw_start_year if isinstance(raw_start_year, int) else None

        lookup_best: dict[str, Any] | None = None
        lookup_score = 0
        for title in titles:
            for query in title_search_variants(title):
                results = await self._sonarr_lookup(query)
                candidate, score = self._best_scored_candidate(
                    titles,
                    results,
                    start_year,
                )
                if score > lookup_score:
                    lookup_best = candidate
                    lookup_score = score
                if lookup_score >= 95:
                    break
            if lookup_score >= 95:
                break

        series_list = await self._sonarr_series()
        existing_best, existing_score = self._best_scored_candidate(
            titles,
            series_list,
            start_year,
        )

        if lookup_best is not None:
            lookup_tvdb_id = _coerce_int(lookup_best.get("tvdbId"))
            if lookup_tvdb_id is not None:
                existing_by_tvdb = next(
                    (
                        series
                        for series in series_list
                        if _coerce_int(series.get("tvdbId")) == lookup_tvdb_id
                    ),
                    None,
                )
                if existing_by_tvdb is not None:
                    matched_series = await self._sonarr_series_payload(existing_by_tvdb)
                    return self._classify_sonarr_state(
                        anime,
                        matched_series,
                        max(existing_score, lookup_score, 110),
                        in_library=True,
                        lookup_match=lookup_best,
                    )

        if existing_best is not None and existing_score >= 45:
            matched_series = await self._sonarr_series_payload(existing_best)
            return self._classify_sonarr_state(
                anime,
                matched_series,
                existing_score,
                in_library=True,
                lookup_match=lookup_best if lookup_score >= 45 else None,
            )
        if lookup_best is not None and lookup_score >= 45:
            return self._classify_sonarr_state(
                anime,
                lookup_best,
                lookup_score,
                in_library=False,
                lookup_match=lookup_best,
            )
        return {
            "backend": "sonarr",
            "state": "missing_mapping",
            "label": "No Sonarr match",
            "requestable": False,
            "matchScore": max(existing_score, lookup_score),
        }

    async def test_sonarr_connection(
        self,
        base_url: str,
        api_key: str,
    ) -> dict[str, Any]:
        try:
            root_folders, quality_profiles, language_profiles, tags = (
                await asyncio.gather(
                    self._sonarr_root_folders(base_url, api_key),
                    self._sonarr_quality_profiles(base_url, api_key),
                    self._sonarr_language_profiles(base_url, api_key),
                    self._sonarr_tags(base_url, api_key),
                )
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            raise HTTPException(
                status_code=exc.response.status_code, detail=detail
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        normalized_root_folders = [
            {
                "id": _coerce_int(item.get("id")),
                "path": str(item.get("path") or "").strip(),
            }
            for item in root_folders
            if str(item.get("path") or "").strip()
        ]
        normalized_quality_profiles = [
            {
                "id": _coerce_int(item.get("id")),
                "name": str(item.get("name") or "").strip(),
            }
            for item in quality_profiles
            if _coerce_int(item.get("id")) is not None
        ]
        normalized_language_profiles = [
            {
                "id": _coerce_int(item.get("id")),
                "name": str(item.get("name") or "").strip(),
            }
            for item in language_profiles
            if _coerce_int(item.get("id")) is not None
        ]
        normalized_tags = [
            {
                "id": _coerce_int(item.get("id")),
                "label": str(item.get("label") or "").strip(),
            }
            for item in tags
            if _coerce_int(item.get("id")) is not None
        ]

        return {
            "success": True,
            "rootFolderCount": len(normalized_root_folders),
            "qualityProfileCount": len(normalized_quality_profiles),
            "languageProfileCount": len(normalized_language_profiles),
            "tagCount": len(normalized_tags),
            "rootFolders": normalized_root_folders,
            "qualityProfiles": normalized_quality_profiles,
            "languageProfiles": normalized_language_profiles,
            "tags": normalized_tags,
            "defaults": {
                "rootFolderPath": (
                    normalized_root_folders[0]["path"]
                    if normalized_root_folders
                    else None
                ),
                "qualityProfileId": (
                    normalized_quality_profiles[0]["id"]
                    if normalized_quality_profiles
                    else None
                ),
                "seriesType": self.settings.sonarr_series_type or "anime",
                "defaultMonitorMode": self.settings.sonarr_default_monitor_mode,
                "defaultSearchOnAdd": self.settings.sonarr_default_search_on_add,
                "defaultSeasonFolder": self.settings.sonarr_default_season_folder,
            },
        }

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

    @staticmethod
    def _server_anime_series_type(server: dict[str, Any]) -> str | None:
        raw_value = server.get("animeSeriesType") or server.get("seriesType")
        if raw_value is None:
            return None
        value = str(raw_value).strip().lower()
        if value in {"standard", "daily", "anime"}:
            return value
        return None

    @staticmethod
    def _anime_request_defaults(server: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "serverId": server.get("id"),
            "profileId": server.get("activeAnimeProfileId")
            or server.get("activeProfileId"),
            "rootFolder": server.get("activeAnimeDirectory")
            or server.get("activeDirectory"),
            "languageProfileId": server.get("activeAnimeLanguageProfileId")
            or server.get("activeLanguageProfileId"),
            "tags": server.get("animeTags") or server.get("tags") or [],
        }
        series_type = WeebarrService._server_anime_series_type(server)
        if series_type is not None:
            defaults["seriesType"] = series_type
        return defaults

    @staticmethod
    def _find_server_by_id(
        servers: list[dict[str, Any]],
        server_id: int,
    ) -> dict[str, Any] | None:
        return next(
            (server for server in servers if server.get("id") == server_id), None
        )

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
            defaults = self._anime_request_defaults(server)
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
                "serverName": server.get("name"),
                **self._anime_request_defaults(server),
            }

        return {
            "success": True,
            "serverCount": len(servers),
            "defaults": defaults,
        }

    def _resolve_request_server(
        self,
        servers: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        forced_server_id = self.settings.seerr_sonarr_server_id
        forced_series_type = self.settings.seerr_series_type
        selected_server: dict[str, Any] | None = None

        if forced_server_id is not None:
            selected_server = self._find_server_by_id(servers, forced_server_id)
            if selected_server is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Configured Sonarr Server ID {forced_server_id} is not available in Seerr.",
                )

        if forced_series_type is None:
            return selected_server

        if selected_server is not None:
            actual_type = self._server_anime_series_type(selected_server)
            if actual_type is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Seerr does not expose an Anime Series Type for the selected Sonarr "
                        "server. Set the Anime Series Type in Seerr itself, then leave "
                        "Weebarr on Seerr default."
                    ),
                )
            if actual_type != forced_series_type:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Configured Sonarr Server ID {forced_server_id} uses anime series type "
                        f"'{actual_type}', not '{forced_series_type}'."
                    ),
                )
            return selected_server

        matching_servers = [
            server
            for server in servers
            if self._server_anime_series_type(server) == forced_series_type
        ]
        if not matching_servers:
            if any(
                self._server_anime_series_type(server) is None for server in servers
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Seerr does not expose Anime Series Type metadata for the configured "
                        "Sonarr server. Set Anime Series Type in Seerr itself and leave "
                        "Weebarr on Seerr default."
                    ),
                )
            raise HTTPException(
                status_code=400,
                detail=(
                    "No Sonarr server in Seerr matches the requested anime series type "
                    f"'{forced_series_type}'. Leave Force Series Type on Seerr default or "
                    "adjust the Sonarr integration settings in Seerr."
                ),
            )
        return self._select_default_server(matching_servers)

    async def _resolve_request_seasons(
        self,
        media_id: int,
        seasons: list[int] | str,
    ) -> list[int]:
        if isinstance(seasons, list):
            return self._resolve_catalog_request_seasons([], seasons)

        details = await self._seerr_tv_details(media_id)
        return self._resolve_catalog_request_seasons(
            self._catalog_seasons(details),
            seasons,
        )

    async def _find_existing_sonarr_series(
        self,
        media_id: int,
        tvdb_id: int | None,
    ) -> dict[str, Any] | None:
        series_list = await self._sonarr_series()
        existing = next(
            (
                series
                for series in series_list
                if _coerce_int(series.get("id")) == media_id
            ),
            None,
        )
        if existing is not None:
            return existing
        if tvdb_id is None:
            return None
        return next(
            (
                series
                for series in series_list
                if _coerce_int(series.get("tvdbId")) == tvdb_id
            ),
            None,
        )

    async def _lookup_sonarr_series(
        self,
        title: str,
        tvdb_id: int | None,
    ) -> tuple[dict[str, Any] | None, int]:
        lookup_best: dict[str, Any] | None = None
        lookup_score = 0
        titles = [title]
        for query in title_search_variants(title):
            results = await self._sonarr_lookup(query)
            if tvdb_id is not None:
                exact = next(
                    (
                        candidate
                        for candidate in results
                        if _coerce_int(candidate.get("tvdbId")) == tvdb_id
                    ),
                    None,
                )
                if exact is not None:
                    return exact, 120
            candidate, score = self._best_scored_candidate(titles, results, None)
            if score > lookup_score:
                lookup_best = candidate
                lookup_score = score
            if lookup_score >= 95:
                break
        return lookup_best, lookup_score

    async def request_in_sonarr(
        self,
        media_id: int,
        title: str,
        tvdb_id: int | None,
        seasons: list[int] | str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        options = options or {}
        monitor_mode = (
            str(
                options.get("monitorMode") or self.settings.sonarr_default_monitor_mode
            ).strip()
            or self.settings.sonarr_default_monitor_mode
        )
        if monitor_mode == "lastSeason":
            monitor_mode = "latestSeason"
        if monitor_mode not in SONARR_MONITOR_TYPES:
            raise HTTPException(status_code=400, detail="Invalid Sonarr monitor mode.")
        search_on_add = (
            bool(options.get("searchOnAdd"))
            if "searchOnAdd" in options
            else self.settings.sonarr_default_search_on_add
        )
        season_folder = (
            bool(options.get("seasonFolder"))
            if "seasonFolder" in options
            else self.settings.sonarr_default_season_folder
        )

        existing_series = await self._find_existing_sonarr_series(media_id, tvdb_id)
        lookup_series: dict[str, Any] | None = None
        lookup_score = 0
        if existing_series is None:
            lookup_series, lookup_score = await self._lookup_sonarr_series(
                title,
                tvdb_id,
            )
            if lookup_series is None or lookup_score < 45:
                raise HTTPException(status_code=404, detail="No Sonarr match found.")

        season_source = lookup_series or existing_series or {}
        catalog_seasons = self._catalog_seasons(season_source)
        default_selected_seasons = self._resolve_catalog_request_seasons(
            catalog_seasons,
            seasons,
        )
        selected_seasons = self._resolve_catalog_request_seasons(
            catalog_seasons,
            (
                cast(list[int], options.get("selectedSeasons"))
                if isinstance(options.get("selectedSeasons"), list)
                else default_selected_seasons
            ),
        )

        if existing_series is None:
            payload = dict(lookup_series or {})
            payload["rootFolderPath"] = self.settings.sonarr_root_folder_path
            payload["qualityProfileId"] = self.settings.sonarr_quality_profile_id
            payload["seriesType"] = self.settings.sonarr_series_type
            payload["seasonFolder"] = season_folder
            payload["monitored"] = True
            if self.settings.sonarr_language_profile_id is not None:
                payload["languageProfileId"] = self.settings.sonarr_language_profile_id
            if self.settings.sonarr_tags:
                payload["tags"] = self.settings.sonarr_tags
            if catalog_seasons:
                payload["seasons"] = [
                    {
                        **dict(season),
                        "monitored": (
                            _coerce_int(season.get("seasonNumber")) in selected_seasons
                            if selected_seasons
                            else bool(season.get("monitored"))
                        ),
                    }
                    for season in cast(
                        list[dict[str, Any]], payload.get("seasons") or []
                    )
                ]
            payload["addOptions"] = {
                "monitor": monitor_mode,
                "searchForMissingEpisodes": search_on_add,
                "searchForCutoffUnmetEpisodes": False,
                "ignoreEpisodesWithFiles": False,
                "ignoreEpisodesWithoutFiles": False,
            }
            response = await self._sonarr_request(
                "POST",
                "/api/v3/series",
                json=payload,
            )
            if response.status_code not in (200, 201, 202):
                if response.status_code == 409:
                    raise HTTPException(status_code=409, detail="Already in Sonarr")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text,
                )
            response_payload = (
                cast(dict[str, Any], response.json()) if response.content else payload
            )
            series_id = _coerce_int(response_payload.get("id"))
            request_context = {
                "title": title,
                "installment": {
                    "seasonNumber": selected_seasons[-1] if selected_seasons else None,
                    "label": (
                        f"Season {selected_seasons[-1]}" if selected_seasons else None
                    ),
                },
            }
            request_state = self._classify_sonarr_state(
                request_context,
                response_payload,
                max(lookup_score, 110),
                in_library=True,
                lookup_match=lookup_series,
            )
            self.clear_cache()
            return {
                "success": True,
                "statusCode": response.status_code,
                "title": title,
                "sentSeasons": selected_seasons,
                "seriesId": series_id,
                "tvdbId": _coerce_int(response_payload.get("tvdbId")),
                "requestState": request_state,
                "response": response_payload,
            }

        series_id = _coerce_int(existing_series.get("id"))
        if series_id is None:
            raise HTTPException(status_code=400, detail="Sonarr series ID is missing.")
        current_series = await self._sonarr_series_details(series_id)

        if catalog_seasons:
            seasonpass_payload = {
                "series": [
                    {
                        "id": series_id,
                        "monitored": True,
                        "seasons": [
                            {
                                **dict(season),
                                "monitored": (
                                    _coerce_int(season.get("seasonNumber"))
                                    in selected_seasons
                                    if selected_seasons
                                    else bool(season.get("monitored"))
                                ),
                            }
                            for season in cast(
                                list[dict[str, Any]],
                                current_series.get("seasons") or [],
                            )
                        ],
                    }
                ],
                "monitoringOptions": {
                    "monitor": monitor_mode,
                    "ignoreEpisodesWithFiles": False,
                    "ignoreEpisodesWithoutFiles": False,
                },
            }
            response = await self._sonarr_request(
                "POST",
                "/api/v3/seasonpass",
                json=seasonpass_payload,
            )
            if response.status_code not in (200, 201, 202):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text,
                )

        if bool(current_series.get("seasonFolder")) != season_folder:
            update_payload = dict(current_series)
            update_payload["seasonFolder"] = season_folder
            response = await self._sonarr_request(
                "PUT",
                f"/api/v3/series/{series_id}",
                json=update_payload,
            )
            if response.status_code not in (200, 201, 202):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text,
                )

        if search_on_add:
            response = await self._sonarr_request(
                "POST",
                "/api/v3/command",
                json={"name": "SeriesSearch", "seriesId": series_id},
            )
            if response.status_code not in (200, 201, 202):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text,
                )

        self.clear_cache()
        updated_series = await self._sonarr_series_details(series_id)
        request_context = {
            "title": title,
            "installment": {
                "seasonNumber": selected_seasons[-1] if selected_seasons else None,
                "label": (
                    f"Season {selected_seasons[-1]}" if selected_seasons else None
                ),
            },
        }
        request_state = self._classify_sonarr_state(
            request_context,
            updated_series,
            110,
            in_library=True,
            lookup_match=updated_series,
        )
        self.clear_cache()
        return {
            "success": True,
            "statusCode": 200,
            "title": title,
            "sentSeasons": selected_seasons,
            "seriesId": series_id,
            "tvdbId": _coerce_int(updated_series.get("tvdbId")),
            "requestState": request_state,
            "response": updated_series,
        }

    async def request_in_seerr(
        self,
        media_id: int,
        title: str,
        tvdb_id: int | None,
        seasons: list[int] | str,
    ) -> dict[str, Any]:
        request_seasons = await self._resolve_request_seasons(media_id, seasons)
        payload: dict[str, Any] = {
            "mediaType": "tv",
            "mediaId": media_id,
            "is4k": False,
            "seasons": request_seasons,
        }
        selected_server: dict[str, Any] | None = None
        if tvdb_id:
            payload["tvdbId"] = tvdb_id
        if (
            self.settings.seerr_sonarr_server_id is not None
            or self.settings.seerr_series_type is not None
        ):
            servers = await self._sonarr_servers(
                self.settings.seerr_base_url,
                self.settings.seerr_api_key,
            )
            selected_server = self._resolve_request_server(servers)
            server_id = (
                selected_server.get("id") if selected_server is not None else None
            )
            if isinstance(server_id, int) and server_id > 0:
                payload["serverId"] = server_id

        anime_defaults = (
            self._anime_request_defaults(selected_server)
            if selected_server is not None
            else await self._sonarr_defaults()
        )

        if self.settings.seerr_force_quality_profile:
            if self.settings.seerr_profile_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Force Quality Profile is enabled, but no Quality Profile ID is configured."
                    ),
                )
            payload["profileId"] = self.settings.seerr_profile_id
        elif anime_defaults.get("profileId") is not None:
            payload["profileId"] = anime_defaults.get("profileId")
        if self.settings.seerr_root_folder is not None:
            payload["rootFolder"] = self.settings.seerr_root_folder
        elif anime_defaults.get("rootFolder"):
            payload["rootFolder"] = anime_defaults.get("rootFolder")
        if self.settings.seerr_language_profile_id is not None:
            payload["languageProfileId"] = self.settings.seerr_language_profile_id
        elif anime_defaults.get("languageProfileId") is not None:
            payload["languageProfileId"] = anime_defaults.get("languageProfileId")
        if self.settings.seerr_request_user_id is not None:
            payload["userId"] = self.settings.seerr_request_user_id
        if self.settings.seerr_tags:
            payload["tags"] = self.settings.seerr_tags
        elif anime_defaults.get("tags"):
            payload["tags"] = anime_defaults.get("tags")

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
                "sentSeasons": request_seasons,
                "response": response.json() if response.content else {},
            }
        if response.status_code == 409:
            raise HTTPException(status_code=409, detail="Already requested in Seerr")
        raise HTTPException(status_code=response.status_code, detail=response.text)
