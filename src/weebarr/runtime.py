"""Runtime helpers for packaged and desktop Weebarr builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping

APP_NAME = "Weebarr"
DESKTOP_MODE_TRUTHY = {"1", "true", "yes", "on"}


def _env(env: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return env if env is not None else os.environ


def is_frozen(*, frozen: bool | None = None) -> bool:
    """Return whether Weebarr is running from a frozen desktop bundle."""

    if frozen is not None:
        return frozen
    return bool(getattr(sys, "frozen", False))


def desktop_mode_enabled(
    env: Mapping[str, str] | None = None,
    *,
    frozen: bool | None = None,
) -> bool:
    """Return whether desktop launcher defaults should be used."""

    if is_frozen(frozen=frozen):
        return True
    value = _env(env).get("WEEBARR_DESKTOP_MODE", "").strip().lower()
    return value in DESKTOP_MODE_TRUTHY


def source_root(*, frozen: bool | None = None) -> Path:
    """Resolve the root that contains the packaged `web/` assets."""

    if is_frozen(frozen=frozen):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        candidate = base / "src"
        if candidate.exists():
            return candidate
        return base
    return Path(__file__).resolve().parents[1]


def web_root(*, frozen: bool | None = None) -> Path:
    """Return the root that contains templates and static assets."""

    return source_root(frozen=frozen) / "web"


def _platform_app_base(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    runtime_env = _env(env)
    os_name = os_name or os.name
    platform_name = platform_name or sys.platform
    home = home or Path.home()

    if os_name == "nt":
        return Path(runtime_env.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
    if platform_name == "darwin":
        return home / "Library" / "Application Support"
    return Path(runtime_env.get("XDG_CONFIG_HOME", str(home / ".config")))


def desktop_app_dir(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    """Return the app-owned directory for native desktop installs."""

    return (
        _platform_app_base(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / APP_NAME
    )


def desktop_config_dir(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    return (
        desktop_app_dir(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / "config"
    )


def desktop_config_path(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    return (
        desktop_config_dir(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / "weebarr.json"
    )


def desktop_log_dir(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    return (
        desktop_app_dir(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / "logs"
    )


def desktop_state_dir(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    return (
        desktop_app_dir(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / "runtime"
    )


def desktop_state_path(
    env: Mapping[str, str] | None = None,
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
) -> Path:
    return (
        desktop_state_dir(
            env,
            os_name=os_name,
            platform_name=platform_name,
            home=home,
        )
        / "desktop-state.json"
    )
