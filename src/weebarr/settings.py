"""Runtime settings and persisted user overrides for Weebarr."""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit


def _default_config_path() -> str:
    config_dir = Path("/config")
    if config_dir.exists() and os.access(config_dir, os.W_OK):
        return str(config_dir / "weebarr.json")
    return str((Path.cwd() / "config" / "weebarr.json").resolve())


DEFAULT_CONFIG_PATH = _default_config_path()
AUTOMATION_BUCKET_KEYS = ("s_tier", "canon", "bingeable", "filler")
DEFAULT_AUTOMATION_BUCKETS = {
    "s_tier": False,
    "canon": False,
    "bingeable": False,
    "filler": False,
}
DEFAULT_AUTOMATION_SCAN_INTERVAL_DAYS = 30
THEME_TOKEN_KEYS = (
    "bg",
    "bg2",
    "pageTail",
    "pageGlowA",
    "pageGlowB",
    "pageGlowC",
    "panel",
    "panel2",
    "panel3",
    "mediaScrim",
    "line",
    "lineStrong",
    "text",
    "muted",
    "subtle",
    "cyan",
    "pink",
    "purple",
    "green",
    "warning",
)
THEME_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
DEFAULT_THEME_LIBRARY = {
    "neon-lights": {
        "id": "neon-lights",
        "name": "Neon Lights",
        "description": "The default Weebarr palette with cyan, magenta, and violet glow.",
        "builtIn": True,
        "editable": False,
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
    },
    "monochrome": {
        "id": "monochrome",
        "name": "Monochrome",
        "description": "Dark charcoal with bright white outlines in dark mode and the inverse in light mode.",
        "builtIn": True,
        "editable": False,
        "tokens": {
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
}


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


def _normalize_public_url(value: str | None) -> str | None:
    normalized = _normalize_optional_str(value)
    if normalized is None:
        return None

    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("public_url must be an absolute http or https URL")

    clean_path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, clean_path, "", ""))


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


def _normalize_scan_interval_days(value: Any) -> int:
    if value in (None, ""):
        return DEFAULT_AUTOMATION_SCAN_INTERVAL_DAYS
    return max(1, min(365, int(value)))


def _normalize_automation_buckets(value: Any) -> dict[str, bool]:
    normalized = dict(DEFAULT_AUTOMATION_BUCKETS)
    if not isinstance(value, dict):
        return normalized
    for key in AUTOMATION_BUCKET_KEYS:
        normalized[key] = _normalize_bool(value.get(key), default=False)
    return normalized


def _normalize_content_filter_mode(value: Any) -> str:
    if value is None:
        return "hide_nsfw"
    normalized = str(value).strip().lower()
    if normalized in ("", "hide_nsfw", "show_all"):
        return normalized or "hide_nsfw"
    if normalized == "adult_only":
        return "hide_nsfw"
    raise ValueError("content_filter_mode must be one of hide_nsfw or show_all")


def _normalize_series_type(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"", "default"}:
        return None
    if normalized in {"standard", "daily", "anime"}:
        return normalized
    raise ValueError("series_type must be one of default, standard, daily, or anime")


def _normalize_theme_color(value: Any) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        raise ValueError("theme colors must not be blank")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", candidate):
        raise ValueError("theme colors must use #RRGGBB or #RRGGBBAA values")
    return candidate.lower()


def _default_color_picker_tokens() -> dict[str, dict[str, str]]:
    return cast(
        dict[str, dict[str, str]],
        deepcopy(DEFAULT_THEME_LIBRARY["neon-lights"]["tokens"]),
    )


def _normalize_theme_tokens(value: Any) -> dict[str, dict[str, str]]:
    if not isinstance(value, dict):
        return _default_color_picker_tokens()
    normalized: dict[str, dict[str, str]] = {}
    defaults = _default_color_picker_tokens()
    for mode in ("dark", "light"):
        candidate = value.get(mode)
        source: dict[str, Any] = candidate if isinstance(candidate, dict) else {}
        normalized[mode] = {}
        for token_key in THEME_TOKEN_KEYS:
            raw = source.get(token_key, defaults[mode][token_key])
            normalized[mode][token_key] = _normalize_theme_color(raw)
    return normalized


def _normalize_theme_manifest(
    value: Any,
    *,
    built_in: bool = False,
    editable: bool = False,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    theme_id = str(value.get("id") or "").strip().lower()
    if not THEME_ID_PATTERN.fullmatch(theme_id):
        raise ValueError("theme id must be lowercase letters, numbers, or hyphens")
    name = str(value.get("name") or "").strip()
    if not name:
        raise ValueError("theme name is required")
    description = str(value.get("description") or "").strip()
    author = str(value.get("author") or "").strip() or None
    tokens = _normalize_theme_tokens(value.get("tokens"))
    return {
        "id": theme_id,
        "name": name,
        "description": description,
        "author": author,
        "builtIn": built_in,
        "editable": editable,
        "tokens": tokens,
    }


def _normalize_theme_imports(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for _, raw_theme in value.items():
        theme = _normalize_theme_manifest(raw_theme, built_in=False, editable=False)
        if theme is None:
            continue
        normalized[theme["id"]] = theme
    return normalized


def _normalize_active_theme_id(value: Any, imported: dict[str, dict[str, Any]]) -> str:
    candidate = str(value or "neon-lights").strip().lower() or "neon-lights"
    if candidate in DEFAULT_THEME_LIBRARY or candidate == "color-picker":
        return candidate
    if candidate in imported:
        return candidate
    return "neon-lights"


def _theme_catalog(
    *,
    imported: dict[str, dict[str, Any]] | None = None,
    color_picker_tokens: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    catalog = [deepcopy(DEFAULT_THEME_LIBRARY["neon-lights"])]
    catalog.append(
        {
            "id": "color-picker",
            "name": "Color Picker",
            "description": "A customizable version of Neon Lights.",
            "builtIn": True,
            "editable": True,
            "tokens": color_picker_tokens or _default_color_picker_tokens(),
        }
    )
    catalog.append(deepcopy(DEFAULT_THEME_LIBRARY["monochrome"]))
    for theme in sorted(
        (imported or {}).values(), key=lambda item: item["name"].lower()
    ):
        catalog.append(deepcopy(theme))
    return catalog


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
    seerr_force_quality_profile: bool = False
    seerr_series_type: str | None = None
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
    automation_enabled_buckets: dict[str, bool] | None = None
    automation_scan_interval_days: int = DEFAULT_AUTOMATION_SCAN_INTERVAL_DAYS
    automation_last_scan_at: str = ""
    automation_last_processed_season: str = ""
    automation_last_processed_year: int | None = None
    active_theme_id: str = "neon-lights"
    theme_imports: dict[str, dict[str, Any]] | None = None
    color_picker_tokens: dict[str, dict[str, str]] | None = None
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
    bootstrap_token: str = ""
    bootstrap_token_hash: str = ""
    plex_client_id: str = "weebarr-web"
    plex_product_name: str = "Weebarr"
    plex_product_version: str = "0.0.0"
    plex_platform: str = "Web"
    plex_allowed_users: list[str] | None = None
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    setup_rate_limit_attempts: int = 5
    setup_rate_limit_window_seconds: int = 600
    plex_rate_limit_attempts: int = 8
    plex_rate_limit_window_seconds: int = 300
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
    def bootstrap_token_enabled(self) -> bool:
        return bool(self.bootstrap_token or self.bootstrap_token_hash)

    @property
    def auth_configured(self) -> bool:
        return self.local_auth_configured or self.uses_plex_auth

    @property
    def setup_required(self) -> bool:
        return not self.auth_configured

    @property
    def automation_enabled(self) -> bool:
        return any(
            (self.automation_enabled_buckets or DEFAULT_AUTOMATION_BUCKETS).values()
        )

    @property
    def theme_catalog(self) -> list[dict[str, Any]]:
        return _theme_catalog(
            imported=self.theme_imports,
            color_picker_tokens=self.color_picker_tokens,
        )

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
            seerr_force_quality_profile=_normalize_bool(
                os.getenv("SEERR_FORCE_QUALITY_PROFILE"),
                default=False,
            ),
            seerr_series_type=_normalize_series_type(os.getenv("SEERR_SERIES_TYPE")),
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
            automation_enabled_buckets=_normalize_automation_buckets(None),
            automation_scan_interval_days=_normalize_scan_interval_days(
                os.getenv("WEEBARR_AUTOMATION_SCAN_INTERVAL_DAYS", "30")
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
            public_url=_normalize_public_url(os.getenv("WEEBARR_PUBLIC_URL")),
            bootstrap_token=os.getenv("WEEBARR_BOOTSTRAP_TOKEN", ""),
            bootstrap_token_hash=os.getenv("WEEBARR_BOOTSTRAP_TOKEN_HASH", ""),
            plex_client_id=os.getenv("WEEBARR_PLEX_CLIENT_ID", "weebarr-web"),
            plex_product_name=os.getenv("WEEBARR_PLEX_PRODUCT_NAME", "Weebarr"),
            plex_product_version=os.getenv("WEEBARR_PLEX_PRODUCT_VERSION", "0.0.0"),
            plex_platform=os.getenv("WEEBARR_PLEX_PLATFORM", "Web"),
            plex_allowed_users=_optional_csv_str(
                os.getenv("WEEBARR_PLEX_ALLOWED_USERS")
            )
            or None,
            login_rate_limit_attempts=int(
                os.getenv("WEEBARR_LOGIN_RATE_LIMIT_ATTEMPTS", "5")
            ),
            login_rate_limit_window_seconds=int(
                os.getenv("WEEBARR_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300")
            ),
            setup_rate_limit_attempts=int(
                os.getenv("WEEBARR_SETUP_RATE_LIMIT_ATTEMPTS", "5")
            ),
            setup_rate_limit_window_seconds=int(
                os.getenv("WEEBARR_SETUP_RATE_LIMIT_WINDOW_SECONDS", "600")
            ),
            plex_rate_limit_attempts=int(
                os.getenv("WEEBARR_PLEX_RATE_LIMIT_ATTEMPTS", "8")
            ),
            plex_rate_limit_window_seconds=int(
                os.getenv("WEEBARR_PLEX_RATE_LIMIT_WINDOW_SECONDS", "300")
            ),
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
            "forceQualityProfile": current.seerr_force_quality_profile,
            "seriesType": current.seerr_series_type or "default",
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
            "automation": {
                "enabledBuckets": current.automation_enabled_buckets
                or dict(DEFAULT_AUTOMATION_BUCKETS),
                "scanIntervalDays": current.automation_scan_interval_days,
                "lastScanAt": current.automation_last_scan_at or None,
                "lastProcessedSeason": current.automation_last_processed_season or None,
                "lastProcessedYear": current.automation_last_processed_year,
            },
            "theme": {
                "activeThemeId": current.active_theme_id,
                "themes": current.theme_catalog,
            },
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
            seerr_force_quality_profile=(
                _normalize_bool(seerr.get("force_quality_profile"))
                if "force_quality_profile" in seerr
                else self._base.seerr_force_quality_profile
            ),
            seerr_series_type=(
                _normalize_series_type(seerr.get("series_type"))
                if "series_type" in seerr
                else self._base.seerr_series_type
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
            automation_enabled_buckets=(
                _normalize_automation_buckets(weebarr.get("automation_enabled_buckets"))
                if "automation_enabled_buckets" in weebarr
                else (
                    deepcopy(self._base.automation_enabled_buckets)
                    if self._base.automation_enabled_buckets is not None
                    else dict(DEFAULT_AUTOMATION_BUCKETS)
                )
            ),
            automation_scan_interval_days=(
                _normalize_scan_interval_days(
                    weebarr.get("automation_scan_interval_days")
                )
                if "automation_scan_interval_days" in weebarr
                else self._base.automation_scan_interval_days
            ),
            automation_last_scan_at=(
                _normalize_optional_str(weebarr.get("automation_last_scan_at"))
                if "automation_last_scan_at" in weebarr
                else self._base.automation_last_scan_at
            )
            or "",
            automation_last_processed_season=(
                _normalize_optional_str(weebarr.get("automation_last_processed_season"))
                if "automation_last_processed_season" in weebarr
                else self._base.automation_last_processed_season
            )
            or "",
            automation_last_processed_year=(
                _normalize_optional_int(weebarr.get("automation_last_processed_year"))
                if "automation_last_processed_year" in weebarr
                else self._base.automation_last_processed_year
            ),
            theme_imports=(
                _normalize_theme_imports(weebarr.get("theme_imports"))
                if "theme_imports" in weebarr
                else (
                    deepcopy(self._base.theme_imports)
                    if self._base.theme_imports is not None
                    else {}
                )
            ),
            color_picker_tokens=(
                _normalize_theme_tokens(weebarr.get("color_picker_tokens"))
                if "color_picker_tokens" in weebarr
                else (
                    deepcopy(self._base.color_picker_tokens)
                    if self._base.color_picker_tokens is not None
                    else _default_color_picker_tokens()
                )
            ),
            active_theme_id=(
                _normalize_active_theme_id(
                    weebarr.get("active_theme_id"),
                    (
                        _normalize_theme_imports(weebarr.get("theme_imports"))
                        if "theme_imports" in weebarr
                        else (
                            deepcopy(self._base.theme_imports)
                            if self._base.theme_imports is not None
                            else {}
                        )
                    ),
                )
                if "active_theme_id" in weebarr or "theme_imports" in weebarr
                else self._base.active_theme_id
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
                _normalize_public_url(auth.get("public_url"))
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
