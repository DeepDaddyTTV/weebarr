"""Version helpers for source, Docker, and native desktop Weebarr builds."""

from __future__ import annotations

import os
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

GIT_DESCRIBE_TIMEOUT_SECONDS = 2
RELEASE_VERSION = "0.2.0"
VERSION_OVERRIDE_ENV = "WEEBARR_VERSION_OVERRIDE"
ROOT = Path(__file__).resolve().parent.parent


def _strip_tag_prefix(value: str) -> str:
    return value[1:] if value.startswith("v") else value


def _run_git(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
            timeout=GIT_DESCRIBE_TIMEOUT_SECONDS,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _git_exact_tag() -> str | None:
    result = _run_git("describe", "--exact-match", "--tags")
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip()
    if not value:
        return None
    return _strip_tag_prefix(value)


def _git_dirty() -> bool | None:
    result = _run_git("status", "--porcelain")
    if result is None or result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _package_version() -> str | None:
    try:
        return package_version("weebarr")
    except PackageNotFoundError:
        return None


def get_version() -> str:
    """
    Resolve the current app version across source, packaged, and container runs.

    Resolution order:
    1. explicit environment override for native launcher/server parity
    2. exact git tag when running from a tagged checkout
    3. current release line with `-dev` or `-dev-dirty` when in a source repo
    4. installed package metadata
    5. static release fallback for container and bundled runs
    """

    override = os.getenv(VERSION_OVERRIDE_ENV, "").strip()
    if override:
        return override

    dirty = _git_dirty()
    if dirty is True:
        return f"{RELEASE_VERSION}-dev-dirty"

    exact_tag = _git_exact_tag()
    if exact_tag:
        return exact_tag
    if dirty is False:
        return f"{RELEASE_VERSION}-dev"

    packaged = _package_version()
    if packaged:
        return packaged

    return RELEASE_VERSION


# Cache the version at import time
__version__ = get_version()
