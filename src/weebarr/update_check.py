"""Published-container version checks for Weebarr."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, dataclass
from time import time
from typing import Any

import httpx

LOGGER = logging.getLogger("weebarr.update_check")

DEFAULT_UPDATE_DOCS_URL = "https://deepdaddyttv.github.io/weebarr/Update-Container/"
DOCKERHUB_TAGS_URL = (
    "https://hub.docker.com/v2/namespaces/deepdaddyttv/"
    "repositories/weebarr/tags?page_size=100"
)
SEMVER_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


@dataclass(slots=True)
class VersionUpdateStatus:
    """Summarized published-version state for sidebar notices."""

    current_version: str
    latest_version: str | None
    outdated: bool
    checked_at: int | None
    upgrade_url: str
    source: str = "dockerhub"

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


def parse_semver(value: str | None) -> tuple[int, int, int] | None:
    """Return a comparable semver tuple when the tag is x.y.z."""

    if not value:
        return None
    match = SEMVER_PATTERN.fullmatch(str(value).strip())
    if not match:
        return None
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


class DockerHubVersionChecker:
    """Cached Docker Hub tag probe for the published Weebarr image."""

    def __init__(
        self,
        *,
        current_version: str,
        tags_url: str = DOCKERHUB_TAGS_URL,
        upgrade_url: str = DEFAULT_UPDATE_DOCS_URL,
        cache_ttl_seconds: int = 21600,
        request_timeout_seconds: float = 5.0,
    ) -> None:
        self.current_version = current_version
        self.tags_url = tags_url
        self.upgrade_url = upgrade_url
        self.cache_ttl_seconds = max(300, cache_ttl_seconds)
        self.request_timeout_seconds = max(1.0, request_timeout_seconds)
        self._lock = asyncio.Lock()
        self._cached_status: VersionUpdateStatus | None = None
        self._expires_at = 0.0

    async def status(self) -> VersionUpdateStatus:
        """Return cached published-version state, refreshing when needed."""

        now = time()
        if self._cached_status and now < self._expires_at:
            return self._cached_status

        async with self._lock:
            now = time()
            if self._cached_status and now < self._expires_at:
                return self._cached_status
            try:
                latest_version = await self._latest_semver_tag()
                current_semver = parse_semver(self.current_version)
                latest_semver = parse_semver(latest_version)
                status = VersionUpdateStatus(
                    current_version=self.current_version,
                    latest_version=latest_version,
                    outdated=bool(
                        current_semver and latest_semver and current_semver < latest_semver
                    ),
                    checked_at=int(now),
                    upgrade_url=self.upgrade_url,
                )
            except (httpx.HTTPError, ValueError) as exc:
                LOGGER.warning("Version update check failed: %s", exc)
                if self._cached_status is not None:
                    self._expires_at = now + min(900, self.cache_ttl_seconds)
                    return self._cached_status
                status = VersionUpdateStatus(
                    current_version=self.current_version,
                    latest_version=None,
                    outdated=False,
                    checked_at=int(now),
                    upgrade_url=self.upgrade_url,
                )

            self._cached_status = status
            self._expires_at = now + self.cache_ttl_seconds
            return status

    async def _latest_semver_tag(self) -> str | None:
        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            response = await client.get(self.tags_url)
            response.raise_for_status()
        payload = response.json()
        tags = payload.get("results")
        if not isinstance(tags, list):
            raise ValueError("Docker Hub tag response is missing results.")
        semver_tags = [
            (parsed, str(tag.get("name")))
            for tag in tags
            if isinstance(tag, dict)
            for parsed in [parse_semver(tag.get("name"))]
            if parsed is not None
        ]
        if not semver_tags:
            raise ValueError("Docker Hub tag response did not include semver tags.")
        semver_tags.sort(key=lambda item: item[0], reverse=True)
        return semver_tags[0][1]
