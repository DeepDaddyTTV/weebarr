<div align="center">

<img src="src/web/static/img/weebarr-wordmark.png" alt="Weebarr wordmark" width="520"/>

**Seasonal anime discovery and Seerr request management**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![GHCR](https://img.shields.io/badge/image-ghcr.io%2Fdeepdaddyttv%2Fweebarr-blue)](https://github.com/DeepDaddyTTV/weebarr/pkgs/container/weebarr)

</div>

Weebarr is a small self-hosted companion app for anime libraries that use Seerr. It helps you browse the current anime season, see what is already available or requested, and send new TV anime requests through Seerr without bouncing between tabs.

It is built for people who want a simple seasonal anime dashboard that plays nicely with their existing Seerr and Sonarr setup.

## Current Features

- **Seasonal anime discovery** powered by AniList.
- **Simple popularity groups** for easier triage: `S-Tier`, `Canon`, `Bingeable`, and `Filler`.
- **Seerr-aware availability** so you can see what is available, requested, partially available, missing, or missing a confident Seerr/TMDb match.
- **One-click TV requests** through Seerr, using your existing anime defaults unless you choose to override them.
- **Optional automation** for requesting selected seasonal groups on a saved schedule.
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
- A working Seerr instance
- A Seerr API key
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

Start it:

```bash
docker compose up -d
```

Open Weebarr:

```text
http://localhost:18080
```

The first time you open the app, Weebarr walks you through setup. You can create a local admin login, use Plex login, or enable both.

## Documentation

The full documentation site is published from the repo `docs/` folder to GitHub Pages:

- [Documentation Home](https://deepdaddyttv.github.io/weebarr/)
- [Docker Desktop on Windows](https://deepdaddyttv.github.io/weebarr/Deployment-Docker-Desktop-Windows)
- [Docker Desktop on Linux](https://deepdaddyttv.github.io/weebarr/Deployment-Docker-Desktop-Linux)
- [Other Deployment Options](https://deepdaddyttv.github.io/weebarr/Deployment-Other-Options)
- [Features](https://deepdaddyttv.github.io/weebarr/Features)
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

Weebarr sends requests to Seerr. It does not bypass Seerr or request directly into Sonarr.

That means your normal Seerr request flow stays in charge, including your anime defaults, Sonarr server, quality profile, root folder, approval behavior, and user rules. Weebarr is the seasonal anime front door, not a replacement for Seerr.

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
