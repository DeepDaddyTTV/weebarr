"""Runtime settings and persisted user overrides for Weebarr."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Any


def _default_config_path() -> str:
    config_dir = Path("/config")
    if config_dir.exists() and os.access(config_dir, os.W_OK):
        return str(config_dir / "weebarr.json")
    return str((Path.cwd() / "config" / "weebarr.json").resolve())


DEFAULT_CONFIG_PATH = _default_config_path()


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _optional_csv_int(value: str | None) -> list[int] | None:
    if value is None or value.strip() == "":
        return None
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def _optional_csv_str(value: str | None) -> list[str]:
    if value is None or value.strip() == "":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _normalize_tags(value: Any) -> list[int] | None:
    if value in (None, "", []):
        return None
    if isinstance(value, list):
        return [int(part) for part in value if part not in (None, "")]
    if isinstance(value, str):
        return _optional_csv_int(value)
    raise ValueError("tags must be a list or comma-separated string")


def _normalize_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    return default


def _normalize_content_filter_mode(value: Any) -> str:
    if value is None:
        return "hide_nsfw"
    normalized = str(value).strip().lower()
    if normalized in ("", "hide_nsfw", "show_all"):
        return normalized or "hide_nsfw"
    if normalized == "adult_only":
        return "hide_nsfw"
    raise ValueError("content_filter_mode must be one of hide_nsfw or show_all")


def _normalize_auth_mode(value: Any) -> str:
    normalized = str(value or "disabled").strip().lower()
    if normalized in {"disabled", "local", "plex", "both"}:
        return normalized
    raise ValueError("auth_mode must be one of disabled, local, plex, or both")


def _normalize_request_record(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    anilist_id = _normalize_optional_int(value.get("anilist_id"))
    season = _normalize_optional_str(value.get("season"))
    year = _normalize_optional_int(value.get("year"))
    requested_at = _normalize_optional_str(value.get("requested_at"))
    if anilist_id is None or not season or year is None or not requested_at:
        return None
    request_seasons = value.get("request_seasons")
    normalized_request_seasons = (
        sorted(
            {
                season_id
                for season_id in (
                    _normalize_optional_int(part) for part in request_seasons
                )
                if season_id is not None and season_id > 0
            }
        )
        if isinstance(request_seasons, list)
        else []
    )
    return {
        "anilist_id": anilist_id,
        "tmdb_id": _normalize_optional_int(value.get("tmdb_id")),
        "tvdb_id": _normalize_optional_int(value.get("tvdb_id")),
        "title": _normalize_optional_str(value.get("title")) or "",
        "season": season,
        "year": year,
        "requested_at": requested_at,
        "request_seasons": normalized_request_seasons,
    }


def _request_record_key(record: dict[str, Any]) -> str:
    return f"{record['anilist_id']}:{record['season']}:{record['year']}"


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
    content_filter_mode: str = "hide_nsfw"
    strict_monitoring: bool = False
    auth_mode: str = "disabled"
    auth_username: str = ""
    auth_password: str = ""
    auth_password_hash: str = ""
    app_api_key: str = ""
    app_api_key_hash: str = ""
    app_api_key_preview_value: str = ""
    session_secret: str = ""
    session_cookie_name: str = "weebarr_session"
    session_max_age_seconds: int = 2592000
    public_url: str | None = None
    plex_client_id: str = "weebarr-web"
    plex_product_name: str = "Weebarr"
    plex_product_version: str = "0.0.0"
    plex_platform: str = "Web"
    plex_allowed_users: list[str] | None = None
    config_path: str = DEFAULT_CONFIG_PATH

    @property
    def seerr_configured(self) -> bool:
        return bool(self.seerr_base_url and self.seerr_api_key)

    @property
    def auth_enabled(self) -> bool:
        return self.auth_configured

    @property
    def local_auth_configured(self) -> bool:
        return bool(
            self.auth_username and (self.auth_password_hash or self.auth_password)
        )

    @property
    def uses_local_auth(self) -> bool:
        return self.local_auth_configured

    @property
    def uses_plex_auth(self) -> bool:
        return bool(self.plex_allowed_users)

    @property
    def plex_login_enabled(self) -> bool:
        return self.uses_plex_auth

    @property
    def api_key_enabled(self) -> bool:
        return bool(self.app_api_key or self.app_api_key_hash)

    @property
    def auth_configured(self) -> bool:
        return self.local_auth_configured or self.uses_plex_auth

    @property
    def setup_required(self) -> bool:
        return not self.auth_configured

    @property
    def effective_auth_mode(self) -> str:
        if self.local_auth_configured and self.uses_plex_auth:
            return "both"
        if self.local_auth_configured:
            return "local"
        if self.uses_plex_auth:
            return "plex"
        return "disabled"

    @property
    def api_key_preview(self) -> str:
        if self.app_api_key_preview_value:
            return self.app_api_key_preview_value
        if self.app_api_key:
            tail = (
                self.app_api_key[-4:] if len(self.app_api_key) > 4 else self.app_api_key
            )
            return f"••••{tail}"
        return ""

    @property
    def seerr_api_key_preview(self) -> str:
        if not self.seerr_api_key:
            return ""
        tail = (
            self.seerr_api_key[-4:]
            if len(self.seerr_api_key) > 4
            else self.seerr_api_key
        )
        return f"••••{tail}"

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
            content_filter_mode=_normalize_content_filter_mode(
                os.getenv("WEEBARR_CONTENT_FILTER_MODE", "hide_nsfw")
            ),
            strict_monitoring=_normalize_bool(
                os.getenv("WEEBARR_STRICT_MONITORING"),
                default=False,
            ),
            auth_mode=_normalize_auth_mode(os.getenv("WEEBARR_AUTH_MODE", "disabled")),
            auth_username=os.getenv("WEEBARR_AUTH_USERNAME", ""),
            auth_password=os.getenv("WEEBARR_AUTH_PASSWORD", ""),
            auth_password_hash=os.getenv("WEEBARR_AUTH_PASSWORD_HASH", ""),
            app_api_key=os.getenv("WEEBARR_API_KEY", ""),
            app_api_key_hash=os.getenv("WEEBARR_API_KEY_HASH", ""),
            app_api_key_preview_value=os.getenv("WEEBARR_API_KEY_PREVIEW", ""),
            session_secret=os.getenv("WEEBARR_SESSION_SECRET", ""),
            session_cookie_name=os.getenv(
                "WEEBARR_SESSION_COOKIE_NAME", "weebarr_session"
            ),
            session_max_age_seconds=int(
                os.getenv("WEEBARR_SESSION_MAX_AGE_SECONDS", "2592000")
            ),
            public_url=_normalize_optional_str(os.getenv("WEEBARR_PUBLIC_URL")),
            plex_client_id=os.getenv("WEEBARR_PLEX_CLIENT_ID", "weebarr-web"),
            plex_product_name=os.getenv("WEEBARR_PLEX_PRODUCT_NAME", "Weebarr"),
            plex_product_version=os.getenv("WEEBARR_PLEX_PRODUCT_VERSION", "0.0.0"),
            plex_platform=os.getenv("WEEBARR_PLEX_PLATFORM", "Web"),
            plex_allowed_users=_optional_csv_str(
                os.getenv("WEEBARR_PLEX_ALLOWED_USERS")
            )
            or None,
            config_path=os.getenv("WEEBARR_CONFIG_PATH", DEFAULT_CONFIG_PATH),
        )


class SettingsStore:
    """Persist and expose live user-editable Weebarr settings."""

    def __init__(self, base_settings: Settings):
        self._base = base_settings
        self._config_path = Path(base_settings.config_path)
        self._lock = RLock()
        self._current = self._base
        self.reload()

    def get(self) -> Settings:
        with self._lock:
            return self._current

    def reload(self) -> Settings:
        with self._lock:
            self._current = self._build_settings(self._load_payload())
            return self._current

    def save_seerr(self, overrides: dict[str, Any]) -> Settings:
        with self._lock:
            payload = self._load_payload()
            seerr = payload.setdefault("seerr", {})
            for key, value in overrides.items():
                if value is None:
                    seerr.pop(key, None)
                else:
                    seerr[key] = value
            self._write_payload(payload)
            self._current = self._build_settings(payload)
            return self._current

    def save_weebarr(self, overrides: dict[str, Any]) -> Settings:
        with self._lock:
            payload = self._load_payload()
            weebarr = payload.setdefault("weebarr", {})
            for key, value in overrides.items():
                if value is None:
                    weebarr.pop(key, None)
                else:
                    weebarr[key] = value
            self._write_payload(payload)
            self._current = self._build_settings(payload)
            return self._current

    def save_auth(self, overrides: dict[str, Any]) -> Settings:
        with self._lock:
            payload = self._load_payload()
            auth = payload.setdefault("auth", {})
            for key, value in overrides.items():
                if value is None:
                    auth.pop(key, None)
                else:
                    auth[key] = value
            self._write_payload(payload)
            self._current = self._build_settings(payload)
            return self._current

    def request_history(
        self,
        *,
        season: str | None = None,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            payload = self._load_payload()
            raw_records = payload.get("requests", [])
            if not isinstance(raw_records, list):
                return []
            records = [
                record
                for record in (_normalize_request_record(item) for item in raw_records)
                if record is not None
            ]
            if season is not None:
                records = [record for record in records if record["season"] == season]
            if year is not None:
                records = [record for record in records if record["year"] == year]
            return sorted(records, key=lambda item: item["requested_at"], reverse=True)

    def record_request(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_request_record(record)
        if normalized is None:
            raise ValueError("invalid request record")

        with self._lock:
            payload = self._load_payload()
            raw_records = payload.get("requests", [])
            if not isinstance(raw_records, list):
                raw_records = []

            key = _request_record_key(normalized)
            updated_records: list[dict[str, Any]] = []
            replaced = False
            for item in raw_records:
                existing = _normalize_request_record(item)
                if existing is None:
                    continue
                if _request_record_key(existing) == key:
                    normalized["requested_at"] = existing["requested_at"]
                    updated_records.append(normalized)
                    replaced = True
                else:
                    updated_records.append(existing)

            if not replaced:
                updated_records.append(normalized)

            payload["requests"] = updated_records
            self._write_payload(payload)
            return normalized

    def connection_summary(self) -> dict[str, Any]:
        current = self.get()
        return {
            "configured": current.seerr_configured,
            "baseUrl": current.seerr_base_url,
            "hasApiKey": bool(current.seerr_api_key),
            "apiKeyPreview": current.seerr_api_key_preview,
            "requestSeasons": current.seerr_request_seasons,
            "sonarrServerId": current.seerr_sonarr_server_id,
            "profileId": current.seerr_profile_id,
            "rootFolder": current.seerr_root_folder,
            "languageProfileId": current.seerr_language_profile_id,
            "requestUserId": current.seerr_request_user_id,
            "tags": current.seerr_tags or [],
        }

    def weebarr_summary(self) -> dict[str, Any]:
        current = self.get()
        return {
            "contentFilterMode": current.content_filter_mode,
            "strictMonitoring": current.strict_monitoring,
        }

    def access_summary(self) -> dict[str, Any]:
        current = self.get()
        return {
            "setupRequired": current.setup_required,
            "configured": current.auth_configured,
            "authMode": current.effective_auth_mode,
            "authUsername": current.auth_username,
            "localAuthConfigured": current.local_auth_configured,
            "plexLoginEnabled": current.uses_plex_auth,
            "publicUrl": current.public_url,
            "plexAllowedUsers": current.plex_allowed_users or [],
            "apiKeyEnabled": current.api_key_enabled,
            "apiKeyPreview": current.api_key_preview,
        }

    def _load_payload(self) -> dict[str, Any]:
        if not self._config_path.exists():
            return {}
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _write_payload(self, payload: dict[str, Any]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _build_settings(self, payload: dict[str, Any]) -> Settings:
        seerr = (
            payload.get("seerr", {}) if isinstance(payload.get("seerr"), dict) else {}
        )
        weebarr = (
            payload.get("weebarr", {})
            if isinstance(payload.get("weebarr"), dict)
            else {}
        )
        auth = payload.get("auth", {}) if isinstance(payload.get("auth"), dict) else {}
        return replace(
            self._base,
            seerr_base_url=(
                _normalize_optional_str(seerr.get("base_url"))
                or self._base.seerr_base_url
            ).rstrip("/"),
            seerr_api_key=_normalize_optional_str(seerr.get("api_key"))
            or self._base.seerr_api_key,
            seerr_request_seasons=_normalize_optional_str(seerr.get("request_seasons"))
            or self._base.seerr_request_seasons,
            seerr_sonarr_server_id=(
                _normalize_optional_int(seerr.get("sonarr_server_id"))
                if "sonarr_server_id" in seerr
                else self._base.seerr_sonarr_server_id
            ),
            seerr_profile_id=(
                _normalize_optional_int(seerr.get("profile_id"))
                if "profile_id" in seerr
                else self._base.seerr_profile_id
            ),
            seerr_root_folder=(
                _normalize_optional_str(seerr.get("root_folder"))
                if "root_folder" in seerr
                else self._base.seerr_root_folder
            ),
            seerr_language_profile_id=(
                _normalize_optional_int(seerr.get("language_profile_id"))
                if "language_profile_id" in seerr
                else self._base.seerr_language_profile_id
            ),
            seerr_request_user_id=(
                _normalize_optional_int(seerr.get("request_user_id"))
                if "request_user_id" in seerr
                else self._base.seerr_request_user_id
            ),
            seerr_tags=(
                _normalize_tags(seerr.get("tags"))
                if "tags" in seerr
                else self._base.seerr_tags
            ),
            content_filter_mode=(
                _normalize_content_filter_mode(weebarr.get("content_filter_mode"))
                if "content_filter_mode" in weebarr
                else (
                    _normalize_content_filter_mode(seerr.get("content_filter_mode"))
                    if "content_filter_mode" in seerr
                    else self._base.content_filter_mode
                )
            ),
            strict_monitoring=(
                _normalize_bool(weebarr.get("strict_monitoring"))
                if "strict_monitoring" in weebarr
                else self._base.strict_monitoring
            ),
            auth_mode=(
                _normalize_auth_mode(auth.get("mode"))
                if "mode" in auth
                else self._base.auth_mode
            ),
            auth_username=(
                _normalize_optional_str(auth.get("username"))
                if "username" in auth
                else self._base.auth_username
            )
            or "",
            auth_password_hash=(
                _normalize_optional_str(auth.get("password_hash"))
                if "password_hash" in auth
                else self._base.auth_password_hash
            )
            or "",
            app_api_key_hash=(
                _normalize_optional_str(auth.get("api_key_hash"))
                if "api_key_hash" in auth
                else self._base.app_api_key_hash
            )
            or "",
            app_api_key_preview_value=(
                _normalize_optional_str(auth.get("api_key_preview"))
                if "api_key_preview" in auth
                else self._base.app_api_key_preview_value
            )
            or "",
            session_secret=(
                _normalize_optional_str(auth.get("session_secret"))
                if "session_secret" in auth
                else self._base.session_secret
            )
            or "",
            public_url=(
                _normalize_optional_str(auth.get("public_url"))
                if "public_url" in auth
                else self._base.public_url
            ),
            plex_allowed_users=(
                _optional_csv_str(auth.get("plex_allowed_users"))
                if isinstance(auth.get("plex_allowed_users"), str)
                else (
                    [
                        str(value).strip()
                        for value in auth.get("plex_allowed_users", [])
                        if str(value).strip()
                    ]
                    if "plex_allowed_users" in auth
                    else self._base.plex_allowed_users
                )
            )
            or None,
        )
