# Weebarr

<div align="center">

<img src="src/web/static/img/weebarr-wordmark.svg" alt="Weebarr wordmark" width="420"/>

**Seasonal anime discovery and Seerr request management**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![GHCR](https://img.shields.io/badge/image-ghcr.io%2Fdeepdaddyttv%2Fweebarr-blue)](https://github.com/DeepDaddyTTV/weebarr/pkgs/container/weebarr)

</div>

Weebarr helps self-hosted anime libraries stay ahead of each release season. It pulls seasonal anime from AniList, ranks and groups shows by popularity, resolves titles against Seerr/TMDB, and lets you request TV anime directly into Seerr.

![Weebarr dashboard screenshot](docs/weebarr-dashboard-live.png)

## Why Weebarr?

- **Seasonal discovery**: Browse current and upcoming anime seasons without manually hunting through multiple anime sites.
- **Popularity-first triage**: Group shows into Headliners, Strong Signal, and Deep Cuts using AniList popularity.
- **Seerr-native requests**: Request matched TV anime through Seerr so your existing Sonarr anime profile, root folder, and approval flow stay in control.
- **Status-aware cards**: See whether a title is requestable, already requested, available, partially available, or missing a Seerr/TMDB match.
- **Audio signal badges**: Shows a best-effort English dub/source-language badge using AniList origin data and cached MAL voice-actor data from Jikan.
- **Self-hosted friendly**: Runs as a small FastAPI container with static frontend assets and environment-based configuration.

## Quick Start

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: America/New_York
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: your-seerr-api-key
    ports:
      - "8898:8888"
    volumes:
      - ./config:/config
    restart: unless-stopped
```

Open `http://localhost:8898`.

## Configuration

Weebarr is configured with environment variables so it works cleanly in Docker Compose, Portainer, Unraid, and similar self-hosted setups.

| Variable | Default | Description |
| --- | --- | --- |
| `WEEBARR_HOST` | `0.0.0.0` | Host interface Weebarr binds to inside the container. |
| `WEEBARR_PORT` | `8888` | Container listen port. |
| `WEEBARR_LOG_LEVEL` | `INFO` | Uvicorn/application log level. |
| `WEEBARR_CONFIG_PATH` | auto | Override the persisted JSON settings path. Defaults to `/config/weebarr.json` when writable. |
| `WEEBARR_ADMIN_TOKEN` | none | Optional token required to save or test Seerr settings from the UI. |
| `SEERR_BASE_URL` | none | Internal Seerr URL, for example `http://seerr:5055`. |
| `SEERR_API_KEY` | none | Seerr API key. Required for request/status integration. |
| `SEERR_REQUEST_SEASONS` | `all` | Request mode for unmatched season-specific titles. Supports `all`, `first`, or `latest`, and Weebarr resolves that into real season numbers before calling Seerr. |
| `SEERR_SONARR_SERVER_ID` | Seerr default | Optional Sonarr server override. |
| `SEERR_PROFILE_ID` | Seerr anime/default profile | Optional Sonarr quality/profile override. |
| `SEERR_ROOT_FOLDER` | Seerr anime/default root | Optional root-folder override sent with request payloads. |
| `SEERR_LANGUAGE_PROFILE_ID` | none | Optional language profile override for older Sonarr setups. |
| `SEERR_REQUEST_USER_ID` | API key user | Optional Seerr user ID to request as. |
| `SEERR_TAGS` | none | Optional comma-separated Seerr/Sonarr tag IDs. |
| `SEERR_CACHE_TTL_SECONDS` | `900` | Seerr search/details/settings cache TTL. |
| `REQUEST_TIMEOUT_SECONDS` | `20` | HTTP timeout for AniList, Seerr, and Jikan calls. |
| `ANILIST_CACHE_TTL_SECONDS` | `21600` | AniList seasonal cache TTL. |
| `AUDIO_LOOKUP_ENABLED` | `true` | Enables cached Jikan lookups for English voice-actor/dub detection. |
| `AUDIO_CACHE_TTL_SECONDS` | `86400` | Audio lookup cache TTL. |
| `AUDIO_LOOKUP_TIMEOUT_SECONDS` | `6` | Per-title timeout for Jikan audio metadata lookups. |

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
SEERR_BASE_URL=http://localhost:5055 SEERR_API_KEY=change-me python -m src.main
```

Run tests:

```bash
pytest tests/unit
```

## Notes

- AniList powers seasonal metadata and popularity sorting.
- Seerr powers TV matching, request status, and request creation.
- Jikan/MAL voice-actor data powers the best-effort `EN Dub` badge. If no English voice actors are found, Weebarr falls back to origin labels like `JA only` or `CH only`.
- If Weebarr cannot confidently match a title through Seerr search, it will show the title as missing mapping instead of creating a risky request.

## License

GPL-3.0. See [LICENSE](LICENSE).
