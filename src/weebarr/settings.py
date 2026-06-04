"""Runtime settings for Weebarr."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _optional_csv_int(value: str | None) -> list[int] | None:
    if value is None or value.strip() == "":
        return None
    return [int(part.strip()) for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    """Environment-backed settings."""

    host: str = "0.0.0.0"
    port: int = 8888
    log_level: str = "INFO"
    anilist_cache_ttl_seconds: int = 21600
    seerr_cache_ttl_seconds: int = 900
    seerr_base_url: str = ""
    seerr_api_key: str = ""
    seerr_sonarr_server_id: int | None = None
    seerr_profile_id: int | None = None
    seerr_root_folder: str | None = None
    seerr_language_profile_id: int | None = None
    seerr_tags: list[int] | None = None
    seerr_request_user_id: int | None = None
    seerr_request_seasons: str = "all"
    request_timeout_seconds: float = 20.0
    audio_lookup_enabled: bool = True
    audio_cache_ttl_seconds: int = 86400
    audio_lookup_timeout_seconds: float = 6.0

    @property
    def seerr_configured(self) -> bool:
        return bool(self.seerr_base_url and self.seerr_api_key)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("WEEBARR_HOST", "0.0.0.0"),
            port=int(os.getenv("WEEBARR_PORT", os.getenv("PORT", "8888"))),
            log_level=os.getenv("WEEBARR_LOG_LEVEL", "INFO"),
            anilist_cache_ttl_seconds=int(
                os.getenv("ANILIST_CACHE_TTL_SECONDS", "21600")
            ),
            seerr_cache_ttl_seconds=int(os.getenv("SEERR_CACHE_TTL_SECONDS", "900")),
            seerr_base_url=os.getenv("SEERR_BASE_URL", "").rstrip("/"),
            seerr_api_key=os.getenv("SEERR_API_KEY", ""),
            seerr_sonarr_server_id=_optional_int(os.getenv("SEERR_SONARR_SERVER_ID")),
            seerr_profile_id=_optional_int(os.getenv("SEERR_PROFILE_ID")),
            seerr_root_folder=os.getenv("SEERR_ROOT_FOLDER") or None,
            seerr_language_profile_id=_optional_int(
                os.getenv("SEERR_LANGUAGE_PROFILE_ID")
            ),
            seerr_tags=_optional_csv_int(os.getenv("SEERR_TAGS")),
            seerr_request_user_id=_optional_int(os.getenv("SEERR_REQUEST_USER_ID")),
            seerr_request_seasons=os.getenv("SEERR_REQUEST_SEASONS", "all"),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            audio_lookup_enabled=os.getenv("AUDIO_LOOKUP_ENABLED", "true").lower()
            not in ("0", "false", "no", "off"),
            audio_cache_ttl_seconds=int(os.getenv("AUDIO_CACHE_TTL_SECONDS", "86400")),
            audio_lookup_timeout_seconds=float(
                os.getenv("AUDIO_LOOKUP_TIMEOUT_SECONDS", "6")
            ),
        )
