<div align="center">

<img src="src/web/static/img/weebarr-wordmark.png" alt="Weebarr wordmark" width="520"/>

**Seasonal anime discovery and request dashboard for Seerr or Sonarr Direct**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![GHCR](https://img.shields.io/badge/image-ghcr.io%2Fdeepdaddyttv%2Fweebarr-blue)](https://github.com/DeepDaddyTTV/weebarr/pkgs/container/weebarr)
[![Docker Hub](https://img.shields.io/badge/image-docker.io%2Fdeepdaddyttv%2Fweebarr-2496ED)](https://hub.docker.com/repository/docker/deepdaddyttv/weebarr/general)

</div>

Weebarr is a small self-hosted companion app for anime libraries that use Seerr, Sonarr, or both. It helps you browse the current anime season, see what is already available or tracked, and send new TV anime requests through either Seerr or the new Sonarr Direct flow without bouncing between tabs.

It is built for people who want a simple seasonal anime dashboard that plays nicely with their existing anime stack while keeping the request backend choice flexible.

## Current Features

- **Seasonal anime discovery** powered by AniList.
- **Simple popularity groups** for easier triage: `S-Tier`, `Canon`, `Bingeable`, and `Filler`.
- **Backend-aware availability** so you can see whether a title is missing, requested, in library, partially available, fully available, or missing a confident backend match.
- **At-a-glance seasonal metadata** including AniList score, popularity, and total episode count directly on cards and detail views.
- **Two request paths**:
  - one-click TV requests through Seerr using your existing anime defaults unless you override them
  - a Sonarr Direct request modal with season selection, monitor mode, search-on-add, and season-folder controls
- **Expandable cast details** so character voice actors stay readable without overwhelming the spotlight or mobile card layout.
- **Responsive mobile shell** with a centered first-load logo, animated full-screen navigation drawer, mobile Settings section picker, and installable PWA metadata.
- **Home-screen install support** for supported iOS and Android browsers using the included PWA manifest and app icons.
- **Optional automation** for requesting selected seasonal groups on a saved schedule.
- **Two-stage first-run setup** so access configuration and request-backend selection stay separate and intentional.
- **Single-admin access** with local login, Plex login, or both.
- **Theme support** with built-in themes and safe token-based theme imports.
- **Docker-friendly setup** with persistent configuration stored in `/config`.

## Preview

<p align="center">
  <img src="docs/assets/img/dark-mode.jpeg" alt="Weebarr dashboard in dark mode" width="100%"/>
  <img src="docs/assets/img/light-mode.jpeg" alt="Weebarr dashboard in light mode" width="100%"/>
</p>

<p align="center"><em>Dark mode</em> and <em>light mode</em> dashboard captures from the live app.</p>

## Getting Started

Weebarr is easiest to run with Docker Compose.

You will need:

- Docker or Docker Desktop
- A working Seerr instance if you want Seerr requests
- A working Sonarr instance if you want Sonarr Direct requests
- The API key for whichever backend you plan to use first
- A folder for Weebarr's `/config` data

Create a `compose.yml` file:

```yaml
services:
  weebarr:
    image: ghcr.io/deepdaddyttv/weebarr:latest
    container_name: weebarr
    environment:
      TZ: UTC
      WEEBARR_PUBLIC_URL: http://localhost:18080
      SEERR_BASE_URL: http://seerr:5055
      SEERR_API_KEY: your-seerr-api-key
    ports:
      - "18080:8888"
    volumes:
      - ./config:/config
    restart: unless-stopped
```

If you prefer Docker Hub, use this image instead:

```yaml
image: deepdaddyttv/weebarr:latest
```

Start it:

```bash
docker compose up -d
```

Open Weebarr:

```text
http://localhost:18080
```

The first time you open the app, Weebarr walks you through setup in two stages:

1. Create the local admin login, use Plex login, or enable both.
2. Choose the request backend after auth. If you pick Sonarr Direct, choose `http` or `https`, enter the Sonarr host and port (default `8989`), then validate the API key so Weebarr can load the live root-folder and quality-profile dropdowns before you save. You can still use `Skip Setup` and finish it later in Settings.

## Documentation

The full documentation site is published from the repo `docs/` folder to GitHub Pages:

- [Docker Hub](https://hub.docker.com/repository/docker/deepdaddyttv/weebarr/general)
- [GitHub Repository](https://github.com/DeepDaddyTTV/weebarr)
- [Documentation Home](https://deepdaddyttv.github.io/weebarr/)
- [Docker Desktop on Windows](https://deepdaddyttv.github.io/weebarr/Deployment-Docker-Desktop-Windows)
- [Docker Desktop on Linux](https://deepdaddyttv.github.io/weebarr/Deployment-Docker-Desktop-Linux)
- [Other Deployment Options](https://deepdaddyttv.github.io/weebarr/Deployment-Other-Options)
- [Backends](https://deepdaddyttv.github.io/weebarr/Backends)
- [Features](https://deepdaddyttv.github.io/weebarr/Features)
- [Install as an App](https://deepdaddyttv.github.io/weebarr/Install-App)
- [Settings](https://deepdaddyttv.github.io/weebarr/Settings)
- [Theme Template](https://deepdaddyttv.github.io/weebarr/Theme-Template)
- [Troubleshooting](https://deepdaddyttv.github.io/weebarr/Troubleshooting)
- [API Reference](https://deepdaddyttv.github.io/weebarr/API-Reference)

## Public Deployment Notes

If you expose Weebarr outside your home network, put it behind a reverse proxy, tunnel, or similar edge layer.

Recommended basics:

- Use HTTPS.
- Set `WEEBARR_PUBLIC_URL` to the real public URL.
- Keep `/config` mounted so settings survive updates.
- Do not expose the raw container port directly to the internet if you can avoid it.
- Use rate limiting and any extra auth protections provided by your proxy or tunnel.

Plex login also depends on `WEEBARR_PUBLIC_URL`, so set it before using Plex auth on a public hostname.

## How Requests Work

Weebarr now supports two request backends:

- `Seerr`: Weebarr keeps the current one-click request button and forwards TV anime requests through Seerr.
- `Sonarr Direct`: Weebarr opens a Sonarr-specific request modal and adds or updates anime directly in Sonarr.

If you stay on Seerr, your normal Seerr request flow stays in charge, including your anime defaults, Sonarr server, quality profile, root folder, approval behavior, and user rules.

If you switch to Sonarr Direct, Weebarr uses the saved Sonarr defaults you choose in setup or Settings, then tracks Sonarr-native states such as `In Library`, `Partially Available`, `Available`, and `No Sonarr match`.

## API

Weebarr includes a small API for health checks, seasonal reads, character data, and safe external request creation.

The quickest health check is:

```text
/api/health
```

See the [API Reference](https://deepdaddyttv.github.io/weebarr/API-Reference) for the full route list and auth notes.

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
WEEBARR_PORT=18080 SEERR_BASE_URL=http://localhost:5055 SEERR_API_KEY=change-me python -m src.main
```

Run tests:

```bash
pytest tests/unit
```

## Support

Before opening an issue, check the [Troubleshooting](https://deepdaddyttv.github.io/weebarr/Troubleshooting) page. It covers the common gremlins: Seerr connection problems, missing matches, automation not running, theme import failures, Plex login issues, and first-run setup behavior.

Bug reports and feature requests can be submitted through GitHub Issues.

## License

GPL-3.0. See [LICENSE](LICENSE).
